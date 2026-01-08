"""Lexer for Minecraft function commands.

This module provides tokenization of Minecraft commands using a custom tokenizer.
Handles command keywords, resource locations, selectors, NBT paths, ranges, and more.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TokenType:
    """Token type constants."""

    # Command keywords
    KEYWORD = "KEYWORD"

    # Resource locations
    RESOURCE_LOCATION = "RESOURCE_LOCATION"

    # Selectors and identifiers
    SELECTOR = "SELECTOR"
    PLAYER_NAME = "PLAYER_NAME"
    OBJECTIVE_NAME = "OBJECTIVE_NAME"

    # Literals
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"

    # Coordinates and selectors
    COORDINATE_RELATIVE = "COORDINATE_RELATIVE"  # ~
    COORDINATE_LOCAL = "COORDINATE_LOCAL"        # ^

    # Ranges
    RANGE = "RANGE"

    # NBT
    NBT_PATH = "NBT_PATH"

    # Operators and punctuation
    EQUALS = "EQUALS"
    LESS = "LESS"
    GREATER = "GREATER"
    LESS_EQUALS = "LESS_EQUALS"
    GREATER_EQUALS = "GREATER_EQUALS"
    EQUALS_EQUALS = "EQUALS_EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    COMMA = "COMMA"
    COLON = "COLON"
    SEMICOLON = "SEMICOLON"
    DOT = "DOT"
    BRACKET_OPEN = "BRACKET_OPEN"
    BRACKET_CLOSE = "BRACKET_CLOSE"
    BRACE_OPEN = "BRACE_OPEN"
    BRACE_CLOSE = "BRACE_CLOSE"
    PAREN_OPEN = "PAREN_OPEN"
    PAREN_CLOSE = "PAREN_CLOSE"

    # Whitespace and special
    WHITESPACE = "WHITESPACE"
    COMMENT = "COMMENT"
    NEWLINE = "NEWLINE"
    CONTINUATION = "CONTINUATION"

    # Strings
    QUOTED_STRING = "QUOTED_STRING"

    # Identifiers
    IDENTIFIER = "IDENTIFIER"

    # Unknown
    UNKNOWN = "UNKNOWN"


@dataclass
class LexToken:
    """Represents a single token with type, value, and position."""

    type: str
    value: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"LexToken({self.type}, '{self.value}', line={self.line}, col={self.column})"


class Lexer:
    """Main lexer class for Minecraft commands."""

    def __init__(self) -> None:
        """Initialize the lexer."""
        # Command keywords sorted by length (longest first) for priority matching
        self.keywords = [
            "scoreboard", "function", "execute", "objectives", "players",
            "data", "merge", "modify", "remove", "add", "set", "reset",
            "operation", "as", "at", "if", "unless", "store", "run",
            "block", "entity", "storage", "bossbar", "team", "chat",
            "gamemode", "give", "effect", "enchant", "tp", "teleport",
            "summon", "kill", "setblock", "fill", "clone", "spreadplayers",
            "trigger", "tag", "attribute", "get", "list",
            # Execute subcommand keywords
            "align", "anchored", "facing", "in", "on", "positioned", "rotated",
        ]
        self.keywords.sort(key=len, reverse=True)

    def tokenize(self, text: str) -> list[LexToken]:
        """Tokenize Minecraft command text into tokens.

        Args:
            text: The Minecraft command text to tokenize

        Returns:
            List of LexToken objects
        """
        tokens: list[LexToken] = []
        lines = text.split("\n")

        for line_num, line in enumerate(lines, 1):
            pos = 0
            col = 1
            line_len = len(line)

            # Check for comment line
            if line.startswith("#"):
                tokens.append(LexToken(TokenType.COMMENT, line, line_num, 1))
                # Add newline if not the last line
                if line_num < len(lines):
                    tokens.append(LexToken(TokenType.NEWLINE, "\n", line_num, line_len + 1))
                continue

            # Handle line continuation (backslash at end)
            if line.rstrip().endswith("\\"):
                line = line.rstrip()[:-1]  # Remove backslash
                line_len = len(line)
                has_continuation = True
            else:
                has_continuation = False

            while pos < line_len:
                char = line[pos]
                remaining = line[pos:]

                # 1. Handle whitespace
                if char in " \t":
                    ws_end = pos
                    while ws_end < line_len and line[ws_end] in " \t":
                        ws_end += 1
                    tokens.append(LexToken(
                        TokenType.WHITESPACE,
                        line[pos:ws_end],
                        line_num, col
                    ))
                    col += ws_end - pos
                    pos = ws_end
                    continue

                # 2. Comments (mid-line)
                if char == "#":
                    tokens.append(LexToken(
                        TokenType.COMMENT,
                        remaining,
                        line_num, col
                    ))
                    break  # Rest of line is comment

                # 3. Selectors
                if char == "@":
                    selector_end = pos + 1
                    if selector_end < line_len and line[selector_end] in "apers":
                        selector_end += 1
                        # Check for arguments in brackets
                        if selector_end < line_len and line[selector_end] == "[":
                            bracket_count = 1
                            selector_end += 1
                            while selector_end < line_len and bracket_count > 0:
                                if line[selector_end] == "[":
                                    bracket_count += 1
                                elif line[selector_end] == "]":
                                    bracket_count -= 1
                                selector_end += 1
                        tokens.append(LexToken(
                            TokenType.SELECTOR,
                            line[pos:selector_end],
                            line_num, col
                        ))
                        col += selector_end - pos
                        pos = selector_end
                        continue
                    else:
                        # Just @ with no valid selector type
                        tokens.append(LexToken(TokenType.UNKNOWN, char, line_num, col))
                        pos += 1
                        col += 1
                        continue

                # 4. Coordinate indicators
                if char == "~":
                    coord_end = pos + 1
                    # Check for optional number
                    if coord_end < line_len:
                        if line[coord_end] in "+-":
                            coord_end += 1
                        num_start = coord_end
                        while coord_end < line_len and (line[coord_end].isdigit() or
                                                          line[coord_end] == "."):
                            coord_end += 1
                        if coord_end == num_start:  # No number, just ~
                            coord_end = pos + 1
                    tokens.append(LexToken(
                        TokenType.COORDINATE_RELATIVE,
                        line[pos:coord_end],
                        line_num, col
                    ))
                    col += coord_end - pos
                    pos = coord_end
                    continue

                if char == "^":
                    coord_end = pos + 1
                    # Check for optional number
                    if coord_end < line_len:
                        if line[coord_end] in "+-":
                            coord_end += 1
                        num_start = coord_end
                        while coord_end < line_len and (line[coord_end].isdigit() or
                                                          line[coord_end] == "."):
                            coord_end += 1
                        if coord_end == num_start:  # No number, just ^
                            coord_end = pos + 1
                    tokens.append(LexToken(
                        TokenType.COORDINATE_LOCAL,
                        line[pos:coord_end],
                        line_num, col
                    ))
                    col += coord_end - pos
                    pos = coord_end
                    continue

                # 5. Numbers with optional ranges (handle 5, 5.5, 5.., 5..10, 1e10)
                if char.isdigit() or (char == "-" and pos + 1 < line_len and
                                       line[pos + 1].isdigit()):
                    num_start = pos
                    if char == "-":
                        pos += 1
                        col += 1

                    # Parse the integer part
                    while pos < line_len and line[pos].isdigit():
                        pos += 1
                        col += 1

                    # Check what follows
                    if pos < line_len and line[pos] == ".":
                        # Check if this is a range or float
                        if pos + 1 < line_len and line[pos + 1] == ".":
                            # This is a range (e.g., 5..10)
                            range_start = pos
                            pos += 2  # skip ..
                            col += 2
                            # Parse number after ..
                            while pos < line_len and line[pos].isdigit():
                                pos += 1
                                col += 1
                            tokens.append(LexToken(
                                TokenType.RANGE,
                                line[num_start:pos],
                                line_num,
                                col - (pos - num_start)
                            ))
                            continue
                        else:
                            # This is a float (e.g., 5.5)
                            pos += 1
                            col += 1
                            while pos < line_len and line[pos].isdigit():
                                pos += 1
                                col += 1
                            # Check for exponent
                            if pos < line_len and line[pos] in "eE":
                                pos += 1
                                col += 1
                                if pos < line_len and line[pos] in "+-":
                                    pos += 1
                                    col += 1
                                while pos < line_len and line[pos].isdigit():
                                    pos += 1
                                    col += 1
                            tokens.append(LexToken(
                                TokenType.FLOAT,
                                line[num_start:pos],
                                line_num,
                                col - (pos - num_start)
                            ))
                            continue

                    elif pos < line_len and line[pos] in "eE":
                        # This is a number with exponent but no decimal (e.g., 1e10)
                        pos += 1
                        col += 1
                        if pos < line_len and line[pos] in "+-":
                            pos += 1
                            col += 1
                        # Exponent part
                        if pos < line_len and line[pos].isdigit():
                            while pos < line_len and line[pos].isdigit():
                                pos += 1
                                col += 1
                            tokens.append(LexToken(
                                TokenType.FLOAT,
                                line[num_start:pos],
                                line_num,
                                col - (pos - num_start)
                            ))
                            continue
                        else:
                            # Invalid exponent (e.g., 1e) - treat as integer
                            tokens.append(LexToken(
                                TokenType.INTEGER,
                                line[num_start:pos],
                                line_num,
                                col - (pos - num_start)
                            ))
                            continue

                    else:
                        # Just an integer
                        tokens.append(LexToken(
                            TokenType.INTEGER,
                            line[num_start:pos],
                            line_num,
                            col - (pos - num_start)
                        ))
                        continue

                # 6. Ranges starting without number (e.g., ..10, ..)
                if char == "." and pos + 1 < line_len and line[pos + 1] == ".":
                    range_start = pos
                    pos += 2  # skip ..
                    col += 2
                    # Parse number after ..
                    while pos < line_len and line[pos].isdigit():
                        pos += 1
                        col += 1
                    tokens.append(LexToken(
                        TokenType.RANGE,
                        line[range_start:pos],
                        line_num,
                        col - (pos - range_start)
                    ))
                    continue

                # 7. Floats starting with decimal point (e.g., .5)
                if char == "." and pos + 1 < line_len and line[pos + 1].isdigit():
                    num_start = pos
                    pos += 1
                    col += 1
                    while pos < line_len and line[pos].isdigit():
                        pos += 1
                        col += 1
                    # Check for exponent
                    if pos < line_len and line[pos] in "eE":
                        pos += 1
                        col += 1
                        if pos < line_len and line[pos] in "+-":
                            pos += 1
                            col += 1
                        while pos < line_len and line[pos].isdigit():
                            pos += 1
                            col += 1
                    tokens.append(LexToken(
                        TokenType.FLOAT,
                        line[num_start:pos],
                        line_num,
                        col - (pos - num_start)
                    ))
                    continue

                # 8. Single dot
                if char == ".":
                    tokens.append(LexToken(TokenType.DOT, char, line_num, col))
                    pos += 1
                    col += 1
                    continue

                # 9. Quoted strings
                if char in '"\'':
                    quote = char
                    str_start = pos
                    pos += 1  # Skip opening quote
                    escaped = False
                    while pos < line_len:
                        if escaped:
                            escaped = False
                        elif line[pos] == "\\":
                            escaped = True
                        elif line[pos] == quote:
                            pos += 1  # Include closing quote
                            break
                        pos += 1
                    tokens.append(LexToken(
                        TokenType.QUOTED_STRING,
                        line[str_start:pos],
                        line_num, col
                    ))
                    col += pos - str_start
                    continue

                # 10. Resource locations, NBT paths, and identifiers
                if char.isalpha() or char == "_":
                    # Look ahead for colon or brackets/dots
                    scan_pos = pos
                    has_colon = False
                    has_bracket = False
                    has_dot = False

                    while scan_pos < line_len:
                        c = line[scan_pos]
                        if c.isalnum() or c in "_-":
                            scan_pos += 1
                        elif c == ":":
                            has_colon = True
                            scan_pos += 1
                            # Continue with path part
                            while scan_pos < line_len and line[scan_pos] not in " \t\n,;=[](){}":
                                scan_pos += 1
                            break
                        elif c == ".":
                            has_dot = True
                            scan_pos += 1
                        elif c == "[":
                            has_bracket = True
                            # Handle bracket content
                            bracket_count = 1
                            scan_pos += 1
                            while scan_pos < line_len and bracket_count > 0:
                                if line[scan_pos] == "[":
                                    bracket_count += 1
                                elif line[scan_pos] == "]":
                                    bracket_count -= 1
                                scan_pos += 1
                        else:
                            break

                    # Determine token type based on content
                    value = line[pos:scan_pos]

                    if has_colon:
                        # Resource location
                        tokens.append(LexToken(
                            TokenType.RESOURCE_LOCATION,
                            value,
                            line_num, col
                        ))
                    elif has_bracket or has_dot:
                        # NBT path
                        tokens.append(LexToken(
                            TokenType.NBT_PATH,
                            value,
                            line_num, col
                        ))
                    else:
                        # Identifier or keyword
                        is_keyword = any(value == kw for kw in self.keywords)
                        token_type = TokenType.KEYWORD if is_keyword else TokenType.IDENTIFIER
                        tokens.append(LexToken(
                            token_type,
                            value,
                            line_num, col
                        ))

                    col += scan_pos - pos
                    pos = scan_pos
                    continue

                # 11. Operators
                if char == "=":
                    if pos + 1 < line_len and line[pos + 1] == "=":
                        tokens.append(LexToken(TokenType.EQUALS_EQUALS, "==", line_num, col))
                        pos += 2
                        col += 2
                    else:
                        tokens.append(LexToken(TokenType.EQUALS, "=", line_num, col))
                        pos += 1
                        col += 1
                    continue

                if char == "<":
                    if pos + 1 < line_len and line[pos + 1] == "=":
                        tokens.append(LexToken(TokenType.LESS_EQUALS, "<=", line_num, col))
                        pos += 2
                        col += 2
                    else:
                        tokens.append(LexToken(TokenType.LESS, "<", line_num, col))
                        pos += 1
                        col += 1
                    continue

                if char == ">":
                    if pos + 1 < line_len and line[pos + 1] == "=":
                        tokens.append(LexToken(TokenType.GREATER_EQUALS, ">=", line_num, col))
                        pos += 2
                        col += 2
                    else:
                        tokens.append(LexToken(TokenType.GREATER, ">", line_num, col))
                        pos += 1
                        col += 1
                    continue

                if char == "!" and pos + 1 < line_len and line[pos + 1] == "=":
                    tokens.append(LexToken(TokenType.NOT_EQUALS, "!=", line_num, col))
                    pos += 2
                    col += 2
                    continue

                # 12. Punctuation
                punct_map = {
                    ",": TokenType.COMMA,
                    ":": TokenType.COLON,
                    ";": TokenType.SEMICOLON,
                    "[": TokenType.BRACKET_OPEN,
                    "]": TokenType.BRACKET_CLOSE,
                    "{": TokenType.BRACE_OPEN,
                    "}": TokenType.BRACE_CLOSE,
                    "(": TokenType.PAREN_OPEN,
                    ")": TokenType.PAREN_CLOSE,
                    ".": TokenType.DOT,
                }
                if char in punct_map:
                    tokens.append(LexToken(punct_map[char], char, line_num, col))
                    pos += 1
                    col += 1
                    continue

                # 13. Unknown character
                tokens.append(LexToken(TokenType.UNKNOWN, char, line_num, col))
                pos += 1
                col += 1

            # Add continuation token if needed
            if has_continuation:
                tokens.append(LexToken(
                    TokenType.CONTINUATION,
                    "\\",
                    line_num, line_len + 1
                ))

            # Add newline at end of line (if there are more lines)
            if line_num < len(lines):
                tokens.append(LexToken(TokenType.NEWLINE, "\n", line_num, line_len + 1))

        return tokens


def tokenize(text: str) -> list[LexToken]:
    """Tokenize Minecraft command text.

    This is the main entry point for the lexer. It takes Minecraft command text
    and returns a list of tokens that can be used for parsing.

    Args:
        text: Minecraft command text (can be multiple lines)

    Returns:
        List of LexToken objects

    Examples:
        >>> from mcfunction.parser.lexer import tokenize
        >>> tokens = tokenize("scoreboard objectives add test dummy")
        >>> for token in tokens:
        ...     if token.type != "WHITESPACE":
        ...         print(f"{token.type}: {token.value}")
        KEYWORD: scoreboard
        KEYWORD: objectives
        KEYWORD: add
        IDENTIFIER: test
        IDENTIFIER: dummy

        >>> tokens = tokenize("@e[type=zombie,distance=..10]")
        >>> for token in tokens:
        ...     if token.type != "WHITESPACE":
        ...         print(f"{token.type}: {token.value}")
        SELECTOR: @e[type=zombie,distance=..10]

        >>> tokens = tokenize("minecraft:stone")
        >>> for token in tokens:
        ...     print(f"{token.type}: {token.value}")
        RESOURCE_LOCATION: minecraft:stone
    """
    lexer = Lexer()
    return lexer.tokenize(text)


def tokenize_compact(text: str) -> list[LexToken]:
    """Tokenize and filter out whitespace and comments.

    Args:
        text: Minecraft command text

    Returns:
        List of meaningful tokens only
    """
    all_tokens = tokenize(text)
    return [
        t for t in all_tokens
        if t.type not in (TokenType.WHITESPACE, TokenType.COMMENT, TokenType.NEWLINE)
    ]
