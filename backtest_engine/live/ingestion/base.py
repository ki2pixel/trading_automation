from abc import ABC, abstractmethod
from typing import Dict

class BasePriceIngestor(ABC):
    """Base class defining the contract for real-time price ingestors."""

    @abstractmethod
    def poll_and_cache(self) -> Dict[str, float]:
        """Polls prices from the API and caches them locally, to Redis, and PostgreSQL."""
        pass

    @abstractmethod
    def start_loop(self, interval_seconds: int = 60) -> None:
        """Starts a blocking loop to poll prices periodically."""
        pass

    @abstractmethod
    async def start_loop_async(self, interval_seconds: int = 60) -> None:
        """Starts an async loop to poll prices periodically."""
        pass
