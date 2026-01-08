"""Data operations executor for Minecraft interpreter.

This module provides executor functions for all data commands:
- data get
- data merge
- data modify
- data remove
"""

from __future__ import annotations

from mcfunction.interpreter.state import GameState
from mcfunction.parser.nbt import NBTCompound, NBTList, NBTValue


def parse_location(location: str) -> tuple[str, str]:
    """Parse a location string into type and target.

    Args:
        location: Location string like "storage minecraft:global" or "entity @s"

    Returns:
        Tuple of (location_type, target)

    Examples:
        >>> parse_location("storage minecraft:global")
        ("storage", "minecraft:global")
        >>> parse_location("entity @s")
        ("entity", "@s")
    """
    parts = location.split(" ", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid location format: {location}")
    return parts[0], parts[1]


def resolve_location_target(state: GameState, location_type: str, target: str) -> NBTValue | None:
    """Resolve a location to its NBT data.

    Args:
        state: The current game state
        location_type: Type of location ('storage', 'entity', 'block')
        target: The target identifier

    Returns:
        The NBT value at the location, or None if not found
    """
    if location_type == "storage":
        return state.storage.get(target)
    elif location_type in ("entity", "block"):
        # Entity and block storage not yet implemented
        # For now, return empty compound
        return NBTCompound({})
    else:
        raise ValueError(f"Unknown location type: {location_type}")


def set_location_target(
    state: GameState, location_type: str, target: str, data: NBTCompound
) -> None:
    """Set NBT data at a location.

    Args:
        state: The current game state
        location_type: Type of location ('storage', 'entity', 'block')
        target: The target identifier
        data: NBT compound data to set
    """
    if location_type == "storage":
        state.storage.set(target, data)
    elif location_type in ("entity", "block"):
        # Entity and block storage not yet implemented
        pass
    else:
        raise ValueError(f"Unknown location type: {location_type}")


def exec_data_get(state: GameState, location: str, path: str | None = None) -> NBTValue:
    """Execute data get command.

    Args:
        state: The current game state
        location: Location like "storage minecraft:global" or "entity @s"
        path: Optional NBT path to get specific value

    Returns:
        The NBT value at the location/path

    Examples:
        >>> exec_data_get(state, "storage minecraft:global", "vars.health")
        NBTInt(20)
    """
    location_type, target = parse_location(location)
    data = resolve_location_target(state, location_type, target)

    if data is None:
        return NBTCompound({})

    if path is None:
        return data

    # Navigate path
    if isinstance(data, NBTCompound):
        parts = path.split(".")
        current: NBTValue = data
        for part in parts:
            if not isinstance(current, NBTCompound) or part not in current.value:
                return NBTCompound({})
            current = current.value[part]
        return current

    return data


def exec_data_merge(state: GameState, location: str, nbt: NBTCompound) -> None:
    """Execute data merge command.

    Args:
        state: The current game state
        location: Location like "storage minecraft:global" or "entity @s"
        nbt: NBT compound to merge

    Examples:
        >>> exec_data_merge(state, "storage minecraft:global", parse_snbt("{value:10}"))
    """
    location_type, target = parse_location(location)
    state.storage.merge(target, nbt)


def _resolve_value_from_source(state: GameState, source: str) -> NBTValue:
    """Resolve a value from a source path (for modify operations with 'from').

    Args:
        state: The current game state
        source: Source string like "storage minecraft:global path" or "entity @s Health"

    Returns:
        The NBT value from the source
    """
    parts = source.split(" ", 2)
    if len(parts) < 2:
        raise ValueError(f"Invalid source format: {source}")

    location_type = parts[0]
    target = parts[1]
    source_path = parts[2] if len(parts) > 2 else None

    return exec_data_get(state, f"{location_type} {target}", source_path)


def _navigate_to_parent(
    state: GameState, location_type: str, target: str, path: str
) -> tuple[NBTCompound, str]:
    """Navigate to the parent compound and get the key for the final element.

    Args:
        state: The current game state
        location_type: Type of location
        target: Target identifier
        path: NBT path to navigate

    Returns:
        Tuple of (parent_compound, final_key)

    Raises:
        ValueError: If path cannot be navigated
    """
    data = resolve_location_target(state, location_type, target)
    if data is None:
        data = NBTCompound({})

    if not isinstance(data, NBTCompound):
        raise ValueError("Cannot navigate through non-compound data")

    parts = path.split(".")
    if len(parts) == 1:
        return data, parts[0]

    current: NBTValue = data
    for part in parts[:-1]:
        if not isinstance(current, NBTCompound):
            raise ValueError(f"Cannot navigate through non-compound at '{part}'")
        if part not in current.value:
            current.value[part] = NBTCompound({})
        current = current.value[part]
        if not isinstance(current, NBTCompound):
            raise ValueError(f"Cannot navigate through non-compound at '{part}'")

    if not isinstance(current, NBTCompound):
        raise ValueError("Internal error: parent should be compound")
    return current, parts[-1]


def exec_data_modify(
    state: GameState,
    location: str,
    path: str,
    operation: str,
    target_path: str | None = None,
    value: NBTValue | None = None,
    index: int | None = None
) -> None:
    """Execute data modify command.

    Args:
        state: The current game state
        location: Location like "storage minecraft:global" or "entity @s"
        path: NBT path to modify
        operation: Operation type ('set', 'append', 'prepend', 'insert', 'merge')
        target_path: Optional source path for 'from' operations
        value: Optional NBT value for 'value' operations
        index: Optional index for 'insert' operation

    Examples:
        >>> exec_data_modify(state, "storage minecraft:global", "vars.health",
        ...                  "set", value=NBTInt(20))
        >>> exec_data_modify(state, "storage minecraft:global", "vars.items", "append",
        ...                  value=parse_snbt("{id:'minecraft:stone'}"))
    """
    location_type, target = parse_location(location)

    # Get source value if needed
    source_value = None
    if target_path:
        source_value = _resolve_value_from_source(state, target_path)
    elif value is not None:
        source_value = value

    # Navigate to parent and get final key
    parent, final_key = _navigate_to_parent(state, location_type, target, path)

    # Handle different operations
    if operation == "set":
        if source_value is None:
            raise ValueError("set operation requires a value")
        parent.value[final_key] = source_value

    elif operation == "merge":
        if source_value is None:
            raise ValueError("merge operation requires a value")

        current = parent.value.get(final_key)
        if isinstance(current, NBTCompound) and isinstance(source_value, NBTCompound):
            # Deep merge
            for k, v in source_value.value.items():
                if k in current.value:
                    current_value = current.value[k]
                    if isinstance(current_value, NBTCompound) and isinstance(v, NBTCompound):
                        _merge_compound_recursive(current_value, v)
                    else:
                        current.value[k] = v
                else:
                    current.value[k] = v
        else:
            parent.value[final_key] = source_value

    elif operation == "append":
        if source_value is None:
            raise ValueError("append operation requires a value")

        current = parent.value.get(final_key)
        if isinstance(current, NBTList):
            current.value.append(source_value)
        else:
            # Create new list
            parent.value[final_key] = NBTList([source_value])

    elif operation == "prepend":
        if source_value is None:
            raise ValueError("prepend operation requires a value")

        current = parent.value.get(final_key)
        if isinstance(current, NBTList):
            current.value.insert(0, source_value)
        else:
            # Create new list
            parent.value[final_key] = NBTList([source_value])

    elif operation == "insert":
        if source_value is None:
            raise ValueError("insert operation requires a value")
        if index is None:
            raise ValueError("insert operation requires an index")

        current = parent.value.get(final_key)
        if isinstance(current, NBTList):
            if 0 <= index <= len(current.value):
                current.value.insert(index, source_value)
            else:
                msg = f"Index {index} out of bounds for list of length {len(current.value)}"
                raise ValueError(msg)
        else:
            raise ValueError("insert operation requires a list")

    else:
        raise ValueError(f"Unknown operation: {operation}")

    # Save back to storage
    if location_type == "storage":
        # Need to update the entire storage entry
        _update_storage_entry(state, location_type, target, path, parent, final_key)


def _update_storage_entry(
    state: GameState,
    location_type: str,
    target: str,
    path: str,
    parent: NBTCompound,
    final_key: str
) -> None:
    """Update the storage entry after modification.

    Args:
        state: The current game state
        location_type: Type of location
        target: Target identifier
        path: Full path that was modified
        parent: Parent compound containing the modified value
        final_key: Final key that was modified
    """
    if location_type != "storage":
        return

    # If path is top-level, just update the storage
    parts = path.split(".")
    if len(parts) == 1:
        state.storage.set(target, parent)
        return

    # For nested paths, need to rebuild from root
    existing = resolve_location_target(state, location_type, target)
    if existing is None:
        existing = NBTCompound({})

    if not isinstance(existing, NBTCompound):
        return

    # Navigate to the same parent and update
    current: NBTValue = existing
    for part in parts[:-1]:
        if not isinstance(current, NBTCompound):
            return
        if part not in current.value:
            current.value[part] = NBTCompound({})
        current = current.value[part]
        if not isinstance(current, NBTCompound):
            return

    if not isinstance(current, NBTCompound):
        return
    current.value[final_key] = parent.value[final_key]
    state.storage.set(target, existing)


def _merge_compound_recursive(target: NBTCompound, source: NBTCompound) -> None:
    """Recursively merge two NBT compounds.

    Args:
        target: Target compound to merge into
        source: Source compound to merge from
    """
    for key, value in source.value.items():
        if key in target.value:
            target_value = target.value[key]
            if isinstance(target_value, NBTCompound) and isinstance(value, NBTCompound):
                _merge_compound_recursive(target_value, value)
            else:
                target.value[key] = value
        else:
            target.value[key] = value


def exec_data_remove(state: GameState, location: str, path: str) -> None:
    """Execute data remove command.

    Args:
        state: The current game state
        location: Location like "storage minecraft:global" or "entity @s"
        path: NBT path to remove

    Examples:
        >>> exec_data_remove(state, "storage minecraft:global", "vars.old_data")
    """
    location_type, target = parse_location(location)
    data = resolve_location_target(state, location_type, target)

    if data is None or not isinstance(data, NBTCompound):
        return

    parts = path.split(".")
    current: NBTValue = data

    # Navigate to parent
    for part in parts[:-1]:
        if not isinstance(current, NBTCompound):
            return
        if part not in current.value:
            return
        current = current.value[part]
        if not isinstance(current, NBTCompound):
            return

    # Remove final key
    if not isinstance(current, NBTCompound):
        return
    final_key = parts[-1]
    if final_key in current.value:
        del current.value[final_key]

    # Save back to storage
    if location_type == "storage":
        state.storage.set(target, data)
