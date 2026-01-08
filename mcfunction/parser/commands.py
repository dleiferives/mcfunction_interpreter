"""Command AST nodes for Minecraft commands.

This file defines the data structures representing parsed Minecraft commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union, Optional, Any

from mcfunction.parser.selector import EntitySelector
from mcfunction.parser.nbt import NBTValue


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
    nbt: NBTValue


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


@dataclass
class ExecuteAs(ExecuteSubcommand):
    selector: EntitySelector


@dataclass
class ExecuteAt(ExecuteSubcommand):
    selector: EntitySelector


@dataclass
class ExecuteAlign(ExecuteSubcommand):
    axes: str  # e.g., "xyz", "xy", "xz", etc.


@dataclass
class ExecuteAnchored(ExecuteSubcommand):
    anchor: str  # 'eyes' or 'feet'


@dataclass
class ExecuteFacing(ExecuteSubcommand):
    target: EntitySelector
    anchor: Optional[str] = None  # 'eyes' or 'feet'


@dataclass
class ExecuteIf(ExecuteSubcommand):
    condition_type: str
    condition_args: dict[str, Any]


@dataclass
class ExecuteUnless(ExecuteSubcommand):
    condition_type: str
    condition_args: dict[str, Any]


@dataclass
class ExecutePositioned(ExecuteSubcommand):
    selector: Optional[EntitySelector] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


@dataclass
class ExecuteRotated(ExecuteSubcommand):
    yaw: Optional[float] = None
    pitch: Optional[float] = None
    selector: Optional[EntitySelector] = None


@dataclass
class ExecuteStore(ExecuteSubcommand):
    store_type: str  # 'result' or 'success'
    target: str
    path: Optional[str] = None
    type: Optional[str] = None  # 'byte', 'short', 'int', 'long', 'float', 'double'
    scale: Optional[float] = None


@dataclass
class Execute:
    subcommands: list[ExecuteSubcommand]
    command: Union[
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
