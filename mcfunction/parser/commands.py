"""Command AST nodes for Minecraft commands.

This file defines the data structures representing parsed Minecraft commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union, Optional, Any


# Scoreboard commands
@dataclass
class ScoreboardObjectivesAdd:
    objective: str
    criteria: str
    display_name: Optional[str] = None


@dataclass
class ScoreboardObjectivesRemove:
    objective: str


@dataclass
class ScoreboardObjectivesList:
    pass


@dataclass
class ScoreboardObjectivesSetDisplay:
    slot: str
    objective: Optional[str] = None


@dataclass
class ScoreboardPlayersSet:
    targets: str
    objective: str
    score: int


@dataclass
class ScoreboardPlayersAdd:
    targets: str
    objective: str
    score: int


@dataclass
class ScoreboardPlayersRemove:
    targets: str
    objective: str
    score: int


@dataclass
class ScoreboardPlayersReset:
    targets: str
    objective: Optional[str] = None


@dataclass
class ScoreboardPlayersOperation:
    targets: str
    target_objective: str
    operation: str
    source: str
    source_objective: str


# Data commands
@dataclass
class DataGet:
    target: str  # storage, entity, or block
    path: Optional[str] = None


@dataclass
class DataMerge:
    target: str
    nbt: Any  # NBTCompound


@dataclass
class DataModify:
    target: str
    path: str
    operation: str  # set, append, prepend, insert, merge
    source: Optional[str] = None  # source path or value
    index: Optional[int] = None  # for insert operation


@dataclass
class DataRemove:
    target: str
    path: str


# Function commands
@dataclass
class FunctionCall:
    function_path: str


# Execute commands
@dataclass
class ExecuteSubcommand:
    """Base class for execute subcommands."""
    type: str


@dataclass
class ExecuteAs(ExecuteSubcommand):
    selector: str


@dataclass
class ExecuteAt(ExecuteSubcommand):
    selector: str


@dataclass
class ExecuteIf(ExecuteSubcommand):
    condition_type: str
    condition_args: dict[str, Any]


@dataclass
class ExecuteUnless(ExecuteSubcommand):
    condition_type: str
    condition_args: dict[str, Any]


@dataclass
class ExecuteStore(ExecuteSubcommand):
    store_type: str  # 'result' or 'success'
    target: str
    path: Optional[str] = None


@dataclass
class Execute:
    subcommands: list[ExecuteSubcommand]
    command: Union[
        ScoreboardObjectivesAdd,
        ScoreboardObjectivesRemove,
        ScoreboardPlayersSet,
        ScoreboardPlayersAdd,
        ScoreboardPlayersRemove,
        ScoreboardPlayersOperation,
        DataGet,
        DataMerge,
        DataModify,
        DataRemove,
        FunctionCall,
        None  # For chain execution
    ]


# All command types
Command = Union[
    ScoreboardObjectivesAdd,
    ScoreboardObjectivesRemove,
    ScoreboardObjectivesList,
    ScoreboardObjectivesSetDisplay,
    ScoreboardPlayersSet,
    ScoreboardPlayersAdd,
    ScoreboardPlayersRemove,
    ScoreboardPlayersReset,
    ScoreboardPlayersOperation,
    DataGet,
    DataMerge,
    DataModify,
    DataRemove,
    FunctionCall,
    Execute,
]
