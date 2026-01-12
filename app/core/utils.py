"""
Utility functions for the application.
Contains helper functions that can be used across the application without causing circular imports.
"""

import secrets
import string


def generate_short_id(length: int = 4) -> str:
    """
    Generate a short random ID using alphanumeric characters (uppercase + digits).
    Uses secrets module for cryptographically strong random generation.

    Args:
        length: Length of the ID (default: 4)

    Returns:
        Random alphanumeric string of specified length

    Note:
        With 4 characters using [A-Z0-9], there are 36^4 = 1,679,616 possible combinations.
        Ensure uniqueness checks in the database to prevent collisions.
    
    Example:
        >>> generate_short_id()
        'A1B2'
        >>> generate_short_id(6)
        'X9Y2K1'
    """
    alphabet = string.ascii_uppercase + string.digits  # A-Z, 0-9
    return "".join(secrets.choice(alphabet) for _ in range(length))
