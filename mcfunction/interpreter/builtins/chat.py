"""Chat command executor for Minecraft interpreter.

This module provides executor functions for chat-related commands:
- say: Broadcast message to all players
- tellraw: Send JSON message to specific players
"""

from __future__ import annotations

from mcfunction.interpreter.state import GameState
from mcfunction.interpreter.builtins.scoreboard import resolve_targets


def exec_say(state: GameState, message: str) -> None:
    """Execute a say command.

    Broadcasts a message to all players in the game.
    In a real implementation, this would post to chat.
    For this interpreter, we log to output.

    Args:
        state: The current game state
        message: The message to broadcast
    """
    # In a real MC server, this would broadcast to all players
    # For the interpreter, we log the action
    print(f"[SAY] {message}")


def exec_tellraw(state: GameState, targets: str, message: str) -> None:
    """Execute a tellraw command.

    Sends a JSON message to specific players.
    In a real implementation, this would send to targeted players.
    For this interpreter, we log to output.

    Args:
        state: The current game state
        targets: Player selector or name
        message: JSON message payload
    """
    resolved = resolve_targets(state, targets)
    # In a real MC server, this would send to specific players
    # For the interpreter, we log the action
    for player in resolved:
        print(f"[TELLRAW -> {player}] {message}")
