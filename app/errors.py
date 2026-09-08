"""Centralized error handling for ORISUN IBUKUN."""
import tkinter as tk
from tkinter import messagebox
import traceback
import logging
from typing import Callable, Any, TypeVar

F = TypeVar('F', bound=Callable[..., Any])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application error."""
    def __init__(self, message: str, code: str = "ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ValidationError(AppError):
    """Validation error."""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")


class DatabaseError(AppError):
    """Database error."""
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")


class NotFoundError(AppError):
    """Resource not found error."""
    def __init__(self, message: str):
        super().__init__(message, "NOT_FOUND")


class PermissionError(AppError):
    """Permission denied error."""
    def __init__(self, message: str):
        super().__init__(message, "PERMISSION_DENIED")


def handle_error(
    error: Exception,
    context: str = "",
    show_dialog: bool = True,
    parent: tk.Misc | None = None
) -> str:
    """
    Centralized error handler.
    
    Args:
        error: The exception that occurred
        context: Additional context about where the error occurred
        show_dialog: Whether to show a message dialog
        parent: Parent widget for dialog
    
    Returns:
        Error message string
    """
    error_msg = str(error)
    
    if isinstance(error, AppError):
        logger.warning(f"{error.code}: {error_msg} | Context: {context}")
    else:
        logger.error(f"Unexpected error: {error_msg} | Context: {context}\n{traceback.format_exc()}")
    
    if show_dialog:
        if isinstance(error, ValidationError):
            messagebox.showwarning("Validation Error", error_msg, parent=parent)
        elif isinstance(error, NotFoundError):
            messagebox.showinfo("Not Found", error_msg, parent=parent)
        elif isinstance(error, PermissionError):
            messagebox.showerror("Permission Denied", error_msg, parent=parent)
        elif isinstance(error, DatabaseError):
            messagebox.showerror("Database Error", error_msg, parent=parent)
        else:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{error_msg}", parent=parent)
    
    return error_msg


def safe_execute(
    func: F,
    *args,
    context: str = "",
    show_dialog: bool = True,
    parent: tk.Misc | None = None,
    default_return: Any = None,
    **kwargs
) -> Any:
    """
    Safely execute a function with centralized error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments
        context: Context for error logging
        show_dialog: Whether to show error dialog
        parent: Parent widget for dialog
        default_return: Default return value on error
        **kwargs: Keyword arguments
    
    Returns:
        Function result or default_return on error
    """
    try:
        return func(*args, **kwargs)
    except AppError as e:
        handle_error(e, context=context, show_dialog=show_dialog, parent=parent)
        return default_return
    except Exception as e:
        handle_error(e, context=context, show_dialog=show_dialog, parent=parent)
        return default_return


def require_role(user_role: str, allowed_roles: list[str]) -> None:
    """Check if user has required role."""
    if user_role not in allowed_roles:
        raise PermissionError(f"Required role: {', '.join(allowed_roles)}. Current: {user_role}")


def validate_input(value: str, field_name: str, validators: list[Callable[[str], Any]] = None) -> str:
    """
    Validate input with multiple validators.
    
    Args:
        value: Input value
        field_name: Field name for error messages
        validators: List of validator functions
    
    Returns:
        Validated value
    
    Raises:
        ValidationError: If validation fails
    """
    if not value or not value.strip():
        raise ValidationError(f"{field_name} is required.")
    
    value = value.strip()
    
    if validators:
        for validator in validators:
            result = validator(value)
            if result is not True:
                raise ValidationError(result if isinstance(result, str) else f"Invalid {field_name}.")
    
    return value