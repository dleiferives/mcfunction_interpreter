"""Entity selector parser for Minecraft commands.

This module handles parsing of entity selectors like @a, @e[type=zombie], etc.
Note: Selectors are parsed for syntax validation only, not resolved to actual entities.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Range:
    """Represents a numeric range like 5, ..10, 5.., 5..10."""

    min: int | None  # None means no lower bound
    max: int | None  # None means no upper bound

    def __str__(self) -> str:
        if self.min is None and self.max is None:
            return ".."
        elif self.min is None:
            return f"..{self.max}"
        elif self.max is None:
            return f"{self.min}.."
        elif self.min == self.max:
            return str(self.min)
        else:
            return f"{self.min}..{self.max}"


@dataclass
class ScoreMatcher:
    """Represents a score objective comparison."""

    objective: str
    value: int | Range


# Type alias for selector argument values
SelectorArgValue = str | int | float | Range | tuple[float, float, float] | dict[str, ScoreMatcher]


@dataclass
class EntitySelector:
    """Represents a parsed entity selector."""

    selector_type: str  # 'a', 'e', 'p', 'r', 's'
    # Arguments can be:
    # - str (for type, tag, name, sort)
    # - int (for limit)
    # - float (for dx, dy, dz)
    # - Range (for distance, x/y_rotation)
    # - tuple[float, float, float] (for x, y, z coordinates)
    # - dict[str, ScoreMatcher] (for scores)
    arguments: dict[str, SelectorArgValue]


class SelectorParser:
    """Parser for entity selector arguments."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def peek(self, n: int = 1) -> str:
        """Peek ahead n characters without consuming."""
        return self.text[self.pos : self.pos + n]

    def consume(self, n: int = 1) -> str:
        """Consume n characters and return them."""
        result = self.text[self.pos : self.pos + n]
        self.pos += n
        return result

    def skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def parse_key_value(self) -> tuple[str, str | int | float | Range | dict[str, ScoreMatcher]]:
        """Parse a single key=value pair."""
        self.skip_whitespace()

        # Parse key
        key_start = self.pos
        while self.pos < len(self.text):
            char = self.text[self.pos]
            if char.isalnum() or char == "_":
                self.pos += 1
            else:
                break
        key = self.text[key_start : self.pos]

        if not key:
            raise ValueError(f"Expected key at position {self.pos}")

        self.skip_whitespace()

        # Expect equals
        if self.peek() != "=":
            raise ValueError(f"Expected = after key '{key}'")
        self.consume()  # consume =

        self.skip_whitespace()

        # Parse value based on key type - need explicit typing for mypy
        # Note: x/y/z are grouped into 'coordinates' tuple
        # dx/dy/dz are individual floats
        value: str | int | float | Range | dict[str, ScoreMatcher]
        if key == "type":
            value = self.parse_string()
        elif key == "tag":
            value = self.parse_string()
        elif key == "name":
            value = self.parse_string()
        elif key == "sort":
            value = self.parse_sort_value()
        elif key == "limit":
            value = self.parse_int()
        elif key in ("x", "y", "z", "dx", "dy", "dz"):
            value = self.parse_float()
        elif key == "distance":
            value = self.parse_range()
        elif key == "scores":
            value = self.parse_scores()
        elif key == "x_rotation":
            value = self.parse_range()
        elif key == "y_rotation":
            value = self.parse_range()
        else:
            # Unknown key - try to parse as string
            value = self.parse_string()

        return key, value

    def parse_string(self) -> str:
        """Parse a string value (quoted or unquoted)."""
        self.skip_whitespace()

        # Check for quoted string
        if self.peek() == '"' or self.peek() == "'":
            quote = self.consume()
            start = self.pos
            while self.pos < len(self.text):
                if self.text[self.pos] == quote:
                    break
                if self.text[self.pos] == "\\":
                    # Skip escaped character
                    self.pos += 2
                else:
                    self.pos += 1
            if self.pos >= len(self.text):
                raise ValueError(f"Unterminated string starting at position {start-1}")
            value = self.text[start : self.pos]
            self.consume()  # consume closing quote
            return value

        # Unquoted string - parse until comma or end
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] not in ",]":
            self.pos += 1
        value = self.text[start : self.pos].strip()
        if not value:
            raise ValueError(f"Expected string value at position {start}")
        return value

    def parse_sort_value(self) -> str:
        """Parse sort value (valid options: nearest, furthest, random, arbitrary)."""
        value = self.parse_string()
        valid_sorts = {"nearest", "furthest", "random", "arbitrary"}
        if value not in valid_sorts:
            raise ValueError(f"Invalid sort value '{value}'. Must be one of {valid_sorts}")
        return value

    def parse_int(self) -> int:
        """Parse an integer value."""
        self.skip_whitespace()
        start = self.pos
        # Handle negative numbers
        if self.peek() == "-":
            self.consume()
        while self.pos < len(self.text) and self.text[self.pos].isdigit():
            self.pos += 1
        num_str = self.text[start : self.pos]
        if not num_str or num_str == "-":
            raise ValueError(f"Expected integer at position {start}")
        return int(num_str)

    def parse_float(self) -> float:
        """Parse a float value."""
        self.skip_whitespace()
        start = self.pos
        # Handle negative numbers
        if self.peek() == "-":
            self.consume()
        has_dot = False
        while self.pos < len(self.text):
            char = self.text[self.pos]
            if char.isdigit():
                self.pos += 1
            elif char == "." and not has_dot:
                has_dot = True
                self.pos += 1
            else:
                break
        num_str = self.text[start : self.pos]
        if not num_str or num_str == "-" or num_str.endswith("."):
            raise ValueError(f"Expected float at position {start}")
        return float(num_str)

    def parse_range(self) -> Range:
        """Parse a range value like 5, ..10, 5.., 5..10."""
        self.skip_whitespace()

        # Check for .. prefix (no minimum)
        if self.peek(2) == "..":
            self.consume(2)
            # Check if there's a number after
            if self.pos >= len(self.text) or self.text[self.pos] in ",]":
                return Range(None, None)
            max_val = self.parse_int()
            return Range(None, max_val)

        # Parse first number
        min_val = self.parse_int()

        self.skip_whitespace()

        # Check for .. suffix
        if self.peek(2) == "..":
            self.consume(2)
            # Check if there's a second number
            if self.pos >= len(self.text) or self.text[self.pos] in ",]":
                return Range(min_val, None)
            max_val = self.parse_int()
            return Range(min_val, max_val)

        # Single number
        return Range(min_val, min_val)

    def parse_scores(self) -> dict[str, ScoreMatcher]:
        """Parse scores argument like {objective=10..20,other=5}."""
        self.skip_whitespace()

        if self.peek() != "{":
            raise ValueError("Expected { for scores at position %d" % self.pos)
        self.consume()  # consume {

        scores: dict[str, ScoreMatcher] = {}

        while True:
            self.skip_whitespace()

            if self.peek() == "}":
                self.consume()  # consume }
                break

            # Parse objective name
            obj_start = self.pos
            while self.pos < len(self.text):
                char = self.text[self.pos]
                if char.isalnum() or char == "_":
                    self.pos += 1
                else:
                    break
            objective = self.text[obj_start : self.pos]

            if not objective:
                raise ValueError(f"Expected objective name at position {obj_start}")

            self.skip_whitespace()

            if self.peek() != "=":
                raise ValueError(f"Expected = after objective '{objective}'")
            self.consume()  # consume =

            self.skip_whitespace()

            # Parse value (can be int or range)
            score_value: int | Range
            if self.peek(2) == ".." or (
                self.pos + 1 < len(self.text)
                and self.text[self.pos + 1] == "."
                and self.text[self.pos].isdigit()
            ):
                # Could be range
                score_value = self.parse_range()
            else:
                # Try to detect if it's a range by looking ahead
                temp_pos = self.pos
                has_dot = False
                while temp_pos < len(self.text) and self.text[temp_pos] not in ",}":
                    if self.text[temp_pos] == ".":
                        has_dot = True
                    temp_pos += 1

                if has_dot or (self.pos < len(self.text) and self.text[self.pos] == "-"):
                    score_value = self.parse_range()
                else:
                    score_value = self.parse_int()

            scores[objective] = ScoreMatcher(objective, score_value)

            self.skip_whitespace()

            if self.peek() == ",":
                self.consume()
            elif self.peek() == "}":
                continue
            else:
                raise ValueError(f"Expected , or }} after score, got '{self.peek()}'")

        return scores

    def parse(self) -> dict[str, SelectorArgValue]:
        """Parse all arguments."""
        args: dict[str, SelectorArgValue] = {}
        coords: list[float] = []

        while self.pos < len(self.text):
            self.skip_whitespace()

            if self.pos >= len(self.text):
                break

            if self.peek() == "]":
                break

            if self.peek() == ",":
                self.consume()
                continue

            key, value = self.parse_key_value()

            # Special handling for coordinates - need to group x, y, z
            # dx, dy, dz are handled via the else branch below
            if key == "x":
                # value is float for x
                coords.append(value)  # type: ignore[arg-type]
            elif key == "y":
                # Ensure we have x first
                while len(coords) < 1:
                    coords.append(0.0)
                # value is float for y
                coords.append(value)  # type: ignore[arg-type]
            elif key == "z":
                # Ensure we have x and y first
                while len(coords) < 2:
                    coords.append(0.0)
                # value is float for z
                coords.append(value)  # type: ignore[arg-type]
            else:
                # dx/dy/dz and other arguments
                args[key] = value  # type: ignore[assignment]

        # Store coordinates as tuple if any were found
        if coords:
            args["coordinates"] = tuple(coords)  # type: ignore[assignment]

        return args


def parse_selector(selector: str) -> EntitySelector:
    """Parse an entity selector.

    Args:
        selector: Entity selector string (e.g., '@a', '@e[type=zombie]')

    Returns:
        EntitySelector with parsed type and arguments

    Raises:
        ValueError: If selector syntax is invalid
    """
    if not selector.startswith("@"):
        raise ValueError(f"Selector must start with @: {selector}")

    if len(selector) < 2:
        raise ValueError("Selector must have a type character after @")

    selector_char = selector[1]

    if selector_char not in "apers":
        raise ValueError(f"Invalid selector type: @{selector_char}")

    # Check for arguments
    if len(selector) == 2:
        return EntitySelector(selector_char, {})

    if selector[2] != "[":
        raise ValueError(f"Expected [ after selector type, got '{selector[2]}'")

    if selector[-1] != "]":
        raise ValueError("Selector must end with ]")

    # Parse arguments
    args_str = selector[3:-1]  # Remove [@ and ]
    parser = SelectorParser(args_str)
    args = parser.parse()

    return EntitySelector(selector_char, args)
