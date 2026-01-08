"""Game state container for Minecraft interpreter.

This module provides the core state management for the Minecraft interpreter,
including scoreboard tracking and NBT data storage.
"""

from __future__ import annotations

from typing import Optional

from mcfunction.parser.nbt import NBTValue, NBTCompound


class ScoreboardState:
    """Manages scoreboard state including objectives, display slots, and player scores."""

    def __init__(self):
        """Initialize empty scoreboard state."""
        # Objectives: name -> (criteria, display_name)
        self.objectives: dict[str, tuple[str, Optional[str]]] = {}

        # Display slots: slot -> objective_name
        self.display_slots: dict[str, Optional[str]] = {}

        # Player scores: (player_name, objective_name) -> score
        self.scores: dict[tuple[str, str], int] = {}

    def add_objective(self, name: str, criteria: str, display: Optional[str] = None) -> None:
        """Add a new objective.

        Args:
            name: Objective name
            criteria: The criteria for the objective (e.g., "dummy")
            display: Optional display name for the objective
        """
        self.objectives[name] = (criteria, display)

    def remove_objective(self, name: str) -> None:
        """Remove an objective.

        Args:
            name: Objective name to remove
        """
        if name in self.objectives:
            del self.objectives[name]
            # Clean up any scores for this objective
            self.scores = {
                key: value for key, value in self.scores.items()
                if key[1] != name
            }
            # Clean up display slots
            for slot, obj in list(self.display_slots.items()):
                if obj == name:
                    self.display_slots[slot] = None

    def set_display(self, slot: str, objective: Optional[str]) -> None:
        """Set or clear a display slot.

        Args:
            slot: Display slot name (e.g., "sidebar", "belowName", "list")
            objective: Objective name to display, or None to clear
        """
        if objective is not None and objective not in self.objectives:
            raise ValueError(f"Objective '{objective}' does not exist")
        self.display_slots[slot] = objective

    def get_score(self, player: str, objective: str) -> int:
        """Get a player's score for an objective.

        Args:
            player: Player name
            objective: Objective name

        Returns:
            The score value (0 if not set)
        """
        if objective not in self.objectives:
            raise ValueError(f"Objective '{objective}' does not exist")
        return self.scores.get((player, objective), 0)

    def set_score(self, player: str, objective: str, value: int) -> None:
        """Set a player's score for an objective.

        Args:
            player: Player name
            objective: Objective name
            value: Score value
        """
        if objective not in self.objectives:
            raise ValueError(f"Objective '{objective}' does not exist")
        self.scores[(player, objective)] = value

    def add_score(self, player: str, objective: str, value: int) -> None:
        """Add to a player's score for an objective.

        Args:
            player: Player name
            objective: Objective name
            value: Amount to add
        """
        current = self.get_score(player, objective)
        self.set_score(player, objective, current + value)

    def remove_score(self, player: str, objective: str, value: int) -> None:
        """Remove from a player's score for an objective.

        Args:
            player: Player name
            objective: Objective name
            value: Amount to remove
        """
        current = self.get_score(player, objective)
        self.set_score(player, objective, current - value)

    def reset_scores(self, player: str, objective: Optional[str] = None) -> None:
        """Reset scores for a player.

        Args:
            player: Player name
            objective: Optional specific objective to reset, or None for all
        """
        if objective:
            # Reset specific objective
            key = (player, objective)
            if key in self.scores:
                del self.scores[key]
        else:
            # Reset all objectives for player
            self.scores = {
                key: value for key, value in self.scores.items()
                if key[0] != player
            }


