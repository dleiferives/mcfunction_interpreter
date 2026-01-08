"""Entity selector parser for Minecraft commands.

This module handles parsing of entity selectors like @a, @e[type=zombie], etc.
Note: Selectors are parsed for syntax validation only, not resolved to actual entities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class EntitySelector:
    """Represents a parsed entity selector."""
    selector_type: str  # 'a', 'e', 'p', 'r', 's'
    arguments: dict[str, str | int | tuple]  # Selector arguments


def parse_selector(selector: str) -> EntitySelector:
    """Parse an entity selector.

    Args:
        selector: Entity selector string (e.g., '@a', '@e[type=zombie]')

    Returns:
        EntitySelector with parsed type and arguments

    Raises:
        ValueError: If selector syntax is invalid
    """
    if not selector.startswith('@'):
        raise ValueError(f"Selector must start with @: {selector}")

    selector_char = selector[1]

    if selector_char not in 'aper':
        raise ValueError(f"Invalid selector type: @")

    # Check for arguments
    if len(selector) == 2:
        return EntitySelector(selector_char, {})

    if selector[2] != '[':
        raise ValueError(f"Expected [ after selector type")

    # Parse arguments - this is a simplified version
    # Full implementation would go here
    args_str = selector[3:-1]  # Remove [ and ]
    args = {}

    # Very basic parsing - just store as raw string for now
    args['raw'] = args_str

    return EntitySelector(selector_char, args)
