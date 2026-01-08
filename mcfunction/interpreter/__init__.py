"""Minecraft function execution and state management."""

from __future__ import annotations

from mcfunction.interpreter.builtins.data import (
    exec_data_get,
    exec_data_merge,
    exec_data_modify,
    exec_data_remove,
)
from mcfunction.interpreter.builtins.scoreboard import (
    exec_scoreboard_objectives_add,
    exec_scoreboard_objectives_list,
    exec_scoreboard_objectives_remove,
    exec_scoreboard_objectives_setdisplay,
    exec_scoreboard_players_add,
    exec_scoreboard_players_operation,
    exec_scoreboard_players_remove,
    exec_scoreboard_players_reset,
    exec_scoreboard_players_set,
)
from mcfunction.interpreter.context import ExecutionContext
from mcfunction.interpreter.executor import (
    FunctionRegistry,
    Interpreter,
    execute_command,
    execute_function,
)
from mcfunction.interpreter.state import GameState

__all__ = [
    "GameState",
    "ExecutionContext",
    "execute_command",
    "execute_function",
    "Interpreter",
    "FunctionRegistry",
    "exec_scoreboard_objectives_add",
    "exec_scoreboard_objectives_remove",
    "exec_scoreboard_objectives_list",
    "exec_scoreboard_objectives_setdisplay",
    "exec_scoreboard_players_set",
    "exec_scoreboard_players_add",
    "exec_scoreboard_players_remove",
    "exec_scoreboard_players_reset",
    "exec_scoreboard_players_operation",
    "exec_data_get",
    "exec_data_merge",
    "exec_data_modify",
    "exec_data_remove",
]
