"""Execute command executor for Minecraft interpreter.

This module provides the executor for the execute command and all its subcommands.
The execute command chains subcommands that modify execution context and conditionally
run commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from mcfunction.parser.commands import (
    Execute,
    ExecuteAlign,
    ExecuteAnchored,
    ExecuteAs,
    ExecuteAt,
    ExecuteFacing,
    ExecuteIf,
    ExecuteIn,
    ExecuteOn,
    ExecutePositioned,
    ExecuteRotated,
    ExecuteStore,
    ExecuteSummon,
    ExecuteUnless,
    ScoreboardObjectivesAdd,
    ScoreboardObjectivesRemove,
    ScoreboardObjectivesList,
    ScoreboardObjectivesSetDisplay,
    ScoreboardPlayersAdd,
    ScoreboardPlayersOperation,
    ScoreboardPlayersRemove,
    ScoreboardPlayersReset,
    ScoreboardPlayersSet,
    DataGet,
    DataMerge,
    DataModify,
    DataRemove,
    FunctionCall,
)
from mcfunction.parser.selector import EntitySelector, parse_selector
from mcfunction.parser.nbt import (
    NBTByte,
    NBTCompound,
    NBTDouble,
    NBTFloat,
    NBTInt,
    NBTLong,
    NBTShort,
    NBTString,
    NBTValue,
)

if TYPE_CHECKING:
    from mcfunction.interpreter.context import ExecutionContext
    from mcfunction.interpreter.state import GameState


def exec_execute_chain(
    state: GameState,
    context: ExecutionContext,
    execute: Execute
) -> list[ExecutionContext]:
    """Execute an execute command chain.

    This function processes all execute subcommands in order, potentially forking
    the execution context multiple times. Each subcommand can:
    - Modify the context (position, rotation, dimension, anchor, executor)
    - Create multiple contexts (forking with as/at)
    - Filter contexts (conditions with if/unless)
    - Store results (store subcommands)

    Args:
        state: The current game state
        context: The initial execution context
        execute: The Execute command containing subcommands and final command

    Returns:
        List of execution contexts ready to execute the final command
    """
    # Start with a single context
    contexts = [context]

    # Process each subcommand in order
    for subcommand in execute.subcommands:
        contexts = _process_subcommand(state, contexts, subcommand)

        # If no contexts remain, we can stop early
        if not contexts:
            return []

    return contexts


def _process_subcommand(
    state: GameState,
    contexts: list[ExecutionContext],
    subcommand: Any
) -> list[ExecutionContext]:
    """Process a single execute subcommand across all contexts.

    Args:
        state: The current game state
        contexts: List of current execution contexts
        subcommand: The subcommand to process

    Returns:
        Updated list of execution contexts
    """
    if isinstance(subcommand, ExecuteAs):
        return _process_as(contexts, subcommand)

    elif isinstance(subcommand, ExecuteAt):
        return _process_at(state, contexts, subcommand)

    elif isinstance(subcommand, ExecuteAlign):
        return _process_align(contexts, subcommand)

    elif isinstance(subcommand, ExecuteAnchored):
        return _process_anchored(contexts, subcommand)

    elif isinstance(subcommand, ExecuteFacing):
        return _process_facing(state, contexts, subcommand)

    elif isinstance(subcommand, ExecuteIn):
        return _process_in(contexts, subcommand)

    elif isinstance(subcommand, ExecuteOn):
        return _process_on(state, contexts, subcommand)

    elif isinstance(subcommand, ExecutePositioned):
        return _process_positioned(state, contexts, subcommand)

    elif isinstance(subcommand, ExecuteRotated):
        return _process_rotated(state, contexts, subcommand)

    elif isinstance(subcommand, ExecuteSummon):
        return _process_summon(state, contexts, subcommand)

    elif isinstance(subcommand, ExecuteIf):
        return _process_if(state, contexts, subcommand)

    elif isinstance(subcommand, ExecuteUnless):
        return _process_unless(state, contexts, subcommand)

    elif isinstance(subcommand, ExecuteStore):
        return _process_store(state, contexts, subcommand)

    else:
        # Unknown subcommand type
        return contexts


def _process_as(
    contexts: list[ExecutionContext],
    subcommand: ExecuteAs
) -> list[ExecutionContext]:
    """Process execute as <selector> - forks contexts for each matching entity.

    Args:
        contexts: Current execution contexts
        subcommand: ExecuteAs subcommand

    Returns:
        New list of contexts, one for each entity matched by selector
    """
    # Resolve selector to entity list
    entities = _resolve_selector(subcommand.selector)

    # Fork each context for each entity
    new_contexts = []
    for ctx in contexts:
        for entity in entities:
            new_contexts.append(ctx.fork(entity))

    return new_contexts


def _process_at(
    state: GameState,
    contexts: list[ExecutionContext],
    subcommand: ExecuteAt
) -> list[ExecutionContext]:
    """Process execute at <selector> - sets position/rotation from entities.

    Args:
        contexts: Current execution contexts
        subcommand: ExecuteAt subcommand

    Returns:
        Forked contexts positioned at matching entities
    """
    entities = _resolve_selector(subcommand.selector)
    new_contexts = []

    for ctx in contexts:
        for entity in entities:
            # In a real implementation, we'd query entity position/rotation
            # For this interpreter, we'll use a placeholder approach
            # Each forked context inherits position from the entity
            forked = ctx.fork(entity)
            # In real implementation, set position/rotation from entity
            # For now, keep current position but we've forked
            new_contexts.append(forked)

    return new_contexts


def _process_align(
    contexts: list[ExecutionContext],
    subcommand: ExecuteAlign
) -> list[ExecutionContext]:
    """Process execute align <axes> - aligns to block grid.

    Args:
        contexts: Current execution contexts
        subcommand: ExecuteAlign subcommand

    Returns:
        Modified contexts
    """
    axes = subcommand.axes.lower()

    for ctx in contexts:
        x, y, z = ctx.position

        if 'x' in axes:
            x = float(int(x))  # Round down to block boundary
        if 'y' in axes:
            y = float(int(y))
        if 'z' in axes:
            z = float(int(z))

        ctx.position = (x, y, z)

    return contexts


def _process_anchored(
    contexts: list[ExecutionContext],
    subcommand: ExecuteAnchored
) -> list[ExecutionContext]:
    """Process execute anchored <anchor> - sets anchor point.

    Args:
        contexts: Current execution contexts
        subcommand: ExecuteAnchored subcommand

    Returns:
        Modified contexts
    """
    for ctx in contexts:
        ctx.set_anchor(subcommand.anchor)

    return contexts


def _process_facing(
    state: GameState,
    contexts: list[ExecutionContext],
    subcommand: ExecuteFacing
) -> list[ExecutionContext]:
    """Process execute facing <target> - sets rotation to face target.

    Args:
        contexts: Current execution contexts
        subcommand: ExecuteFacing subcommand

    Returns:
        Modified contexts
    """
    # Handle facing entity selector
    if subcommand.target is not None:
        entities = _resolve_selector(subcommand.target)
        # In real implementation, calculate direction to entity
        # For now, just update rotation (placeholder)
        for ctx in contexts:
            # Would calculate yaw/pitch to face entity
            # Placeholder: keep current rotation
            pass

    # Handle facing coordinates
    elif subcommand.x is not None:
        target_x, target_y, target_z = subcommand.x, subcommand.y, subcommand.z
        for ctx in contexts:
            x, y, z = ctx.position
            # Calculate direction to target coordinates
            # Placeholder: set fixed rotation or calculate properly
            # For now, we'd calculate yaw and pitch here
            # This is a simplified version
            dx = target_x - x
            dy = target_y - y
            dz = target_z - z

            # Calculate yaw (horizontal rotation)
            import math
            if dz != 0 or dx != 0:
                yaw = -math.degrees(math.atan2(dx, dz))
            else:
                yaw = 0

            # Calculate pitch (vertical rotation)
            distance_horizontal = math.sqrt(dx * dx + dz * dz)
            if distance_horizontal != 0 or dy != 0:
                pitch = -math.degrees(math.atan2(dy, distance_horizontal))
            else:
                pitch = 0

            ctx.set_rotation(yaw, pitch)

    return contexts


def _process_in(
    contexts: list[ExecutionContext],
    subcommand: ExecuteIn
) -> list[ExecutionContext]:
    """Process execute in <dimension> - sets dimension.

    Args:
        contexts: Current execution contexts
        subcommand: ExecuteIn subcommand

    Returns:
        Modified contexts
    """
    for ctx in contexts:
        ctx.set_dimension(subcommand.dimension)

    return contexts


def _process_on(
    state: GameState,
    contexts: list[ExecutionContext],
    subcommand: ExecuteOn
) -> list[ExecutionContext]:
    """Process execute on <target> - executes on block/entity/bossbar/storage/players.

    Args:
        contexts: Current execution contexts
        subcommand: ExecuteOn subcommand

    Returns:
        Forked contexts for the target
    """
    # Execute on target can fork contexts
    # For block, entity, bossbar - would query targets
    # For storage - would target storage location
    # For players - would target all players

    new_contexts = []
    target_type = subcommand.target

    for ctx in contexts:
        if target_type == "players":
            # Fork for all players (placeholder)
            new_contexts.append(ctx.fork("@a"))
        elif target_type == "entity":
            # Fork for entities (placeholder)
            new_contexts.append(ctx.fork("@e"))
        elif target_type == "block":
            # Target block at current position (no fork, but change context)
            new_ctx = ctx.clone()
            # Block context would reference block location
            new_contexts.append(new_ctx)
        elif target_type == "storage":
            # Target storage (no fork)
            new_contexts.append(ctx.clone())
        elif target_type == "bossbar":
            # Target bossbar (no fork)
            new_contexts.append(ctx.clone())

    return new_contexts if new_contexts else contexts


def _process_positioned(
    state: GameState,
    contexts: list[ExecutionContext],
    subcommand: ExecutePositioned
) -> list[ExecutionContext]:
    """Process execute positioned <selector|coordinates> - sets position.

    Args:
        contexts: Current execution contexts
        subcommand: ExecutePositioned subcommand

    Returns:
        Modified contexts
    """
    if subcommand.selector is not None:
        # Positioned at entity selector
        entities = _resolve_selector(subcommand.selector)
        new_contexts = []
        for ctx in contexts:
            for entity in entities:
                # Fork and set position from entity
                forked = ctx.fork(entity)
                # Would set position from entity
                new_contexts.append(forked)
        return new_contexts

    elif subcommand.x is not None:
        # Positioned at coordinates
        for ctx in contexts:
            ctx.set_position(subcommand.x, subcommand.y, subcommand.z)

    return contexts


def _process_rotated(
    state: GameState,
    contexts: list[ExecutionContext],
    subcommand: ExecuteRotated
) -> list[ExecutionContext]:
    """Process execute rotated <selector|rotation> - sets rotation.

    Args:
        contexts: Current execution contexts
        subcommand: ExecuteRotated subcommand

    Returns:
        Modified contexts
    """
    if subcommand.selector is not None:
        # Rotated from entity selector
        entities = _resolve_selector(subcommand.selector)
        new_contexts = []
        for ctx in contexts:
            for entity in entities:
                # Fork and set rotation from entity
                forked = ctx.fork(entity)
                # Would set rotation from entity
                new_contexts.append(forked)
        return new_contexts

    elif subcommand.yaw is not None:
        # Rotated with explicit angles
        for ctx in contexts:
            ctx.set_rotation(subcommand.yaw, subcommand.pitch or 0.0)

    return contexts


def _process_summon(
    state: GameState,
    contexts: list[ExecutionContext],
    subcommand: ExecuteSummon
) -> list[ExecutionContext]:
    """Process execute summon - summons entity and becomes it.

    Args:
        contexts: Current execution contexts
        subcommand: ExecuteSummon subcommand

    Returns:
        New contexts with summoned entity as executor
    """
    # Summon entity and change executor to it
    for ctx in contexts:
        # In a real implementation, this would summon the entity
        # and set the executor to the summoned entity's ID
        # For now, we just change the executor to the entity type
        # as a placeholder
        ctx.executor = f"@e[type={subcommand.entity},limit=1]"

    return contexts


def _process_if(
    state: GameState,
    contexts: list[ExecutionContext],
    subcommand: ExecuteIf
) -> list[ExecutionContext]:
    """Process execute if <condition> - keeps contexts that pass condition.

    Args:
        contexts: Current execution contexts
        subcommand: ExecuteIf subcommand

    Returns:
        Filtered list of contexts that pass the condition
    """
    return _evaluate_condition(state, contexts, subcommand, negate=False)


def _process_unless(
    state: GameState,
    contexts: list[ExecutionContext],
    subcommand: ExecuteUnless
) -> list[ExecutionContext]:
    """Process execute unless <condition> - keeps contexts that fail condition.

    Args:
        contexts: Current execution contexts
        subcommand: ExecuteUnless subcommand

    Returns:
        Filtered list of contexts that fail the condition
    """
    return _evaluate_condition(state, contexts, subcommand, negate=True)


def _evaluate_condition(
    state: GameState,
    contexts: list[ExecutionContext],
    subcommand: ExecuteIf | ExecuteUnless,
    negate: bool
) -> list[ExecutionContext]:
    """Evaluate a condition and filter contexts.

    Args:
        state: The game state
        contexts: Current execution contexts
        subcommand: ExecuteIf or ExecuteUnless
        negate: Whether to negate the condition result

    Returns:
        Filtered contexts
    """
    condition_type = subcommand.condition_type
    condition_args = subcommand.condition_args

    passing_contexts = []

    for ctx in contexts:
        result = _check_condition(state, ctx, condition_type, condition_args)

        # Apply negation
        if negate:
            result = not result

        if result:
            passing_contexts.append(ctx)

    return passing_contexts


def _check_condition(
    state: GameState,
    ctx: ExecutionContext,
    condition_type: str,
    condition_args: dict[str, Any]
) -> bool:
    """Check a single condition.

    Args:
        state: The game state
        ctx: The execution context
        condition_type: Type of condition
        condition_args: Arguments for the condition

    Returns:
        Whether the condition passes
    """
    if condition_type == "block":
        # if block <x> <y> <z> <block>
        x = condition_args.get("x", ctx.position[0])
        y = condition_args.get("y", ctx.position[1])
        z = condition_args.get("z", ctx.position[2])
        block = condition_args.get("block")

        # Would check if block exists at position
        # For this interpreter, we'll return True as placeholder
        # In real implementation, query game world
        return True

    elif condition_type == "data":
        # if data <source> <path>
        source = condition_args.get("source")
        path = condition_args.get("path")

        # Parse source (storage, entity, block)
        if source.startswith("storage"):
            # storage <namespace>:<path>
            parts = source.split(" ", 1)
            if len(parts) > 1:
                location = parts[1]
                data = state.storage.get(location, path)
                # Check if data exists and is non-empty
                if isinstance(data, NBTCompound):
                    return len(data.value) > 0
                return data is not None

        # For entity/block, placeholder
        return True

    elif condition_type == "entity":
        # if entity <selector>
        selector_str = condition_args.get("selector")
        if not selector_str:
            return False

        try:
            selector = parse_selector(selector_str)
            entities = _resolve_selector(selector)
            # Check if any entities match
            return len(entities) > 0
        except ValueError:
            return False

    elif condition_type == "score":
        # if score <target> <objective> <operator> <value|source> [<sourceObjective>]
        target = condition_args.get("target")
        objective = condition_args.get("objective")
        operator = condition_args.get("operator")
        value_or_source = condition_args.get("value")
        source_objective = condition_args.get("sourceObjective")

        if target is None or objective is None or operator is None:
            return False

        # Get target score
        target_players = _resolve_target(state, target)
        if not target_players:
            return False

        target_score = state.get_score(target_players[0], objective)

        # Compare based on operator
        if operator in ("=", "=="):
            if source_objective:
                # Compare with another score
                source_players = _resolve_target(state, value_or_source)
                if not source_players:
                    return False
                source_score = state.get_score(source_players[0], source_objective)
                return target_score == source_score
            else:
                # Compare with value
                return target_score == int(value_or_source)

        elif operator == "!=":
            if source_objective:
                source_players = _resolve_target(state, value_or_source)
                if not source_players:
                    return False
                source_score = state.get_score(source_players[0], source_objective)
                return target_score != source_score
            else:
                return target_score != int(value_or_source)

        elif operator == "<":
            if source_objective:
                source_players = _resolve_target(state, value_or_source)
                if not source_players:
                    return False
                source_score = state.get_score(source_players[0], source_objective)
                return target_score < source_score
            else:
                return target_score < int(value_or_source)

        elif operator == "<=":
            if source_objective:
                source_players = _resolve_target(state, value_or_source)
                if not source_players:
                    return False
                source_score = state.get_score(source_players[0], source_objective)
                return target_score <= source_score
            else:
                return target_score <= int(value_or_source)

        elif operator == ">":
            if source_objective:
                source_players = _resolve_target(state, value_or_source)
                if not source_players:
                    return False
                source_score = state.get_score(source_players[0], source_objective)
                return target_score > source_score
            else:
                return target_score > int(value_or_source)

        elif operator == ">=":
            if source_objective:
                source_players = _resolve_target(state, value_or_source)
                if not source_players:
                    return False
                source_score = state.get_score(source_players[0], source_objective)
                return target_score >= source_score
            else:
                return target_score >= int(value_or_source)

        return False

    else:
        # Unknown condition type
        return False


def _process_store(
    state: GameState,
    contexts: list[ExecutionContext],
    subcommand: ExecuteStore
) -> list[ExecutionContext]:
    """Process execute store - stores result/success of subsequent command.

    Note: Store commands modify the context to remember what needs to be stored,
    but the actual storage happens after the command executes.

    Args:
        contexts: Current execution contexts
        subcommand: ExecuteStore subcommand

    Returns:
        Modified contexts with store information
    """
    # Store is tricky because it needs to capture the result of the NEXT command
    # We'll store the information in the context for later use
    # The actual storage happens when the command is executed

    for ctx in contexts:
        # Store the store operation in the context
        # This will be used by the command executor
        if not hasattr(ctx, '_store_ops'):
            ctx._store_ops = []

        ctx._store_ops.append({
            'type': subcommand.store_type,
            'target': subcommand.target,
            'path': subcommand.path,
            'store_type': subcommand.type,
            'scale': subcommand.scale
        })

    return contexts


def _resolve_selector(selector: EntitySelector) -> list[str]:
    """Resolve an entity selector to a list of entity identifiers.

    In a real Minecraft implementation, this would query the world for matching entities.
    For this interpreter, we return placeholder identifiers based on selector type.

    Args:
        selector: Parsed entity selector

    Returns:
        List of entity identifiers (player names or entity IDs)
    """
    selector_type = selector.selector_type

    # Simple selectors without arguments
    if not selector.arguments:
        if selector_type == "s":
            return ["@s"]
        elif selector_type == "a":
            return ["@a"]  # All players (placeholder)
        elif selector_type == "e":
            return ["@e"]  # All entities (placeholder)
        elif selector_type == "p":
            return ["@p"]  # Nearest player (placeholder)
        elif selector_type == "r":
            return ["@r"]  # Random player (placeholder)

    # Selectors with arguments
    # In a real implementation, these would filter entities
    # For this interpreter, we return the selector type as-is
    if selector_type == "s":
        return ["@s"]
    elif selector_type == "a":
        return ["@a"]
    elif selector_type == "e":
        return ["@e"]
    elif selector_type == "p":
        return ["@p"]
    elif selector_type == "r":
        return ["@r"]

    return ["@s"]


def _resolve_target(state: GameState, target: str) -> list[str]:
    """Resolve a target string (selector or player name) to player names.

    Args:
        state: The game state
        target: Selector or player name

    Returns:
        List of player names
    """
    if not target.startswith("@"):
        return [target]

    try:
        selector = parse_selector(target)
        return _resolve_selector(selector)
    except ValueError:
        return [target]


def exec_execute_run(
    state: GameState,
    contexts: list[ExecutionContext],
    command: Any
) -> None:
    """Execute the final command in an execute chain.

    This is called with the contexts returned by exec_execute_chain.
    It runs the command for each context, handling store operations.

    Args:
        state: The game state
        contexts: Execution contexts from the chain
        command: The command to execute
    """
    from mcfunction.interpreter.builtins import (
        exec_scoreboard_players_set,
        exec_scoreboard_players_add,
        exec_scoreboard_players_remove,
        exec_scoreboard_players_reset,
        exec_scoreboard_players_operation,
        exec_data_get,
        exec_data_merge,
        exec_data_modify,
        exec_data_remove,
    )

    for ctx in contexts:
        # Execute the command
        result = 0
        success = False

        if isinstance(command, ScoreboardPlayersSet):
            exec_scoreboard_players_set(state, command.targets, command.objective, command.score)
            result = command.score
            success = True

        elif isinstance(command, ScoreboardPlayersAdd):
            exec_scoreboard_players_add(state, command.targets, command.objective, command.score)
            result = command.score
            success = True

        elif isinstance(command, ScoreboardPlayersRemove):
            exec_scoreboard_players_remove(state, command.targets, command.objective, command.score)
            result = command.score
            success = True

        elif isinstance(command, ScoreboardPlayersReset):
            exec_scoreboard_players_reset(state, command.targets, command.objective)
            result = 0
            success = True

        elif isinstance(command, ScoreboardPlayersOperation):
            exec_scoreboard_players_operation(
                state, command.targets, command.target_objective, command.operation,
                command.source, command.source_objective
            )
            result = 0
            success = True

        elif isinstance(command, DataGet):
            result_data = exec_data_get(state, command.target, command.path)
            # Convert NBT to int for result
            if isinstance(result_data, NBTInt):
                result = result_data.value
            elif isinstance(result_data, NBTCompound):
                result = 1 if result_data.value else 0
            else:
                result = 0
            success = True

        elif isinstance(command, DataMerge):
            exec_data_merge(state, command.target, command.nbt)
            result = 0
            success = True

        elif isinstance(command, DataModify):
            exec_data_modify(
                state, command.target, command.path, command.operation,
                command.source, command.value, command.index
            )
            result = 0
            success = True

        elif isinstance(command, DataRemove):
            exec_data_remove(state, command.target, command.path)
            result = 0
            success = True

        elif isinstance(command, Execute):
            # Nested execute - recursive call
            nested_contexts = exec_execute_chain(state, ctx, command)
            for nested_ctx in nested_contexts:
                if nested_ctx._store_ops:
                    # Would handle nested store operations
                    pass
            result = 0
            success = True

        elif isinstance(command, FunctionCall):
            # Function call - would be handled by function executor
            # For now, treat as success
            result = 0
            success = True

        else:
            # Unknown command type
            result = 0
            success = False

        # Update context result and success
        ctx.result = result
        ctx.success = success

        # Handle store operations
        if hasattr(ctx, '_store_ops') and ctx._store_ops:
            for store_op in ctx._store_ops:
                _perform_store_operation(state, ctx, store_op)

            # Clear store operations after processing
            ctx._store_ops = []


def _perform_store_operation(
    state: GameState,
    ctx: ExecutionContext,
    store_op: dict[str, Any]
) -> None:
    """Perform a store operation.

    Args:
        state: The game state
        ctx: The execution context
        store_op: Store operation data
    """
    store_type = store_op['type']
    target = store_op['target']
    path = store_op['path']
    data_type = store_op['store_type']
    scale = store_op['scale']

    # Determine value to store
    if store_type == "result":
        value = ctx.result
    else:  # "success"
        value = 1 if ctx.success else 0

    # Apply scale
    if scale is not None:
        value = int(value * scale)

    # Store the value
    # Parse target format: "storage namespace:path" or "entity @s" or "block x y z"
    parts = target.split(" ", 1)
    if len(parts) < 2:
        return

    target_type = parts[0]
    target_location = parts[1]

    if target_type == "storage":
        # Store in NBT storage
        nbt_value = _value_to_nbt(value, data_type)
        # Set at the specified path
        if path:
            # Need to use modify
            # This is simplified - in real implementation, would use proper NBT path
            current = state.storage.get(target_location)
            if not isinstance(current, NBTCompound):
                current = NBTCompound({})
            current.value[path] = nbt_value
            state.storage.set(target_location, current)
        else:
            # Store at root
            if isinstance(nbt_value, NBTCompound):
                state.storage.set(target_location, nbt_value)
            else:
                # Wrap in compound
                state.storage.set(target_location, NBTCompound({path or "value": nbt_value}))

    elif target_type == "entity":
        # Store in entity NBT (not fully implemented for this interpreter)
        pass

    elif target_type == "block":
        # Store in block NBT (not fully implemented for this interpreter)
        pass


def _value_to_nbt(value: int, data_type: str | None) -> NBTValue:
    """Convert a Python value to NBT format.

    Args:
        value: The value to convert
        data_type: Target NBT type

    Returns:
        NBT value
    """
    if data_type is None:
        return NBTInt(value)

    # Map types to NBT
    type_map = {
        "byte": NBTByte,
        "short": NBTShort,
        "int": NBTInt,
        "long": NBTLong,
        "float": NBTFloat,
        "double": NBTDouble,
    }

    nbt_class = type_map.get(data_type, NBTInt)

    # Convert for float types
    if nbt_class in (NBTFloat, NBTDouble):
        return nbt_class(float(value))

    return nbt_class(value)
