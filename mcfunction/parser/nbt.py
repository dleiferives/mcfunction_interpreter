"""NBT/SNBT parser for Minecraft data structures.

Handles parsing of Stringified Named Binary Tag (SNBT) format used in Minecraft commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union, Any
import re


# Type definitions
@dataclass
class NBTByte:
    value: int

    def __str__(self) -> str:
        return f"{self.value}b"


@dataclass
class NBTShort:
    value: int

    def __str__(self) -> str:
        return f"{self.value}s"


@dataclass
class NBTInt:
    value: int

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class NBTLong:
    value: int

    def __str__(self) -> str:
        return f"{self.value}L"


@dataclass
class NBTFloat:
    value: float

    def __str__(self) -> str:
        return f"{self.value}f"


@dataclass
class NBTDouble:
    value: float

    def __str__(self) -> str:
        return f"{self.value}d"


@dataclass
class NBTString:
    value: str

    def __str__(self) -> str:
        if re.match(r'^[a-zA-Z0-9_.+-]+$', self.value) and not self.value.startswith('"'):
            return self.value
        escaped = self.value.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'


@dataclass
class NBTByteArray:
    value: list[NBTByte]

    def __str__(self) -> str:
        return f"[B;{','.join(str(b) for b in self.value)}]"


@dataclass
class NBTIntArray:
    value: list[NBTInt]

    def __str__(self) -> str:
        return f"[I;{','.join(str(i) for i in self.value)}]"


@dataclass
class NBTLongArray:
    value: list[NBTLong]

    def __str__(self) -> str:
        return f"[L;{','.join(str(l) for l in self.value)}]"


@dataclass
class NBTList:
    value: list[NBTValue]

    def __str__(self) -> str:
        return f"[{','.join(str(v) for v in self.value)}]"


@dataclass
class NBTCompound:
    value: dict[str, NBTValue]

    def __str__(self) -> str:
        pairs = []
        for k, v in self.value.items():
            key = NBTString(k).__str__()
            pairs.append(f"{key}:{v}")
        return "{" + ",".join(pairs) + "}"


# Union type for all NBT values
NBTValue = Union[
    NBTByte, NBTShort, NBTInt, NBTLong,
    NBTFloat, NBTDouble, NBTString,
    NBTByteArray, NBTIntArray, NBTLongArray,
    NBTList, NBTCompound
]


class SNBTParser:
    """SNBT parser with state management for recursive parsing."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def peek(self, n: int = 1) -> str:
        """Peek ahead n characters without consuming."""
        return self.text[self.pos:self.pos + n]

    def consume(self, n: int = 1) -> str:
        """Consume n characters and return them."""
        result = self.text[self.pos:self.pos + n]
        self.pos += n
        return result

    def skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def parse(self) -> NBTValue:
        """Parse the SNBT text into an NBT value."""
        self.skip_whitespace()
        if self.pos >= len(self.text):
            raise ValueError("Empty SNBT")

        char = self.peek()

        if char == '{':
            return self.parse_compound()
        elif char == '[':
            return self.parse_array_or_list()
        elif char == '"':
            return self.parse_quoted_string()
        elif char in '0123456789-':
            return self.parse_number()
        elif char.isalpha() or char == '_':
            return self.parse_unquoted_string()
        else:
            raise ValueError(f"Unexpected character at position {self.pos}: {char}")

    def parse_compound(self) -> NBTCompound:
        """Parse a compound like {key:value, key2:value2}."""
        self.consume()  # Consume {
        self.skip_whitespace()
        result = {}

        if self.peek() == '}':
            self.consume()  # Consume }
            return NBTCompound(result)

        while True:
            self.skip_whitespace()
            key = self.parse_string()
            self.skip_whitespace()

            if self.consume() != ':':
                raise ValueError("Expected : between key and value")

            value = self.parse()
            result[key.value] = value

            self.skip_whitespace()
            char = self.peek()
            if char == '}':
                self.consume()  # Consume }
                break
            elif char == ',':
                self.consume()  # Consume ,
                continue
            else:
                raise ValueError(f"Expected , or }} but got {char}")

        return NBTCompound(result)

    def parse_array_or_list(self) -> Union[NBTList, NBTByteArray, NBTIntArray, NBTLongArray]:
        """Parse array or list."""
        self.consume()  # Consume [
        self.skip_whitespace()

        # Check for typed array prefix
        if self.peek().isalpha() and self.peek(2) == ';':
            array_type = self.consume(1)
            self.consume()  # Consume ;

            values = []
            while True:
                self.skip_whitespace()
                if self.peek() == ']':
                    break
                values.append(self.parse())
                self.skip_whitespace()
                if self.peek() == ',':
                    self.consume()
                else:
                    break

            self.consume()  # Consume ]

            if array_type == 'B':
                return NBTByteArray([NBTByte(v.value) if isinstance(v, NBTInt) else v for v in values])
            elif array_type == 'I':
                return NBTIntArray([NBTInt(v.value) if isinstance(v, NBTInt) else v for v in values])
            elif array_type == 'L':
                return NBTLongArray([NBTLong(v.value) if isinstance(v, NBTInt) else v for v in values])
            else:
                raise ValueError(f"Unknown array type: {array_type}")

        # Regular list
        if self.peek() == ']':
            self.consume()
            return NBTList([])

        values = []
        while True:
            self.skip_whitespace()
            if self.peek() == ']':
                break
            values.append(self.parse())
            self.skip_whitespace()
            if self.peek() == ',':
                self.consume()
            else:
                break

        self.consume()  # Consume ]
        return NBTList(values)

    def parse_string(self) -> NBTString:
        """Parse either quoted or unquoted string."""
        self.skip_whitespace()
        if self.peek() == '"':
            return self.parse_quoted_string()
        return self.parse_unquoted_string()

    def parse_quoted_string(self) -> NBTString:
        """Parse a quoted string."""
        self.consume()  # Consume opening "
        value = ""
        while True:
            if self.pos >= len(self.text):
                raise ValueError("Unterminated string")
            char = self.consume()
            if char == '"':
                break
            if char == '\\':
                # Handle escape sequences
                if self.pos < len(self.text):
                    value += self.consume()
                else:
                    value += '\\'
            else:
                value += char
        return NBTString(value)

    def parse_unquoted_string(self) -> NBTString:
        """Parse an unquoted string (alphanumeric, underscore, plus, minus, dot)."""
        start = self.pos
        while self.pos < len(self.text):
            char = self.text[self.pos]
            if char.isalnum() or char in '_.+-':
                self.pos += 1
            else:
                break

        if start == self.pos:
            raise ValueError(f"No valid unquoted string at position {self.pos}")

        return NBTString(self.text[start:self.pos])

    def parse_number(self) -> NBTValue:
        """Parse a number with optional suffix."""
        start = self.pos
        has_decimal = False
        has_exponent = False

        # Handle negative sign
        if self.peek() == '-':
            self.consume()

        # Parse digits
        while self.pos < len(self.text):
            char = self.text[self.pos]
            if char.isdigit():
                self.pos += 1
            elif char == '.' and not has_decimal:
                has_decimal = True
                self.pos += 1
            elif char in 'eE' and not has_exponent:
                has_exponent = True
                self.pos += 1
                if self.peek() in '+-':
                    self.pos += 1
            else:
                break

        num_str = self.text[start:self.pos]
        self.skip_whitespace()

        # Check for suffix
        suffix = None
        if self.pos < len(self.text) and self.text[self.pos] in 'bslfd':
            suffix = self.text[self.pos]
            self.pos += 1

        value = float(num_str) if '.' in num_str or has_exponent else int(num_str)

        if suffix == 'b':
            return NBTByte(value)
        elif suffix == 's':
            return NBTShort(value)
        elif suffix == 'l' or suffix == 'L':
            return NBTLong(value)
        elif suffix == 'f':
            return NBTFloat(value)
        elif suffix == 'd':
            return NBTDouble(value)
        else:
            # Determine type by value
            if has_decimal or has_exponent:
                return NBTDouble(value)
            return NBTInt(value)

    def parse_unquoted_string_as_number(self) -> NBTValue:
        """Parse unquoted string but return it as a number if it looks like one."""
        result = self.parse_unquoted_string()
        # If it's just a number, return it as such
        try:
            value = int(result.value)
            return NBTInt(value)
        except ValueError:
            pass
        return result


def parse_snbt(snbt: str) -> NBTValue:
    """Parse SNBT string into an NBT value.

    Args:
        snbt: Stringified NBT in Minecraft format

    Returns:
        NBTValue: Parsed NBT structure

    Examples:
        >>> parse_snbt('{id:"minecraft:stone",Count:1b}')
        NBTCompound(value={'id': NBTString('minecraft:stone'), 'Count': NBTByte(1)})

        >>> parse_snbt('[1,2,3]')
        NBTList(value=[NBTInt(1), NBTInt(2), NBTInt(3)])

        >>> parse_snbt('123.5d')
        NBTDouble(123.5)
    """
    parser = SNBTParser(snbt.strip())
    return parser.parse()
