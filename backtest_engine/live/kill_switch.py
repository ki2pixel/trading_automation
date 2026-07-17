import asyncio
import json
import logging
import os
import re
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.exceptions import RedisError

from backtest_engine.live.utils import NETWORK_TIMEOUT_DEFAULT

logger = logging.getLogger("papertrader")

_trading_suspended: bool = False
_LEGACY_STATE_KEY = "trading:suspended"


class KillSwitchStateError(RuntimeError):
    """Raised when a distributed Kill Switch state transition cannot be persisted."""


@dataclass(frozen=True)
class KillSwitchStatus:
    suspended: bool
    source: str
    reason: Optional[str]
    event_id: Optional[str]
    updated_at: Optional[str]
    distributed: bool
    healthy: bool

    def as_dict(self) -> dict[str, bool | str | None]:
        return {
            "status": "suspended" if self.suspended else "active",
            "source": self.source,
            "reason": self.reason,
            "event_id": self.event_id,
            "updated_at": self.updated_at,
            "distributed": self.distributed,
            "healthy": self.healthy,
        }


import threading

_trading_suspended_lock = threading.Lock()

def is_trading_suspended() -> bool:
    """Return the local Kill Switch state."""
    with _trading_suspended_lock:
        return _trading_suspended


def set_trading_suspended(value: bool) -> None:
    """Set the local Kill Switch state."""
    global _trading_suspended
    with _trading_suspended_lock:
        _trading_suspended = value


def _normalize_namespace(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9:_-]+", "-", value.strip().lower())
    return normalized.strip("-:") or "paper"


def get_kill_switch_namespace() -> str:
    """Return the environment-isolated Redis namespace for the Kill Switch."""
    configured_namespace = os.getenv("KILL_SWITCH_NAMESPACE")
    if configured_namespace:
        return _normalize_namespace(configured_namespace)

    environment = (
        os.getenv("PAPER_TRADER_ENV")
        or os.getenv("ENVIRONMENT")
        or "paper"
    )
    return f"paper_trader:{_normalize_namespace(environment)}"


def get_kill_switch_state_key() -> str:
    """Return the canonical Kill Switch state key."""
    return f"{get_kill_switch_namespace()}:kill_switch:state"


def get_kill_switch_channel() -> str:
    """Return the environment-isolated Kill Switch Pub/Sub channel."""
    return f"{get_kill_switch_namespace()}:kill_switch:urgency"


def get_kill_switch_confirmation_key() -> str:
    """Return the transient Kill Switch confirmation key."""
    return f"{get_kill_switch_namespace()}:kill_switch:confirmed"


def _new_status(
    suspended: bool,
    source: str,
    reason: Optional[str] = None,
    event_id: Optional[str] = None,
    updated_at: Optional[str] = None,
    distributed: bool = False,
    healthy: bool = True,
) -> KillSwitchStatus:
    return KillSwitchStatus(
        suspended=suspended,
        source=source,
        reason=reason,
        event_id=event_id,
        updated_at=updated_at,
        distributed=distributed,
        healthy=healthy,
    )


def _create_transition_status(
    suspended: bool,
    source: str,
    reason: Optional[str],
) -> KillSwitchStatus:
    return _new_status(
        suspended=suspended,
        source=source,
        reason=reason,
        event_id=str(uuid.uuid4()),
        updated_at=datetime.now(timezone.utc).isoformat(),
        distributed=True,
    )


def _decode_state(raw_state: Any, source: str) -> KillSwitchStatus:
    if isinstance(raw_state, bytes):
        raw_value = raw_state.decode("utf-8")
    elif isinstance(raw_state, str):
        raw_value = raw_state
    else:
        return _new_status(
            suspended=True,
            source="invalid_state",
            reason="Unsupported Redis Kill Switch state type",
            distributed=True,
            healthy=False,
        )

    if raw_value == "true":
        return _new_status(
            suspended=True,
            source="legacy",
            reason="Legacy distributed Kill Switch state",
            distributed=True,
        )

    try:
        payload = json.loads(raw_value)
    except json.JSONDecodeError:
        return _new_status(
            suspended=True,
            source="invalid_state",
            reason="Malformed distributed Kill Switch state",
            distributed=True,
            healthy=False,
        )

    if not isinstance(payload, dict):
        return _new_status(
            suspended=True,
            source="invalid_state",
            reason="Malformed distributed Kill Switch payload",
            distributed=True,
            healthy=False,
        )

    state = payload.get("status")
    if state not in {"active", "suspended"}:
        return _new_status(
            suspended=True,
            source="invalid_state",
            reason="Unknown distributed Kill Switch status",
            distributed=True,
            healthy=False,
        )

    reason = payload.get("reason")
    event_id = payload.get("event_id")
    updated_at = payload.get("updated_at")
    return _new_status(
        suspended=state == "suspended",
        source=source,
        reason=reason if isinstance(reason, str) else None,
        event_id=event_id if isinstance(event_id, str) else None,
        updated_at=updated_at if isinstance(updated_at, str) else None,
        distributed=True,
    )


