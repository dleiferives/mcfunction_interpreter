"""Scoreboard command parser for Minecraft commands.

This module provides parsers for all scoreboard subcommands, including:
- scoreboard objectives (add, remove, list, setdisplay)
- scoreboard players (set, add, remove, reset, operation)
"""

from __future__ import annotations

from typing import Optional

from mcfunction.parser.commands import (
    ScoreboardObjectivesAdd,
    ScoreboardObjectivesRemove,
    ScoreboardObjectivesList,
    ScoreboardObjectivesSetDisplay,
    ScoreboardPlayersSet,
    ScoreboardPlayersAdd,
    ScoreboardPlayersRemove,
    ScoreboardPlayersReset,
    ScoreboardPlayersOperation,
)
from mcfunction.parser.lexer import tokenize_compact, TokenType
from mcfunction.parser.selector import parse_selector


class ScoreboardParser:
    """Parser for scoreboard commands."""

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

    def parse_identifier(self) -> str:
        """Parse an identifier token (objective name, player name, etc.)."""
        token_type = self.peek_type()
        value = self.peek()

        if token_type in (TokenType.IDENTIFIER, TokenType.OBJECTIVE_NAME, TokenType.PLAYER_NAME, TokenType.KEYWORD):
            return self.consume()

        # Also accept resource locations as identifiers
        if token_type == TokenType.RESOURCE_LOCATION:
            return self.consume()

        raise ValueError(f"Expected identifier, got '{value}' (type: {token_type})")

    def parse_targets(self) -> str:
        """Parse targets (selector or player name)."""
        token_type = self.peek_type()
        value = self.peek()

        if token_type == TokenType.SELECTOR:
            # Validate selector syntax
            selector = self.consume()
            try:
                parse_selector(selector)  # Validate
            except ValueError as e:
                raise ValueError(f"Invalid selector: {e}")
            return selector
        elif token_type in (TokenType.IDENTIFIER, TokenType.PLAYER_NAME, TokenType.KEYWORD):
            return self.consume()
        else:
            raise ValueError(f"Expected selector or player name, got '{value}' (type: {token_type})")

    def parse_int(self) -> int:
        """Parse an integer token."""
        token_type = self.peek_type()
        value = self.peek()

        if token_type != TokenType.INTEGER:
            raise ValueError(f"Expected integer, got '{value}' (type: {token_type})")

        try:
            result = int(self.consume())
            return result
        except ValueError:
            raise ValueError(f"Invalid integer: '{value}'")

    def parse_operation(self) -> str:
        """Parse an operation operator.

        Supported operations: =, +=, -=, *=, /=, %=, ><, <, >
        """
        # Check for >< (swap operator)
        if self.peek() == ">" and self.peek(1) == "<":
            self.consume()
            self.consume()
            return "><"

        # Check for compound operators: +=, -=, *=, /=, %=
        if self.peek(1) == "=":
            op = self.peek()
            if op in ("+", "-", "*", "/", "%"):
                self.consume()
                self.consume()
                return f"{op}="

        # Check for single character operators: =, <, >
        if self.peek() == "=":
            self.consume()
            return "="
        if self.peek() == "<":
            self.consume()
            return "<"
        if self.peek() == ">":
            self.consume()
            return ">"

        raise ValueError(f"Invalid operation operator: '{self.peek()}'")


def parse_scoreboard_objectives_add(text: str) -> ScoreboardObjectivesAdd:
    """Parse: scoreboard objectives add <objective> <criteria> [display name]"""
    tokens = [t for t in tokenize_compact(text) if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]

    if len(tokens) < 4:
        raise ValueError("Too few tokens for objectives add")

    # Verify tokens are "scoreboard objectives add"
    if tokens[0].value != "scoreboard" or tokens[1].value != "objectives" or tokens[2].value != "add":
        raise ValueError("Not a scoreboard objectives add command")

    parser = ScoreboardParser(tokens[3:])

    objective = parser.parse_identifier()
    criteria = parser.parse_identifier()

    # Optional display name
    display_name = None
    if parser.pos < len(parser.tokens):
        # Display name can be quoted or unquoted identifier
        remaining = parser.peek()
        if remaining:
            display_name = remaining
            parser.consume()

    return ScoreboardObjectivesAdd(objective, criteria, display_name)


def parse_scoreboard_objectives_remove(text: str) -> ScoreboardObjectivesRemove:
    """Parse: scoreboard objectives remove <objective>"""
    tokens = [t for t in tokenize_compact(text) if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]

    if len(tokens) < 3:
        raise ValueError("Too few tokens for objectives remove")

    if tokens[0].value != "scoreboard" or tokens[1].value != "objectives" or tokens[2].value != "remove":
        raise ValueError("Not a scoreboard objectives remove command")

    parser = ScoreboardParser(tokens[3:])
    objective = parser.parse_identifier()

    return ScoreboardObjectivesRemove(objective)


