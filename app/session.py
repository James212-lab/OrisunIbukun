"""Session management for ORISUN IBUKUN - using Tkinter's after() for thread safety."""
import tkinter as tk
from typing import Callable, Optional


class SessionManager:
    """Manages user session with automatic timeout using Tkinter's event loop."""

    def __init__(
        self,
        root: tk.Misc,
        timeout_minutes: int = 20,
        warning_minutes: int = 5,
        on_timeout: Optional[Callable[[], None]] = None,
        on_warning: Optional[Callable[[int], None]] = None
    ):
        self.root = root
        self.timeout_seconds = timeout_minutes * 60
        self.warning_seconds = warning_minutes * 60
        self.on_timeout = on_timeout
        self.on_warning = on_warning

        self._last_activity = 0
        self._after_id: Optional[str] = None
        self._warning_shown = False
        self._running = False

    def start(self) -> None:
        """Start the session timer."""
        self._running = True
        self._last_activity = self._now()
        self._warning_shown = False
        self._schedule_tick()

    def stop(self) -> None:
        """Stop the session timer."""
        self._running = False
        if self._after_id:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def record_activity(self) -> None:
        """Record user activity to reset the timeout."""
        self._last_activity = self._now()
        self._warning_shown = False

    def get_remaining_time(self) -> int:
        """Get remaining session time in seconds."""
        elapsed = self._now() - self._last_activity
        remaining = self.timeout_seconds - elapsed
        return max(0, int(remaining))

    def is_expired(self) -> bool:
        """Check if session has expired."""
        return self.get_remaining_time() <= 0

    def _now(self) -> float:
        """Get current time in seconds (use time.time for accuracy)."""
        import time
        return time.time()

    def _schedule_tick(self) -> None:
        """Schedule the next timer tick."""
        if not self._running:
            return
        self._after_id = self.root.after(1000, self._on_tick)

    def _on_tick(self) -> None:
        """Timer tick - check for warning/timeout."""
        if not self._running:
            return

        remaining = self.get_remaining_time()

        # Show warning
        if remaining <= self.warning_seconds and remaining > 0 and not self._warning_shown:
            self._warning_shown = True
            if self.on_warning:
                # Ensure callback runs on main thread
                self.root.after(0, lambda: self.on_warning(remaining))

        # Timeout
        if remaining <= 0:
            if self.on_timeout:
                self.root.after(0, self.on_timeout)
            self.stop()
            return

        # Schedule next tick
        self._schedule_tick()


class SessionMixin:
    """Mixin to add session management to a Tkinter window."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._session_manager = SessionManager(
            root=self,
            timeout_minutes=20,
            warning_minutes=5,
            on_timeout=self._on_session_timeout,
            on_warning=self._on_session_warning
        )
        self._bind_activity_events()
        self._session_manager.start()

    def _bind_activity_events(self) -> None:
        """Bind events that count as user activity - only to self, not globally."""
        events = [
            '<Key>', '<Button>', '<Motion>', '<Enter>', '<Leave>',
            '<FocusIn>', '<FocusOut>', '<MouseWheel>'
        ]
        for event in events:
            self.bind(event, self._on_activity, add='+')

    def _on_activity(self, event: tk.Event) -> None:
        """Handle user activity event."""
        self._session_manager.record_activity()

    def _on_session_warning(self, remaining_seconds: int) -> None:
        """Handle session warning - show dialog."""
        from tkinter import messagebox
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        if minutes <= 1:
            messagebox.showwarning(
                "Session Expiring Soon",
                f"Your session will expire in {minutes} minute(s) {seconds} seconds due to inactivity.",
                parent=self
            )

    def _on_session_timeout(self) -> None:
        """Handle session timeout - logout user."""
        from tkinter import messagebox
        messagebox.showinfo("Session Expired", "Your session has expired due to inactivity.", parent=self)
        if hasattr(self, 'logout'):
            self.logout()
        elif hasattr(self, 'destroy'):
            self.destroy()

    def reset_session(self) -> None:
        """Reset the session timer."""
        self._session_manager.record_activity()

    def get_session_info(self) -> dict:
        """Get current session info."""
        return {
            "remaining_seconds": self._session_manager.get_remaining_time(),
            "is_expired": self._session_manager.is_expired(),
        }

    def _cleanup_session(self) -> None:
        """Clean up session manager - call on logout/destroy."""
        self._session_manager.stop()