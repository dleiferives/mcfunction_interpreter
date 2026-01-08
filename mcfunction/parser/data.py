"""Data command parser for Minecraft commands.

This module provides parsers for data subcommands, including:
- data get
- data merge
- data modify
- data remove
"""

from __future__ import annotations

from typing import Optional, Union

from mcfunction.parser.commands import (
    DataGet,
    DataMerge,
    DataModify,
    DataRemove,
)
from mcfunction.parser.lexer import tokenize_compact, TokenType
from mcfunction.parser.nbt import parse_snbt, NBTValue, NBTCompound
from mcfunction.parser.selector import parse_selector


class DataParser:
    """Parser for data commands."""

    def __init__(self, tokens):
        """Initialize parser with token list."""
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset: int = 0) -> Optional[str]:
        """Peek at token value at offset from current position."""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx].value
        return None

    def peek_type(self, offset: int = 0) -> Optional[str]:
        """Peek at token type at offset from current position."""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx].type
        return None

    def consume(self) -> str:
        """Consume and return current token value."""
        if self.pos < len(self.tokens):
            val = self.tokens[self.pos].value
            self.pos += 1
            return val
        raise ValueError("Unexpected end of tokens")

    def consume_if(self, expected_value: str) -> bool:
        """Consume token if it matches expected value, return True if consumed."""
        if self.peek() == expected_value:
            self.consume()
            return True
        return False

    def expect(self, expected_value: str) -> str:
        """Expect and consume a specific token value."""
        if self.peek() != expected_value:
            raise ValueError(f"Expected '{expected_value}', got '{self.peek()}'")
        return self.consume()

    def parse_location(self) -> str:
        """Parse a data location like 'storage minecraft:global', 'entity @s', 'block 1 2 3'."""
        location_type = self.consume()

        if location_type == "storage":
            storage_path = self.consume()
            return f"storage {storage_path}"

        elif location_type == "entity":
            selector_token = self.peek()
            if selector_token and selector_token.startswith("@"):
                selector = self.consume()
                try:
                    parse_selector(selector)
                except ValueError as e:
                    raise ValueError(f"Invalid selector in data command: {e}")
                return f"entity {selector}"
            else:
                raise ValueError("Expected selector after 'entity' in data command")

        elif location_type == "block":
            x = self.consume()
            y = self.consume()
            z = self.consume()

            for coord in [x, y, z]:
                if coord in ("~", "^"):
                    continue
                if coord.startswith("~") or coord.startswith("^"):
                    coord_val = coord[1:]
                    if coord_val:
                        try:
                            float(coord_val)
                        except ValueError:
                            raise ValueError(f"Invalid coordinate: '{coord}'")
                else:
                    try:
                        float(coord)
                    except ValueError:
                        raise ValueError(f"Invalid coordinate: '{coord}'")

            return f"block {x} {y} {z}"

        else:
            raise ValueError(f"Unknown location type '{location_type}'. Expected 'storage', 'entity', or 'block'")

    def parse_nbt_path(self) -> str:
        """Parse an NBT path like 'data', 'Inventory[0]', 'tag.Value'."""
        path_tokens = []

        while self.pos < len(self.tokens):
            token = self.peek()
            token_type = self.peek_type()

            if token_type in (TokenType.COORDINATE_RELATIVE, TokenType.COORDINATE_LOCAL):
                break

            if token in ["set", "merge", "append", "prepend", "insert", "remove", "get", "modify"]:
                break

            if token_type in (TokenType.IDENTIFIER, TokenType.KEYWORD, TokenType.NBT_PATH,
                             TokenType.RESOURCE_LOCATION, TokenType.DOT,
                             TokenType.BRACKET_OPEN, TokenType.BRACKET_CLOSE,
                             TokenType.INTEGER):
                path_tokens.append(self.consume())
            else:
                break

        if not path_tokens:
            raise ValueError("Expected NBT path")

        return "".join(path_tokens)

    def parse_nbt_value(self) -> NBTValue:
        """Parse an NBT value from tokens."""
        remaining_tokens = self.tokens[self.pos:]
        nbt_string = "".join(token.value for token in remaining_tokens)

        if not nbt_string:
            raise ValueError("Expected NBT value")

        try:
            result = parse_snbt(nbt_string)
            self.pos = len(self.tokens)
            return result
        except ValueError as e:
            raise ValueError(f"Invalid NBT syntax: {e}")

    def parse_modify_operation(self) -> str:
        """Parse the modify operation (append, insert, merge, prepend, set)."""
        op = self.consume()
        valid_ops = {"append", "insert", "merge", "prepend", "set"}
        if op not in valid_ops:
            raise ValueError(f"Invalid operation '{op}'. Expected one of: {valid_ops}")
        return op

    def _parse_data_source(self) -> str:
        """Parse a data source for 'from' operations.

        Parses a source in the format:
        - storage <namespace:path> [nbt_path]
        - entity <selector> [nbt_path]
        - block <x> <y> <z> [nbt_path]

        Returns the combined source as a string.
        """
        source_location = self.parse_location()

        if self.pos < len(self.tokens):
            try:
                source_path = self.parse_nbt_path()
                return f"{source_location} {source_path}"
            except ValueError:
                return source_location
        else:
            return source_location


