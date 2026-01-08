"""Command and data structure parsing for Minecraft mcfunction syntax."""

from mcfunction.parser.commands import (
    Command,
    Execute,
    ExecuteSubcommand,
    ExecuteAs,
    ExecuteAt,
    ExecuteAlign,
    ExecuteAnchored,
    ExecuteFacing,
    ExecuteIf,
    ExecuteUnless,
    ExecutePositioned,
    ExecuteRotated,
    ExecuteStore,
    ExecuteIn,
    ExecuteOn,
    ExecuteSummon,
    FunctionCall,
    Say,
    Tellraw,
)
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
from mcfunction.parser.data import (
    parse_data_get,
    parse_data_merge,
    parse_data_modify,
    parse_data_remove,
    parse_data_command,
)
from mcfunction.parser.function_execute import (
    parse_function_call,
    parse_execute,
    parse_command_from_tokens,
)
from mcfunction.parser.chat import (
    parse_say,
    parse_tellraw,
)
from mcfunction.datapack import (
    DataPack,
    load_datapack,
    FunctionTag,
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
    "parse_data_get",
    "parse_data_merge",
    "parse_data_modify",
    "parse_data_remove",
    "parse_data_command",
    "parse_function_call",
    "parse_execute",
    "parse_command_from_tokens",
    # Execute command types
    "Execute",
    "ExecuteSubcommand",
    "ExecuteAs",
    "ExecuteAt",
    "ExecuteAlign",
    "ExecuteAnchored",
    "ExecuteFacing",
    "ExecuteIf",
    "ExecuteUnless",
    "ExecutePositioned",
    "ExecuteRotated",
    "ExecuteStore",
    "ExecuteIn",
    "ExecuteOn",
    "ExecuteSummon",
    "FunctionCall",
    # Chat command types
    "Say",
    "Tellraw",
    # Chat command parsers
    "parse_say",
    "parse_tellraw",
    # Datapack types
    "DataPack",
    "load_datapack",
    "FunctionTag",
]