def _get_redis_client() -> Any:
    from backtest_engine.live.connection import get_redis_client

    return get_redis_client()


def get_kill_switch_status(redis_client: Any = None) -> KillSwitchStatus:
    """Read the canonical distributed state and synchronize the local state."""
    client = redis_client if redis_client is not None else _get_redis_client()
    if client is None:
        return _new_status(
            suspended=is_trading_suspended(),
            source="local",
            distributed=False,
        )

    try:
        raw_state = client.get(get_kill_switch_state_key())
        if raw_state is None:
            legacy_state = client.get(_LEGACY_STATE_KEY)
            if legacy_state is None:
                status = _new_status(False, "redis", distributed=True)
            else:
                status = _decode_state(legacy_state, "legacy")
        else:
            status = _decode_state(raw_state, "redis")
    except (RedisError, OSError) as exc:
        logger.warning("[KillSwitch] Unable to read distributed Kill Switch state: %s", exc)
        status = _new_status(
            suspended=True,
            source="redis_unavailable",
            reason="Distributed Kill Switch state is unavailable",
            distributed=True,
            healthy=False,
        )

    set_trading_suspended(status.suspended)
    return status


async def get_kill_switch_status_async() -> KillSwitchStatus:
    """Read the canonical Kill Switch state without blocking the event loop."""
    return await asyncio.to_thread(get_kill_switch_status)


def _serialize_status(status: KillSwitchStatus) -> str:
    return json.dumps(
        {
            "status": "suspended" if status.suspended else "active",
            "source": status.source,
            "reason": status.reason,
            "event_id": status.event_id,
            "updated_at": status.updated_at,
        },
        separators=(",", ":"),
    )


def _persist_transition(status: KillSwitchStatus, command: str) -> KillSwitchStatus:
    client = _get_redis_client()
    if client is None:
        if os.getenv("REDIS_URL"):
            raise KillSwitchStateError("Distributed Kill Switch Redis client is unavailable")
        return replace(status, distributed=False)

    try:
        client.set(get_kill_switch_state_key(), _serialize_status(status))
    except (RedisError, OSError) as exc:
        raise KillSwitchStateError("Unable to persist distributed Kill Switch state") from exc

    try:
        client.publish(get_kill_switch_channel(), command)
    except (RedisError, OSError) as exc:
        logger.warning("[KillSwitch] State persisted but notification publish failed: %s", exc)

    return status


async def suspend_trading(reason: str, source: str) -> KillSwitchStatus:
    """Suspend trading locally and persist the state before notifying workers."""
    set_trading_suspended(True)
    status = _create_transition_status(True, source, reason)
    return await asyncio.to_thread(_persist_transition, status, "SUSPEND")


async def resume_trading(source: str) -> KillSwitchStatus:
    """Persist an explicit active state before resuming local trading."""
    status = _create_transition_status(False, source, "Operator-confirmed resume")
    persisted_status = await asyncio.to_thread(_persist_transition, status, "RESUME")
    set_trading_suspended(False)
    return persisted_status


def _write_confirmation() -> None:
    client = _get_redis_client()
    if client is None:
        return

    try:
        client.set(
            get_kill_switch_confirmation_key(),
            "true",
            ex=60,
        )
    except (RedisError, OSError) as exc:
        logger.warning("[KillSwitch] Failed to persist Kill Switch confirmation: %s", exc)


