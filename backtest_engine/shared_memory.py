"""
backtest_engine/shared_memory.py

Zero-copy memory sharing architecture using POSIX shared memory (/dev/shm)
and Python's multiprocessing.shared_memory module.
Allows high-speed concurrent read-only access to pre-calculated indicators.
"""

from __future__ import annotations

import logging
from multiprocessing import shared_memory
import numpy as np

logger = logging.getLogger(__name__)


class SharedIndicatorVolume:
    """
    Manages the lifecycle, read-only worker mapping, and destruction of static
    multi-dimensional NumPy arrays in system shared memory (/dev/shm).
    """

    def __init__(
        self,
        array_to_share: np.ndarray | None = None,
        shm_name: str | None = None,
        shape: tuple[int, ...] | None = None,
        dtype: np.dtype | str | None = None,
    ):
        self.shm: shared_memory.SharedMemory | None = None
        self.shm_name: str | None = None
        self.shape: tuple[int, ...] | None = None
        self.dtype: np.dtype | None = None
        self.nbytes: int | None = None

        if array_to_share is not None:
            # Parent process flow: allocate POSIX segment and copy the data
            self.shape = array_to_share.shape
            self.dtype = np.dtype(array_to_share.dtype)
            self.nbytes = array_to_share.nbytes

            self.shm = shared_memory.SharedMemory(create=True, size=self.nbytes)
            self.shm_name = self.shm.name

            # Map array to write initial data
            parent_view = np.ndarray(self.shape, dtype=self.dtype, buffer=self.shm.buf)
            parent_view[:] = array_to_share[:]
            logger.debug(f"Allocated shared memory '{self.shm_name}' with size {self.nbytes} bytes.")
        else:
            # Worker process flow: capture descriptor values for lazy mapping
            if shm_name is None or shape is None or dtype is None:
                raise ValueError("Worker attachment requires shm_name, shape, and dtype")
            self.shm_name = shm_name
            self.shape = shape
            self.dtype = np.dtype(dtype)

    def get_view(self) -> np.ndarray:
        """
        Retrieves a local numpy view pointing directly to the underlying raw buffer.
        By operating on raw pointer offsets, this avoids triggering Copy-on-Write (CoW)
        duplications under Linux multiprocessing forks.
        """
        if self.shm is None:
            try:
                self.shm = shared_memory.SharedMemory(name=self.shm_name, create=False)
            except Exception as exc:
                logger.error(f"Failed to attach to shared memory '{self.shm_name}': {exc}")
                raise
        return np.ndarray(self.shape, dtype=self.dtype, buffer=self.shm.buf)

    def close(self) -> None:
        """
        Closes current handle's mapping to the shared memory segment.
        Must be called by each child process once finished.
        """
        if self.shm is not None:
            try:
                self.shm.close()
            except Exception as exc:
                logger.debug(f"Error closing shared memory view '{self.shm_name}': {exc}")

    def unlink(self) -> None:
        """
        Destroys the POSIX shared memory segment, releasing OS resources.
        Should only be called by the allocating parent process.
        """
        if self.shm is not None:
            try:
                self.shm.close()
            except Exception:
                pass
            try:
                self.shm.unlink()
                logger.debug(f"Destroyed shared memory segment '{self.shm_name}'.")
            except FileNotFoundError:
                pass
            except Exception as exc:
                logger.warning(f"Error unlinking shared memory '{self.shm_name}': {exc}")
