"""Validation helpers."""
import re
import html


def sanitize_string(value: str, max_length: int | None = None) -> str:
    """Sanitize string input - strip whitespace and escape HTML."""
    value = value.strip()
    value = html.escape(value)
    if max_length and len(value) > max_length:
        value = value[:max_length]
    return value


def validate_member_id(member_id: str) -> bool:
    return bool(re.match(r"^ORI-\d{5}$", member_id))


def validate_amount(value: str) -> float:
    cleaned = value.replace(",", "").replace("₦", "").strip()
    if not cleaned:
        raise ValueError("Amount is required.")
    try:
        amount = float(cleaned)
    except ValueError:
        raise ValueError("Please enter a valid number.")
    if amount < 0:
        raise ValueError("Amount cannot be negative.")
    return amount


def validate_positive_amount(value: str) -> float:
    """Validate amount is positive (greater than zero)."""
    amount = validate_amount(value)
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    return amount


def validate_phone(phone: str) -> bool:
    cleaned = phone.strip().replace(" ", "").replace("-", "")
    return len(cleaned) >= 7 and cleaned.isdigit()


def validate_phone_strict(phone: str) -> str:
    """Validate and return cleaned phone number."""
    cleaned = phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not cleaned:
        raise ValueError("Phone number is required.")
    if not cleaned.isdigit():
        raise ValueError("Phone number must contain only digits.")
    if len(cleaned) < 7:
        raise ValueError("Phone number must be at least 7 digits.")
    return cleaned


def validate_email(email: str) -> str:
    """Validate email format."""
    email = email.strip().lower()
    if not email:
        raise ValueError("Email is required.")
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError("Please enter a valid email address.")
    return email


def validate_required(value: str, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} is required.")
    return value


def validate_pin(pin: str) -> str:
    """Validate PIN - must be 4-6 digits."""
    pin = pin.strip()
    if not pin:
        raise ValueError("PIN is required.")
    if not pin.isdigit():
        raise ValueError("PIN must contain only digits.")
    if len(pin) < 4 or len(pin) > 6:
        raise ValueError("PIN must be 4-6 digits.")
    return pin


def validate_name(name: str, field_name: str = "Name") -> str:
    """Validate name - Unicode letters (incl. diacritics), digits, spaces, hyphens, apostrophes, periods."""
    name = name.strip()
    if not name:
        raise ValueError(f"{field_name} is required.")
    if len(name) < 2:
        raise ValueError(f"{field_name} must be at least 2 characters.")
    for ch in name:
        if not (ch.isalpha() or ch.isdigit() or ch in " .-'"):
            raise ValueError(f"{field_name} contains an invalid character: {ch!r}.")
    return name


def sanitize_input(value: str, max_length: int = 500) -> str:
    """General purpose input sanitization."""
    return sanitize_string(value, max_length)
