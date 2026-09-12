"""Single-instance enforcement using a Windows named mutex."""
import sys
import ctypes

_MUTEX_NAME = "Global\\OrisunIbukun_SingleInstance"


class SingleInstanceGuard:
    """Prevents multiple instances via a named mutex. Release on exit."""

    def __init__(self):
        self._handle = None

    def acquire(self) -> bool:
        """Try to acquire the mutex. Returns True if this is the only instance."""
        if sys.platform != "win32":
            return True
        try:
            handle = ctypes.windll.kernel32.CreateMutexW(None, True, _MUTEX_NAME)
            if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
                ctypes.windll.kernel32.CloseHandle(handle)
                return False
            self._handle = handle
            return True
        except Exception:
            return True

    def release(self) -> None:
        if self._handle:
            try:
                ctypes.windll.kernel32.CloseHandle(self._handle)
            except Exception:
                pass
            self._handle = None
