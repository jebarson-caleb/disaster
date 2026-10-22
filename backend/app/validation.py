"""Request-payload validation shared by the operational API routes.

Every helper raises ``ValueError`` with a user-safe message. The application
error handler converts ``ValueError`` into a 400 response, so routes can call
these helpers directly without wrapping each one.
"""

from math import isfinite


def text(data, name, max_length, required=True, default=""):
    """Return trimmed text, enforcing presence and the column length."""
    value = data.get(name)
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ValueError(f"{name} is required")
        return default
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be text")
    output = str(value).strip()
    if len(output) > max_length:
        raise ValueError(f"{name} must contain at most {max_length} characters")
    return output


def optional_text(data, name, max_length):
    return text(data, name, max_length, required=False, default=None)


def choice(data, name, allowed, default=None):
    value = data.get(name, default)
    normalized = str(value).strip().lower() if value is not None else None
    if normalized not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(sorted(allowed))}")
    return normalized


def coordinate(value, name, minimum, maximum):
    try:
        output = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a number") from error
    if not isfinite(output) or not minimum <= output <= maximum:
        raise ValueError(f"{name} is outside valid bounds")
    return output


def latitude(value, name="latitude"):
    return coordinate(value, name, -90, 90)


def longitude(value, name="longitude"):
    return coordinate(value, name, -180, 180)


def optional_latitude(value, name="latitude"):
    return None if value in {None, ""} else latitude(value, name)


def optional_longitude(value, name="longitude"):
    return None if value in {None, ""} else longitude(value, name)


def whole_number(value, name, minimum=0, maximum=1_000_000):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a whole number")
    try:
        output = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a whole number") from error
    if isinstance(value, float) and value != output:
        raise ValueError(f"{name} must be a whole number")
    if not minimum <= output <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return output


def optional_whole_number(value, name, minimum=0, maximum=1_000_000, default=0):
    return default if value in {None, ""} else whole_number(value, name, minimum, maximum)


def http_url(value, name, max_length=500):
    output = str(value or "").strip()
    if not output:
        return None
    if len(output) > max_length:
        raise ValueError(f"{name} must contain at most {max_length} characters")
    if not output.startswith(("https://", "http://")):
        raise ValueError(f"{name} must start with http:// or https://")
    return output
