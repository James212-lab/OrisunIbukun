"""Utility helpers."""
import hashlib
import os
import sys
import uuid
import datetime
import threading
from pathlib import Path
from typing import Callable, TypeVar, Any

F = TypeVar('F', bound=Callable[..., Any])


def generate_id(prefix: str = "TX") -> str:
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    short = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{ts}-{short}"


def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


def format_currency(amount: float) -> str:
    currency = "₦"
    if amount < 0:
        return f"-{currency}{abs(amount):,.0f}"
    return f"{currency}{amount:,.0f}"


def get_asset_path(filename: str) -> str:
    """Resolve a bundled asset (works in source runs and PyInstaller builds)."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))) / "assets"
    else:
        base = Path(__file__).resolve().parent.parent / "assets"
    return str(base / filename)


def set_window_icon(window) -> None:
    """Apply the app logo to a Tk window; silently ignore failures."""
    try:
        ico = get_asset_path("icon.ico")
        if os.path.exists(ico):
            window.iconbitmap(ico)
            return
    except Exception:
        pass
    try:
        import tkinter as tk
        png = get_asset_path("icon.png")
        if os.path.exists(png):
            img = tk.PhotoImage(file=png)
            window.iconphoto(True, img)
            window._icon_ref = img  # keep a reference
    except Exception:
        pass


def today_str() -> str:
    return datetime.date.today().isoformat()


def now_str() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def debounce(wait_ms: int) -> Callable[[F], F]:
    """
    Decorator to debounce a function call.
    
    Args:
        wait_ms: Milliseconds to wait before executing
        
    Example:
        @debounce(300)
        def on_search(query: str):
            ...
    """
    def decorator(func: F) -> F:
        timer: threading.Timer | None = None
        lock = threading.Lock()
        
        def wrapper(*args: Any, **kwargs: Any) -> None:
            nonlocal timer
            with lock:
                if timer:
                    timer.cancel()
                timer = threading.Timer(wait_ms / 1000.0, func, args=args, kwargs=kwargs)
                timer.daemon = True
                timer.start()
        
        return wrapper  # type: ignore
    return decorator


class PaginationHelper:
    """Helper for paginated queries."""
    
    def __init__(self, page_size: int = 50):
        self.page_size = page_size
        self.current_page = 1
        self.total_items = 0
        self.total_pages = 0
    
    def get_offset(self) -> int:
        """Get the OFFSET value for SQL query."""
        return (self.current_page - 1) * self.page_size
    
    def get_limit(self) -> int:
        """Get the LIMIT value for SQL query."""
        return self.page_size
    
    def set_total_items(self, total: int) -> None:
        """Set total items and calculate pages."""
        self.total_items = total
        self.total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
    
    def next_page(self) -> bool:
        """Go to next page. Returns True if page changed."""
        if self.current_page < self.total_pages:
            self.current_page += 1
            return True
        return False
    
    def prev_page(self) -> bool:
        """Go to previous page. Returns True if page changed."""
        if self.current_page > 1:
            self.current_page -= 1
            return True
        return False
    
    def go_to_page(self, page: int) -> bool:
        """Go to specific page. Returns True if page changed."""
        if 1 <= page <= self.total_pages:
            self.current_page = page
            return True
        return False
    
    def get_page_info(self) -> dict:
        """Get pagination info for display."""
        return {
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "total_items": self.total_items,
            "page_size": self.page_size,
            "has_next": self.current_page < self.total_pages,
            "has_prev": self.current_page > 1,
            "start_item": (self.current_page - 1) * self.page_size + 1 if self.total_items > 0 else 0,
            "end_item": min(self.current_page * self.page_size, self.total_items),
        }
