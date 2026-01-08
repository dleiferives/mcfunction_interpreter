"""Chat command parser for Minecraft commands.

This module provides parsers for chat-related commands:
- say: Broadcast message to all players
- tellraw: Send JSON message to specific players
"""

from __future__ import annotations

from mcfunction.parser.commands import Say, Tellraw
from mcfunction.parser.lexer import tokenize_compact


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
        # Skip the 'say' keyword if present
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == "say":
            self.pos += 1

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
        # Skip the 'tellraw' keyword if present
        if self.pos < len(self.tokens) and self.tokens[self.pos].value == "tellraw":
            self.pos += 1

        if self.pos >= len(self.tokens):
            raise ValueError("tellraw command requires targets")

        # First token after tellraw is the target selector/player
        targets = self.consume()

        if self.pos >= len(self.tokens):
            raise ValueError("tellraw command requires a message")

        # Collect all remaining tokens as the JSON message
        # We need to reconstruct JSON tokens carefully to preserve structure
        message_parts = []

        # Look ahead to reconstruct JSON properly
        remaining_tokens = self.tokens[self.pos:]

        # Use a simple algorithm: collect tokens and join with smart spacing
        for i, token in enumerate(remaining_tokens):
            token_value = token.value
            message_parts.append(token_value)
            self.pos += 1

        if not message_parts:
            raise ValueError("tellraw command requires a message")

        # Reconstruct message by joining tokens with minimal spacing
        # For compact JSON: no spaces unless needed for readability
        message = self._reconstruct_json_compact(message_parts)
        return Tellraw(targets=targets, message=message)

    def _reconstruct_json_compact(self, tokens: list[str]) -> str:
        """Reconstruct JSON from tokens in a compact format."""
        if not tokens:
            return ""

        result = []

        for i, token in enumerate(tokens):
            # QUOTED_STRING tokens already include their quotes
            if token.startswith('"') or token.startswith("'"):
                if i > 0 and tokens[i-1] not in ['{', '[', ':', ',']:
                    result.append(" ")
                result.append(token)
            elif token in ['{', '[']:
                # Start of object/array
                if i > 0 and tokens[i-1] not in ['{', '[', ':', ',']:
                    result.append(" ")
                result.append(token)
            elif token in ['}', ']']:
                # End of object/array
                result.append(token)
                # Add space before next if needed for readability
                if i < len(tokens) - 1 and tokens[i+1] not in ['}', ']', ',', ':']:
                    result.append(" ")
            elif token == ',':
                result.append(",")
                result.append(" ")
            elif token == ':':
                result.append(":")
            else:
                # Numbers, booleans, null, etc.
                if i > 0 and tokens[i-1] not in ['{', '[', ':', ',']:
                    result.append(" ")
                result.append(token)

        return "".join(result)


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
    # Tokenize and use the ChatParser for consistency
    tokens = tokenize_compact(command)
    parser = ChatParser(tokens)
    return parser.parse_tellraw()