def parse_data_get(location: str, path: str | None) -> DataGet:
    """Parse data get command.

    Args:
        location: The target location (e.g., 'storage minecraft:global', 'entity @s', 'block 1 2 3')
        path: Optional NBT path

    Returns:
        DataGet AST node

    Examples:
        >>> parse_data_get("storage minecraft:global", "data")
        DataGet(target='storage minecraft:global', path='data')

        >>> parse_data_get("entity @s", None)
        DataGet(target='entity @s', path=None)
    """
    return DataGet(target=location, path=path)


def parse_data_merge(location: str, nbt: NBTCompound) -> DataMerge:
    """Parse data merge command.

    Args:
        location: The target location (e.g., 'storage minecraft:global', 'entity @s', 'block 1 2 3')
        nbt: NBT compound to merge

    Returns:
        DataMerge AST node

    Examples:
        >>> from mcfunction.parser.nbt import parse_snbt
        >>> nbt = parse_snbt("{value:10}")
        >>> parse_data_merge("storage minecraft:global", nbt)
        DataMerge(target='storage minecraft:global', nbt=NBTCompound(...))
    """
    return DataMerge(target=location, nbt=nbt)


def parse_data_modify(location: str, path: str, op: str, target_path: str | None, value: NBTValue) -> DataModify:
    """Parse data modify command.

    Args:
        location: The target location (e.g., 'storage minecraft:global', 'entity @s', 'block 1 2 3')
        path: NBT path to modify
        operation: Operation type ('append', 'insert', 'merge', 'prepend', 'set')
        source: Source path (for insert operations) or None for value operations
        value: NBT value to use

    Returns:
        DataModify AST node

    Examples:
        >>> from mcfunction.parser.nbt import parse_snbt
        >>> value = parse_snbt("10")
        >>> parse_data_modify("entity @s", "Health", "set", None, value)
        DataModify(target='entity @s', path='Health', operation='set', source=None, ...)
    """
    return DataModify(
        target=location,
        path=path,
        operation=op,
        source=target_path,
        value=value
    )


def parse_data_remove(location: str, path: str) -> DataRemove:
    """Parse data remove command.

    Args:
        location: The target location (e.g., 'storage minecraft:global', 'entity @s', 'block 1 2 3')
        path: NBT path to remove

    Returns:
        DataRemove AST node

    Examples:
        >>> parse_data_remove("entity @s", "PersistenceRequired")
        DataRemove(target='entity @s', path='PersistenceRequired')
    """
    return DataRemove(target=location, path=path)