class DataStorage:
    """Manages NBT data storage at namespace:path locations."""

    def __init__(self):
        """Initialize empty data storage."""
        # Storage: (namespace, path) -> NBTCompound
        self.storage: dict[tuple[str, str], NBTCompound] = {}

    def get(self, location: str, path: Optional[str] = None) -> NBTValue:
        """Get data from storage.

        Args:
            location: Full location like "minecraft:global"
            path: Optional NBT path within the storage

        Returns:
            The NBT value. Returns empty compound if storage doesn't exist.
        """
        # Parse location
        if ":" in location:
            namespace, storage_path = location.split(":", 1)
        else:
            namespace, storage_path = "minecraft", location

        key = (namespace, storage_path)

        if key not in self.storage:
            return NBTCompound({})

        data = self.storage[key]

        if path is None:
            return data

        # Navigate path (simplified - handles basic dot notation)
        result = self._navigate_path(data, path)
        return result if result is not None else NBTCompound({})

    def set(self, location: str, data: NBTCompound) -> None:
        """Set storage data.

        Args:
            location: Full location like "minecraft:global"
            data: NBT compound data
        """
        if ":" in location:
            namespace, storage_path = location.split(":", 1)
        else:
            namespace, storage_path = "minecraft", location

        self.storage[(namespace, storage_path)] = data

    def merge(self, location: str, data: NBTCompound) -> None:
        """Merge data into storage (like data merge).

        Args:
            location: Full location like "minecraft:global"
            data: NBT compound to merge
        """
        existing = self.get(location)

        if existing is None:
            # No existing data, just set it
            self.set(location, data)
            return

        if not isinstance(existing, NBTCompound):
            # Can't merge into non-compound
            return

        # Deep merge the compound
        self._merge_compound(existing, data)
        self.set(location, existing)

    def modify(
        self,
        location: str,
        path: str,
        operation: str,
        value: Optional[NBTValue] = None,
        source: Optional[str] = None,
        source_path: Optional[str] = None,
        index: Optional[int] = None
    ) -> None:
        """Modify data in storage.

        Args:
            location: Full location like "minecraft:global"
            path: NBT path to modify
            operation: Operation type (set, append, prepend, insert, merge)
            value: NBT value for value operations
            source: Source location for copy operations
            source_path: Source path within the source location
            index: Index for insert operation
        """
        existing = self.get(location)

        if existing is None:
            # Create empty compound if nothing exists
            existing = NBTCompound({})

        if not isinstance(existing, NBTCompound):
            raise ValueError("Can only modify compound data")

        # For now, handle basic set/merge operations
        # A full implementation would need to parse NBT paths properly
        if operation == "set" and value is not None:
            self._set_path(existing, path, value)
        elif operation == "merge" and value is not None:
            current = self._get_path(existing, path)
            if isinstance(current, NBTCompound) and isinstance(value, NBTCompound):
                self._merge_compound(current, value)
            else:
                self._set_path(existing, path, value)

        self.set(location, existing)

    def remove(self, location: str, path: str) -> None:
        """Remove data from storage.

        Args:
            location: Full location like "minecraft:global"
            path: NBT path to remove
        """
        existing = self.get(location)

        if existing is None:
            return

        if not isinstance(existing, NBTCompound):
            return

        self._remove_path(existing, path)
        self.set(location, existing)

    # Internal helper methods
    def _navigate_path(self, data: NBTValue, path: str) -> Optional[NBTValue]:
        """Navigate through NBT structure using a path."""
        if not path or not isinstance(data, NBTCompound):
            return data

        parts = path.split(".")
        current = data

        for part in parts:
            if not isinstance(current, NBTCompound):
                return None
            if part not in current.value:
                return None
            current = current.value[part]

        return current

    def _set_path(self, data: NBTCompound, path: str, value: NBTValue) -> None:
        """Set a value at an NBT path."""
        parts = path.split(".")
        current = data

        for part in parts[:-1]:
            if part not in current.value:
                current.value[part] = NBTCompound({})
            current = current.value[part]
            if not isinstance(current, NBTCompound):
                raise ValueError(f"Cannot navigate through non-compound at '{part}'")

        current.value[parts[-1]] = value

    def _get_path(self, data: NBTCompound, path: str) -> Optional[NBTValue]:
        """Get a value at an NBT path."""
        return self._navigate_path(data, path)

    def _remove_path(self, data: NBTCompound, path: str) -> None:
        """Remove a value at an NBT path."""
        parts = path.split(".")
        current = data

        for part in parts[:-1]:
            if part not in current.value:
                return
            current = current.value[part]
            if not isinstance(current, NBTCompound):
                return

        if parts[-1] in current.value:
            del current.value[parts[-1]]

    def _merge_compound(self, target: NBTCompound, source: NBTCompound) -> None:
        """Deep merge two NBT compounds."""
        for key, value in source.value.items():
            if key in target.value and isinstance(target.value[key], NBTCompound) and isinstance(value, NBTCompound):
                self._merge_compound(target.value[key], value)
            else:
                target.value[key] = value


class GameState:
    """Main game state container for the Minecraft interpreter.

    Tracks all game state including scoreboards, data storage, and players.
    """

    def __init__(self):
        """Initialize empty game state."""
        self.scoreboards = ScoreboardState()
        self.storage = DataStorage()
        self.players: set[str] = set()  # Track registered players for testing

    # Scoreboard methods
    def get_score(self, player: str, objective: str) -> int:
        """Get a player's score for an objective."""
        return self.scoreboards.get_score(player, objective)

    def set_score(self, player: str, objective: str, value: int) -> None:
        """Set a player's score for an objective."""
        self.scoreboards.set_score(player, objective, value)

    def add_objective(self, name: str, criteria: str, display: Optional[str] = None) -> None:
        """Add a scoreboard objective."""
        self.scoreboards.add_objective(name, criteria, display)

    def set_display(self, slot: str, objective: Optional[str]) -> None:
        """Set a display slot."""
        self.scoreboards.set_display(slot, objective)

    # Storage methods
    def get_storage(self, location: str, path: str | None = None) -> NBTValue:
        """Get data from storage."""
        return self.storage.get(location, path)

    def set_storage(self, location: str, data: NBTCompound) -> None:
        """Set storage data."""
        self.storage.set(location, data)

    def modify_storage(self, location: str, path: str, op: str, value: NBTValue) -> None:
        """Modify storage data."""
        self.storage.modify(location, path, op, value=value)