class KillSwitchListener:
    """Listen to environment-isolated emergency commands and enforce Kill Switch transitions."""

    def __init__(self, engine: Any, redis_url: Optional[str] = None) -> None:
        self.engine = engine
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self.redis_client: Optional[aioredis.Redis] = None
        self._listener_task: Optional[asyncio.Task[None]] = None
        self._running = False
        self.channel = get_kill_switch_channel()

    async def start(self) -> None:
        """Start the Pub/Sub listener in the background."""
        if not self.redis_url:
            logger.warning("[KillSwitch] REDIS_URL is not set. Kill Switch is running in local-only mode.")
            return

        self._running = True
        self._listener_task = asyncio.create_task(self._listen_loop())
        logger.info("[KillSwitch] Asynchronous ESMA RTS 6 listener started for channel '%s'.", self.channel)

    async def stop(self) -> None:
        """Stop the background listener."""
        self._running = False
        if self._listener_task is None:
            return

        self._listener_task.cancel()
        try:
            await self._listener_task
        except asyncio.CancelledError:
            pass
        logger.info("[KillSwitch] Kill Switch listener stopped.")

    def _redis_connection_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "decode_responses": True,
            "socket_timeout": NETWORK_TIMEOUT_DEFAULT,
            "socket_connect_timeout": NETWORK_TIMEOUT_DEFAULT,
            "health_check_interval": 30,
            "socket_keepalive": True,
        }
        redis_user = os.getenv("REDIS_USER")
        redis_password = os.getenv("REDIS_PASSWORD")
        if redis_user:
            kwargs["username"] = redis_user
        if redis_password:
            kwargs["password"] = redis_password
        return kwargs

    async def _listen_loop(self) -> None:
        while self._running:
            self.redis_client = None
            try:
                self.redis_client = aioredis.from_url(
                    self.redis_url,
                    **self._redis_connection_kwargs(),
                )
                pubsub = self.redis_client.pubsub()
                await pubsub.subscribe(self.channel)
                logger.info("[KillSwitch] Subscribed to Redis channel '%s'.", self.channel)

                while self._running:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0,
                    )
                    if message:
                        await self._handle_command(message.get("data"))
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                logger.info("[KillSwitch] Listener task cancelled. Exiting.")
                return
            except (RedisError, OSError) as exc:
                if not self._running:
                    return
                logger.info("[KillSwitch] Redis connection lost (%s). Reconnecting in 5 seconds...", exc)
                await asyncio.sleep(5)
            except Exception as exc:
                if not self._running:
                    return
                logger.exception("[KillSwitch] Unexpected listener error: %s. Retrying in 5 seconds...", exc)
                await asyncio.sleep(5)
            finally:
                if self.redis_client is not None:
                    try:
                        await self.redis_client.aclose()
                    except Exception:
                        pass

    async def _handle_command(self, raw_command: Any) -> None:
        if not isinstance(raw_command, str):
            logger.warning("[KillSwitch] Ignoring invalid Redis command payload.")
            return

        if raw_command == "KILL":
            logger.critical("[KillSwitch] EMERGENCY SIGNAL RECEIVED: KILL. Suspending trading immediately!")
            await self.trigger_kill()
            return

        if raw_command in {"SUSPEND", "RESUME"}:
            status = await get_kill_switch_status_async()
            logger.info(
                "[KillSwitch] Distributed state synchronized: status=%s source=%s event_id=%s",
                "suspended" if status.suspended else "active",
                status.source,
                status.event_id,
            )

    async def trigger_kill(self) -> None:
        """Persist the emergency suspension and cancel all configured open orders."""
        try:
            await suspend_trading("Emergency KILL command", "redis_command")
        except KillSwitchStateError:
            logger.exception("[KillSwitch] Failed to persist distributed emergency suspension")

        cancel_failures: list[str] = []

        if self.engine and getattr(self.engine, "bybit_client", None):
            try:
                logger.info("[KillSwitch] Cancelling all Bybit Spot orders...")
                await asyncio.to_thread(
                    self.engine.bybit_client._request,
                    "POST",
                    "/v5/order/cancel-all",
                    json_data={"category": "spot"},
                    signed=True,
                )
                logger.info("[KillSwitch] All Bybit Spot orders successfully cancelled.")
            except Exception as e:
                cancel_failures.append(f"Bybit: {e}")
                logger.exception("[KillSwitch] Failed to cancel Bybit orders")

        if self.engine and getattr(self.engine, "t212_client", None):
            try:
                logger.info("[KillSwitch] Cancelling all Trading 212 open orders...")
                orders = await asyncio.to_thread(self.engine.t212_client.get_pending_orders)
                for order in orders:
                    order_id = order.get("orderId")
                    if order_id:
                        logger.info("[KillSwitch] Cancelling Trading 212 order: %s...", order_id)
                        await asyncio.to_thread(self.engine.t212_client.cancel_order, order_id)
                logger.info("[KillSwitch] All Trading 212 open orders successfully cancelled.")
            except Exception as e:
                cancel_failures.append(f"T212: {e}")
                logger.exception("[KillSwitch] Failed to cancel Trading 212 orders")

        await asyncio.to_thread(_write_confirmation)

        # C2-FIX: CRITICAL alert if cancel operations failed while state is suspended
        if cancel_failures:
            logger.critical(
                "[KillSwitch] EMERGENCY: Trading suspended but %d cancel operation(s) failed: %s. "
                "MANUAL INTERVENTION REQUIRED.",
                len(cancel_failures),
                "; ".join(cancel_failures),
            )
        else:
            logger.info("[KillSwitch] Emergency suspension confirmed and propagated.")