def parse_data_command(text: str) -> Union[DataGet, DataMerge, DataModify, DataRemove]:
    """Parse a data command from text.

    Args:
        text: The data command text (e.g., 'data get entity @s Health')

    Returns:
        Appropriate Data AST node

    Examples:
        >>> parse_data_command("data get entity @s Health")
        DataGet(target='entity @s', path='Health')

        >>> parse_data_command("data merge storage minecraft:global {value:10}")
        DataMerge(target='storage minecraft:global', nbt=...)

        >>> parse_data_command("data modify entity @s Health set value 20")
        DataModify(target='entity @s', path='Health', operation='set', ...)
    """
    tokens = [t for t in tokenize_compact(text) if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]

    if len(tokens) < 3:
        raise ValueError("Too few tokens for data command")

    # Verify starts with "data"
    if tokens[0].value != "data":
        raise ValueError("Not a data command")

    subcommand = tokens[1].value

    if subcommand == "get":
        return _parse_data_get_command(tokens[2:])
    elif subcommand == "merge":
        return _parse_data_merge_command(tokens[2:])
    elif subcommand == "modify":
        return _parse_data_modify_command(tokens[2:])
    elif subcommand == "remove":
        return _parse_data_remove_command(tokens[2:])
    else:
        raise ValueError(f"Unknown data subcommand: {subcommand}")


def _parse_data_get_command(tokens) -> DataGet:
    """Internal: parse data get command tokens."""
    parser = DataParser(tokens)
    location = parser.parse_location()
    path = None
    if parser.pos < len(parser.tokens):
        path = parser.parse_nbt_path()
    return parse_data_get(location, path)


def _parse_data_merge_command(tokens) -> DataMerge:
    """Internal: parse data merge command tokens."""
    parser = DataParser(tokens)
    location = parser.parse_location()
    nbt = parser.parse_nbt_value()
    if not isinstance(nbt, NBTCompound):
        raise ValueError("data merge requires an NBT compound")
    return parse_data_merge(location, nbt)


def _parse_data_modify_command(tokens) -> DataModify:
    """Internal: parse data modify command tokens."""
    parser = DataParser(tokens)
    location = parser.parse_location()
    path = parser.parse_nbt_path()
    operation = parser.parse_modify_operation()

    if operation == "insert":
        if parser.pos >= len(parser.tokens):
            raise ValueError("insert requires an index")

        index_token = parser.consume()
        try:
            index = int(index_token)
        except ValueError:
            raise ValueError(f"insert index must be an integer, got '{index_token}'")

        if parser.consume_if("from"):
            source = parser._parse_data_source()
            return DataModify(
                target=location,
                path=path,
                operation=operation,
                source=source,
                index=index
            )
        else:
            raise ValueError("insert requires 'from' keyword")

    elif operation in {"append", "prepend"}:
        if parser.consume_if("from"):
            source = parser._parse_data_source()
            return DataModify(
                target=location,
                path=path,
                operation=operation,
                source=source
            )
        elif parser.consume_if("value"):
            value = parser.parse_nbt_value()
            return DataModify(
                target=location,
                path=path,
                operation=operation,
                value=value
            )
        else:
            raise ValueError(f"{operation} requires 'from' or 'value'")

    elif operation in {"merge", "set"}:
        if parser.consume_if("value"):
            value = parser.parse_nbt_value()
            return DataModify(
                target=location,
                path=path,
                operation=operation,
                value=value
            )
        elif parser.consume_if("from"):
            source = parser._parse_data_source()
            return DataModify(
                target=location,
                path=path,
                operation=operation,
                source=source
            )
        else:
            raise ValueError(f"{operation} requires 'value' or 'from'")

    else:
        raise ValueError(f"Unknown operation: {operation}")


def _parse_data_remove_command(tokens) -> DataRemove:
    """Internal: parse data remove command tokens."""
    parser = DataParser(tokens)
    location = parser.parse_location()
    path = parser.parse_nbt_path()
    return parse_data_remove(location, path)
