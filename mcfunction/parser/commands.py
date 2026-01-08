"""Command AST nodes for Minecraft commands.

This file defines the data structures representing parsed Minecraft commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mcfunction.parser.nbt import NBTValue
from mcfunction.parser.selector import EntitySelector


# Scoreboard commands
@dataclass
class ScoreboardObjectivesAdd:
    objective: str
    criteria: str
    display_name: str | None = None


@dataclass
class ScoreboardObjectivesRemove:
    objective: str


@dataclass
class ScoreboardObjectivesList:
    pass


@dataclass
class ScoreboardObjectivesSetDisplay:
    slot: str
    objective: str | None = None


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
    objective: str | None = None


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
    path: str | None = None


@dataclass
class DataMerge:
    target: str
    nbt: NBTValue


@dataclass
class DataModify:
    target: str
    path: str
    operation: str  # set, append, prepend, insert, merge
    source: str | None = None  # source path
    value: NBTValue | None = None  # NBT value for value operations
    index: int | None = None  # for insert operation


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
    target: EntitySelector | None = None  # When facing a selector
    anchor: str | None = None  # 'eyes' or 'feet'
    x: float | None = None  # When facing coordinates
    y: float | None = None
    z: float | None = None


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
    selector: EntitySelector | None = None
    x: float | None = None
    y: float | None = None
    z: float | None = None


@dataclass
class ExecuteRotated(ExecuteSubcommand):
    yaw: float | None = None
    pitch: float | None = None
    selector: EntitySelector | None = None


@dataclass
class ExecuteStore(ExecuteSubcommand):
    store_type: str  # 'result' or 'success'
    target: str
    path: str | None = None
    type: str | None = None  # 'byte', 'short', 'int', 'long', 'float', 'double'
    scale: float | None = None


@dataclass
class ExecuteIn(ExecuteSubcommand):
    dimension: str  # 'overworld', 'the_nether', 'the_end'


@dataclass
class ExecuteOn(ExecuteSubcommand):
    target: str  # 'block', 'entity', 'bossbar', 'storage', 'players'


@dataclass
class ExecuteSummon(ExecuteSubcommand):
    entity: str  # Entity type to summon


@dataclass
class Execute:
    subcommands: list[ExecuteSubcommand]
    command: (
        ScoreboardObjectivesAdd
        | ScoreboardObjectivesRemove
        | ScoreboardObjectivesList
        | ScoreboardObjectivesSetDisplay
        | ScoreboardPlayersSet
        | ScoreboardPlayersAdd
        | ScoreboardPlayersRemove
        | ScoreboardPlayersReset
        | ScoreboardPlayersOperation
        | DataGet
        | DataMerge
        | DataModify
        | DataRemove
        | FunctionCall
        | Execute
        | None
    )


# All command types
Command = (
    ScoreboardObjectivesAdd
    | ScoreboardObjectivesRemove
    | ScoreboardObjectivesList
    | ScoreboardObjectivesSetDisplay
    | ScoreboardPlayersSet
    | ScoreboardPlayersAdd
    | ScoreboardPlayersRemove
    | ScoreboardPlayersReset
    | ScoreboardPlayersOperation
    | DataGet
    | DataMerge
    | DataModify
    | DataRemove
    | FunctionCall
    | Execute
)
