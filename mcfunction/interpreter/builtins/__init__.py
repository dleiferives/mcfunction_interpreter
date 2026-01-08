"""Built-in command executors for Minecraft interpreter."""

from __future__ import annotations

from .scoreboard import (
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

__all__ = [
    "exec_scoreboard_objectives_add",
    "exec_scoreboard_objectives_remove",
    "exec_scoreboard_objectives_list",
    "exec_scoreboard_objectives_setdisplay",
    "exec_scoreboard_players_set",
    "exec_scoreboard_players_add",
    "exec_scoreboard_players_remove",
    "exec_scoreboard_players_reset",
    "exec_scoreboard_players_operation",
]
