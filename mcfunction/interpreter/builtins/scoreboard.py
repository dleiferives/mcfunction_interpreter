"""Scoreboard operations executor for Minecraft interpreter.

This module provides executor functions for all scoreboard commands.
"""

from __future__ import annotations

from mcfunction.interpreter.state import GameState


def resolve_targets(state: GameState, targets: str) -> list[str]:
    """Resolve entity selector or player name to a list of player names.

    In a real Minecraft implementation, this would query the actual entities.
    For this interpreter, we:
    - Treat direct player names as-is
    - Treat @s as the "executor" (we'll use a placeholder)
    - Treat @a, @e, @p, @r as requiring player context (we'll resolve to available players)

    Args:
        state: The current game state (for context)
        targets: Entity selector string or player name

    Returns:
        List of player names
    """
    # Direct player name
    if not targets.startswith("@"):
        return [targets]

    # Parse selector
    from mcfunction.parser.selector import parse_selector
    try:
        selector = parse_selector(targets)
    except ValueError:
        # If parsing fails, treat as literal
        return [targets]

    # Get available players from state
    available_players = list(state.players)

    # For @s, we need a way to know the current executor
    # For this interpreter, we'll use the first player or a placeholder
    if selector.selector_type == "s":
        if available_players:
            return [available_players[0]]
        return ["@s"]

    # For @a - all players
    if selector.selector_type == "a":
        return available_players if available_players else ["@a"]

    # For @e - all entities (players in this simplified interpreter)
    if selector.selector_type == "e":
        return available_players if available_players else ["@e"]

    # For @p - nearest player (first in list for simplicity)
    if selector.selector_type == "p":
        if available_players:
            return [available_players[0]]
        return ["@p"]

    # For @r - random player (random from list or first)
    if selector.selector_type == "r":
        if available_players:
            import random
            return [random.choice(available_players)]
        return ["@r"]

    return [targets]


def exec_scoreboard_objectives_add(
    state: GameState, name: str, criteria: str, display: str | None = None
) -> None:
    """Add a new scoreboard objective.

    Args:
        state: The game state
        name: Objective name
        criteria: The criteria for the objective (e.g., "dummy")
        display: Optional display name
    """
    state.add_objective(name, criteria, display)


def exec_scoreboard_objectives_remove(
    state: GameState, name: str
) -> None:
    """Remove a scoreboard objective.

    Args:
        state: The game state
        name: Objective name to remove
    """
    state.scoreboards.remove_objective(name)


def exec_scoreboard_objectives_list(
    state: GameState
) -> None:
    """List all scoreboard objectives.

    Args:
        state: The game state
    """
    objectives = state.scoreboards.objectives
    if not objectives:
        print("There are no scoreboard objectives registered")
        return

    print("Objective list:")
    for name, (criteria, display) in objectives.items():
        if display:
            print(f"  - {name}: {criteria} (display: {display})")
        else:
            print(f"  - {name}: {criteria}")


def exec_scoreboard_objectives_setdisplay(
    state: GameState, slot: str, objective: str | None
) -> None:
    """Set or clear a display slot.

    Args:
        state: The game state
        slot: Display slot name (e.g., "sidebar", "belowName", "list")
        objective: Objective name to display, or None to clear
    """
    state.set_display(slot, objective)


def exec_scoreboard_players_set(
    state: GameState, targets: str, objective: str, score: int
) -> None:
    """Set player scores.

    Args:
        state: The game state
        targets: Entity selector or player name
        objective: Objective name
        score: Score value
    """
    players = resolve_targets(state, targets)
    for player in players:
        state.set_score(player, objective, score)


def exec_scoreboard_players_add(
    state: GameState, targets: str, objective: str, score: int
) -> None:
    """Add to player scores.

    Args:
        state: The game state
        targets: Entity selector or player name
        objective: Objective name
        score: Amount to add
    """
    players = resolve_targets(state, targets)
    for player in players:
        state.scoreboards.add_score(player, objective, score)


def exec_scoreboard_players_remove(
    state: GameState, targets: str, objective: str, score: int
) -> None:
    """Remove from player scores.

    Args:
        state: The game state
        targets: Entity selector or player name
        objective: Objective name
        score: Amount to remove
    """
    players = resolve_targets(state, targets)
    for player in players:
        state.scoreboards.remove_score(player, objective, score)


def exec_scoreboard_players_reset(
    state: GameState, targets: str, objective: str | None = None
) -> None:
    """Reset player scores.

    Args:
        state: The game state
        targets: Entity selector or player name
        objective: Optional specific objective to reset, or None for all
    """
    players = resolve_targets(state, targets)
    for player in players:
        state.scoreboards.reset_scores(player, objective)


def exec_scoreboard_players_operation(
    state: GameState, targets: str, target_obj: str, op: str,
    source: str, source_obj: str
) -> None:
    """Perform operation between scores.

    Args:
        state: The game state
        targets: Target entity selector or player name
        target_obj: Target objective
        op: Operation (=, +=, -=, *=, /=, %=, ><, <, >)
        source: Source entity selector or player name
        source_obj: Source objective

    Supported operations:
        = : Assign source to target
        += : Add source to target
        -= : Subtract source from target
        *= : Multiply target by source
        /= : Divide target by source
        %= : Modulo target by source
        >< : Swap target and source
        < : Min target with source
        > : Max target with source
    """
    target_players = resolve_targets(state, targets)
    source_players = resolve_targets(state, source)

    # For operations, we typically operate on the first target and first source
    # unless it's swap (<>) which affects all combinations
    if not target_players or not source_players:
        return

    if op == "><":
        # Swap operation - needs to work with pairs
        # For simplicity, swap between first of each
        target = target_players[0]
        source_p = source_players[0]

        target_score = state.get_score(target, target_obj)
        source_score = state.get_score(source_p, source_obj)

        state.set_score(target, target_obj, source_score)
        state.set_score(source_p, source_obj, target_score)
        return

    # For all other operations, iterate through target players
    for target in target_players:
        target_score = state.get_score(target, target_obj)
        source_score = state.get_score(source_players[0], source_obj)

        if op == "=":
            state.set_score(target, target_obj, source_score)
        elif op == "+=":
            state.set_score(target, target_obj, target_score + source_score)
        elif op == "-=":
            state.set_score(target, target_obj, target_score - source_score)
        elif op == "*=":
            state.set_score(target, target_obj, target_score * source_score)
        elif op == "/=":
            if source_score == 0:
                state.set_score(target, target_obj, 0)
            else:
                state.set_score(target, target_obj, target_score // source_score)
        elif op == "%=":
            if source_score == 0:
                state.set_score(target, target_obj, 0)
            else:
                state.set_score(target, target_obj, target_score % source_score)
        elif op == "<":
            # Minimum operation
            state.set_score(target, target_obj, min(target_score, source_score))
        elif op == ">":
            # Maximum operation
            state.set_score(target, target_obj, max(target_score, source_score))