def parse_scoreboard_objectives_list(text: str) -> ScoreboardObjectivesList:
    """Parse: scoreboard objectives list"""
    tokens = [t for t in tokenize_compact(text) if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]

    if len(tokens) < 2:
        raise ValueError("Too few tokens for objectives list")

    if tokens[0].value != "scoreboard" or tokens[1].value != "objectives" or len(tokens) != 3 or tokens[2].value != "list":
        raise ValueError("Not a scoreboard objectives list command")

    return ScoreboardObjectivesList()


def parse_scoreboard_objectives_setdisplay(text: str) -> ScoreboardObjectivesSetDisplay:
    """Parse: scoreboard objectives setdisplay <slot> [objective]"""
    tokens = [t for t in tokenize_compact(text) if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]

    if len(tokens) < 3:
        raise ValueError("Too few tokens for objectives setdisplay")

    if tokens[0].value != "scoreboard" or tokens[1].value != "objectives" or tokens[2].value != "setdisplay":
        raise ValueError("Not a scoreboard objectives setdisplay command")

    parser = ScoreboardParser(tokens[3:])

    slot = parser.parse_identifier()

    # Optional objective
    objective = None
    if parser.pos < len(parser.tokens):
        objective = parser.parse_identifier()

    return ScoreboardObjectivesSetDisplay(slot, objective)


def parse_scoreboard_players_set(text: str) -> ScoreboardPlayersSet:
    """Parse: scoreboard players set <targets> <objective> <score>"""
    tokens = [t for t in tokenize_compact(text) if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]

    if len(tokens) < 5:
        raise ValueError("Too few tokens for players set")

    if tokens[0].value != "scoreboard" or tokens[1].value != "players" or tokens[2].value != "set":
        raise ValueError("Not a scoreboard players set command")

    parser = ScoreboardParser(tokens[3:])

    targets = parser.parse_targets()
    objective = parser.parse_identifier()
    score = parser.parse_int()

    return ScoreboardPlayersSet(targets, objective, score)


def parse_scoreboard_players_add(text: str) -> ScoreboardPlayersAdd:
    """Parse: scoreboard players add <targets> <objective> <score>"""
    tokens = [t for t in tokenize_compact(text) if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]

    if len(tokens) < 5:
        raise ValueError("Too few tokens for players add")

    if tokens[0].value != "scoreboard" or tokens[1].value != "players" or tokens[2].value != "add":
        raise ValueError("Not a scoreboard players add command")

    parser = ScoreboardParser(tokens[3:])

    targets = parser.parse_targets()
    objective = parser.parse_identifier()
    score = parser.parse_int()

    return ScoreboardPlayersAdd(targets, objective, score)


def parse_scoreboard_players_remove(text: str) -> ScoreboardPlayersRemove:
    """Parse: scoreboard players remove <targets> <objective> <score>"""
    tokens = [t for t in tokenize_compact(text) if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]

    if len(tokens) < 5:
        raise ValueError("Too few tokens for players remove")

    if tokens[0].value != "scoreboard" or tokens[1].value != "players" or tokens[2].value != "remove":
        raise ValueError("Not a scoreboard players remove command")

    parser = ScoreboardParser(tokens[3:])

    targets = parser.parse_targets()
    objective = parser.parse_identifier()
    score = parser.parse_int()

    return ScoreboardPlayersRemove(targets, objective, score)


def parse_scoreboard_players_reset(text: str) -> ScoreboardPlayersReset:
    """Parse: scoreboard players reset <targets> [objective]"""
    tokens = [t for t in tokenize_compact(text) if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]

    if len(tokens) < 3:
        raise ValueError("Too few tokens for players reset")

    if tokens[0].value != "scoreboard" or tokens[1].value != "players" or tokens[2].value != "reset":
        raise ValueError("Not a scoreboard players reset command")

    parser = ScoreboardParser(tokens[3:])

    targets = parser.parse_targets()

    # Optional objective
    objective = None
    if parser.pos < len(parser.tokens):
        objective = parser.parse_identifier()

    return ScoreboardPlayersReset(targets, objective)


def parse_scoreboard_players_operation(text: str) -> ScoreboardPlayersOperation:
    """Parse: scoreboard players operation <targets> <targetObjective> <operation> <source> <sourceObjective>

    Supported operations: =, +=, -=, *=, /=, %=, ><, <, >
    """
    tokens = [t for t in tokenize_compact(text) if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]

    if len(tokens) < 6:
        raise ValueError("Too few tokens for players operation")

    if tokens[0].value != "scoreboard" or tokens[1].value != "players" or tokens[2].value != "operation":
        raise ValueError("Not a scoreboard players operation command")

    parser = ScoreboardParser(tokens[3:])

    targets = parser.parse_targets()
    target_objective = parser.parse_identifier()
    operation = parser.parse_operation()
    source = parser.parse_targets()
    source_objective = parser.parse_identifier()

    return ScoreboardPlayersOperation(
        targets,
        target_objective,
        operation,
        source,
        source_objective
    )
