"""Chat command parser for Minecraft commands.

This module provides parsers for chat-related commands:
- say: Broadcast message to all players
- tellraw: Send JSON message to specific players
"""

from __future__ import annotations

from mcfunction.parser.commands import Say, Tellraw
from mcfunction.parser.lexer import tokenize_compact, TokenType


class ChatParser:
    """Parser for chat commands."""

    def __init__(self, tokens):
        """Initialize parser with token list."""
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset: int = 0) -> str | None:
        """Peek at token value at offset from current position."""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx].value
        return None

    def peek_type(self, offset: int = 0) -> str | None:
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

    def parse_say(self) -> Say:
        """Parse a say command.

        Format: say <message>

        Returns:
            Say AST node with message content

        Raises:
            ValueError: If message is missing
        """
        if self.pos >= len(self.tokens):
            raise ValueError("say command requires a message")

        # Collect all remaining tokens as the message
        message_parts = []
        while self.pos < len(self.tokens):
            message_parts.append(self.consume())

        if not message_parts:
            raise ValueError("say command requires a message")

        message = " ".join(message_parts)
        return Say(message=message)

    def parse_tellraw(self) -> Tellraw:
        """Parse a tellraw command.

        Format: tellraw <targets> <message>

        Returns:
            Tellraw AST node with targets and message

        Raises:
            ValueError: If targets or message is missing
        """
        if self.pos >= len(self.tokens):
            raise ValueError("tellraw command requires targets")

        # First token is the target selector/player
        targets = self.consume()

        if self.pos >= len(self.tokens):
            raise ValueError("tellraw command requires a message")

        # Collect all remaining tokens as the JSON message
        # We need to reconstruct JSON tokens carefully to preserve structure
        message_parts = []

        # Track brace/bracket depth for JSON
        brace_depth = 0
        bracket_depth = 0
        in_string = False
        escape_next = False

        # Look ahead to reconstruct JSON properly
        remaining_tokens = self.tokens[self.pos:]

        for i, token in enumerate(remaining_tokens):
            token_value = token.value

            # Simple JSON reconstruction
            # This handles the basic case where tokens represent JSON structure
            if not in_string:
                if token_value in '{':
                    brace_depth += 1
                elif token_value in '}':
                    brace_depth -= 1
                elif token_value in '[':
                    bracket_depth += 1
                elif token_value in ']':
                    bracket_depth -= 1
                elif token_value.startswith('"') or token_value.startswith("'"):
                    in_string = True

            if in_string and (token_value.endswith('"') or token_value.endswith("'")) and not token_value.startswith('\\'):
                in_string = False

            message_parts.append(token_value)

            # If we're back to zero depth and not in string, we could potentially stop
            # But to be safe, we'll consume all remaining tokens
            self.pos += 1

            # If we're not in a string and depths are zero, and next token isn't JSON-like,
            # we might want to stop, but let's just consume everything to be consistent

        if not message_parts:
            raise ValueError("tellraw command requires a message")

        # This is a simplified reconstruction - ideally we'd use the original string
        # But for now, joining with spaces is what we get from tokens
        message = " ".join(message_parts)
        return Tellraw(targets=targets, message=message)


def parse_say(command: str) -> Say:
    """Parse a say command from text.

    Args:
        command: The say command text (e.g., 'say Hello World!')

    Returns:
        Say AST node

    Raises:
        ValueError: If command syntax is invalid
    """
    # Simple approach: split on first space and take the rest as message
    parts = command.split(maxsplit=1)

    if len(parts) < 2:
        raise ValueError("say command requires a message")

    if parts[0] != "say":
        raise ValueError("Not a say command")

    message = parts[1]
    return Say(message=message)


def parse_tellraw(command: str) -> Tellraw:
    """Parse a tellraw command from text.

    Args:
        command: The tellraw command text (e.g., 'tellraw @a {"text":"Hello"}')

    Returns:
        Tellraw AST node

    Raises:
        ValueError: If command syntax is invalid
    """
    # First, validate by tokenizing
    tokens = [t for t in tokenize_compact(command) if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]

    if len(tokens) < 2:
        raise ValueError("tellraw command requires targets and message")
    if len(tokens) < 3:
        raise ValueError("tellraw command requires a message")

    if tokens[0].value != "tellraw":
        raise ValueError("Not a tellraw command")

    # Get the target selector/player from the token
    targets = tokens[1].value

    # Find the position after "tellraw" keyword in original command
    command_start = command.find("tellraw") + 7  # length of "tellraw"
    after_keyword = command[command_start:].lstrip()

    # Find the end of the target by looking for where it ends
    # This handles selectors like @a, @p[type=player], player names, etc.
    targets_end = 0
    bracket_depth = 0
    in_brackets = False

    for i, char in enumerate(after_keyword):
        if char == '[':
            in_brackets = True
            bracket_depth += 1
        elif char == ']':
            bracket_depth -= 1
            if bracket_depth == 0:
                in_brackets = False
        elif char in " \t":
            if not in_brackets:
                targets_end = i
                break
        elif i == 0:
            # First character of targets
            continue
        elif targets_end == 0:
            # We're still in the target specification
            continue

    # If we didn't find a space (single word targets), targets_end is 0
    # In that case, we need to find where the target ends
    if targets_end == 0:
        # Find first whitespace or non-target character
        for i, char in enumerate(after_keyword):
            if char in " \t{[\"":
                targets_end = i
                break
        if targets_end == 0:
            targets_end = len(after_keyword)  # Use full string if no delimiter found

    # Everything after the target is the message
    message = after_keyword[targets_end:].lstrip()

    if not message:
        raise ValueError("tellraw command requires a message")

    return Tellraw(targets=targets, message=message)
