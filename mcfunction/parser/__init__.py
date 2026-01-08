"""Command and data structure parsing for Minecraft mcfunction syntax."""

from mcfunction.parser.commands import Command
from mcfunction.parser.lexer import Lexer, LexToken, TokenType, tokenize, tokenize_compact
from mcfunction.parser.nbt import parse_snbt
from mcfunction.parser.scoreboard import (
    parse_scoreboard_objectives_add,
    parse_scoreboard_objectives_remove,
    parse_scoreboard_objectives_list,
    parse_scoreboard_objectives_setdisplay,
    parse_scoreboard_players_set,
    parse_scoreboard_players_add,
    parse_scoreboard_players_remove,
    parse_scoreboard_players_reset,
    parse_scoreboard_players_operation,
)
from mcfunction.parser.selector import (
    EntitySelector,
    Range,
    ScoreMatcher,
    SelectorArgValue,
    parse_selector,
)

__all__ = [
    "parse_snbt",
    "parse_selector",
    "EntitySelector",
    "Range",
    "ScoreMatcher",
    "SelectorArgValue",
    "Command",
    "Lexer",
    "LexToken",
    "TokenType",
    "tokenize",
    "tokenize_compact",
    "parse_scoreboard_objectives_add",
    "parse_scoreboard_objectives_remove",
    "parse_scoreboard_objectives_list",
    "parse_scoreboard_objectives_setdisplay",
    "parse_scoreboard_players_set",
    "parse_scoreboard_players_add",
    "parse_scoreboard_players_remove",
    "parse_scoreboard_players_reset",
    "parse_scoreboard_players_operation",
]
