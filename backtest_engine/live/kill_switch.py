import os
import asyncio
import logging
from typing import Any, Optional
import redis.asyncio as aioredis

logger = logging.getLogger("papertrader")

# Global memory flag to suspend all trading strategies
_trading_suspended: bool = False

def is_trading_suspended() -> bool:
    """Check if trading has been suspended by the Kill Switch."""
    return _trading_suspended

def set_trading_suspended(value: bool) -> None:
    """Set the trading suspension flag."""
    global _trading_suspended
    _trading_suspended = value


class KillSwitchListener:
    """
    Asynchronous listener that subscribes to Redis pub/sub channel 'URGENCY'.
    When a 'KILL' command is received, suspends all strategies and cancels all active orders.
    """
    def __init__(self, engine: Any, redis_url: Optional[str] = None) -> None:
        self.engine = engine
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self._listener_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """Start listening to the Pub/Sub channel in the background."""
        if not self.redis_url:
            logger.warning("[KillSwitch] REDIS_URL is not set. Kill Switch cannot run in distributed pub/sub mode.")
            return

        self._running = True
        self._listener_task = asyncio.create_task(self._listen_loop())
        logger.info("[KillSwitch] Asynchronous ESMA RTS 6 Kill Switch listener started.")

    async def stop(self) -> None:
        """Stop the background listener."""
        self._running = False
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            logger.info("[KillSwitch] Kill Switch listener stopped.")

    async def _listen_loop(self) -> None:
        while self._running:
            try:
                redis_user = os.getenv("REDIS_USER")
                redis_password = os.getenv("REDIS_PASSWORD")
                
                redis_kwargs = {
                    "decode_responses": True,
                    "socket_timeout": 10,
                }
                if redis_user:
                    redis_kwargs["username"] = redis_user
                if redis_password:
                    redis_kwargs["password"] = redis_password
                    
                client = aioredis.from_url(self.redis_url, **redis_kwargs)
                pubsub = client.pubsub()
                await pubsub.subscribe("URGENCY")
                
                logger.info("[KillSwitch] Subscribed to Redis channel 'URGENCY'.")
                
                while self._running:
                    # Check for messages with timeout
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message:
                        data = message.get("data")
                        if data == "KILL":
                            logger.critical("[KillSwitch] EMERGENCY SIGNAL RECEIVED: KILL. Suspending trading immediately!")
                            await self.trigger_kill()
                    await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"[KillSwitch] Connection error or error in listen loop: {e}. Retrying in 5 seconds...")
                await asyncio.sleep(5)

    async def trigger_kill(self) -> None:
        """Trigger the emergency suspension and order cancellations."""
        # 1. Suspend in memory and distributed
        set_trading_suspended(True)
        
        # Share status via Redis for other workers/containers
        try:
            redis_user = os.getenv("REDIS_USER")
            redis_password = os.getenv("REDIS_PASSWORD")
            redis_kwargs = {}
            if redis_user:
                redis_kwargs["username"] = redis_user
            if redis_password:
                redis_kwargs["password"] = redis_password
            client = aioredis.from_url(self.redis_url, **redis_kwargs)
            await client.set("trading:suspended", "true")
        except Exception as re:
            logger.exception(f"[KillSwitch] Failed to set distributed suspend flag in Redis: {re}")

        # 2. Cancel Bybit orders
        if self.engine and getattr(self.engine, "bybit_client", None):
            try:
                logger.info("[KillSwitch] Cancelling all Bybit Spot orders...")
                await asyncio.to_thread(
                    self.engine.bybit_client._request,
                    "POST",
                    "/v5/order/cancel-all",
                    json_data={"category": "spot"},
                    signed=True
                )
                logger.info("[KillSwitch] All Bybit Spot orders successfully cancelled.")
            except Exception as e:
                logger.exception(f"[KillSwitch] Failed to cancel Bybit orders: {e}")

        # 3. Cancel Trading 212 orders
        if self.engine and getattr(self.engine, "t212_client", None):
            try:
                logger.info("[KillSwitch] Cancelling all Trading 212 open orders...")
                # Fetch pending/open orders
                orders = await asyncio.to_thread(self.engine.t212_client.get_pending_orders)
                for order in orders:
                    order_id = order.get("orderId")
                    if order_id:
                        logger.info(f"[KillSwitch] Cancelling Trading 212 order: {order_id}...")
                        await asyncio.to_thread(self.engine.t212_client.cancel_order, order_id)
                logger.info("[KillSwitch] All Trading 212 open orders successfully cancelled.")
            except Exception as e:
                logger.exception(f"[KillSwitch] Failed to cancel Trading 212 orders: {e}")
