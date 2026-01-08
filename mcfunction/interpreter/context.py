"""Execution context for Minecraft command execution.

This module provides the execution context that tracks the state of command execution,
including executor identity, position, rotation, dimension, and result storage.
"""

from __future__ import annotations

from typing import Optional


class ExecutionContext:
    """Tracks the execution context for Minecraft commands.

    The execution context contains information about who is executing commands,
    where they are located, and what the result of the last operation was.
    This context is used by execute commands to chain subcommands and fork
    execution across multiple entities.

    Attributes:
        executor: The entity executing the command (e.g., "@s", "PlayerName", "@a")
        position: The execution position as (x, y, z) coordinates
        rotation: The execution rotation as (yaw, pitch) angles
        dimension: The dimension identifier (e.g., "overworld", "the_nether", "the_end")
        anchor: The anchor point for facing/positioning ("eyes" or "feet")
        success: Whether the last operation succeeded
        result: The result value from the last operation (used for store commands)
    """

    def __init__(
        self,
        executor: str = "@s",
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation: tuple[float, float] = (0.0, 0.0),
        dimension: str = "overworld",
        anchor: str = "feet",
        success: bool = True,
        result: int = 0
    ):
        """Initialize an execution context.

        Args:
            executor: The executing entity (default: "@s")
            position: (x, y, z) coordinates (default: (0, 0, 0))
            rotation: (yaw, pitch) angles (default: (0, 0))
            dimension: Dimension identifier (default: "overworld")
            anchor: Anchor point - "eyes" or "feet" (default: "feet")
            success: Success state of last operation (default: True)
            result: Result value for store operations (default: 0)
        """
        self.executor = executor
        self.position = position
        self.rotation = rotation
        self.dimension = dimension
        self.anchor = anchor
        self.success = success
        self.result = result

    def fork(self, entity: str) -> ExecutionContext:
        """Create a child context for forking behavior.

        Creates a new execution context that inherits most properties from the current
        context but changes the executor. This is used by execute commands to run
        subcommands as different entities.

        The forked context:
        - Inherits position, rotation, dimension, and anchor
        - Gets the new executor
        - Resets success and result (starts fresh for the forked execution)

        Args:
            entity: The new executor entity (e.g., "@a", "PlayerName", "@e[type=armor_stand]")

        Returns:
            A new ExecutionContext with the specified executor
        """
        return ExecutionContext(
            executor=entity,
            position=self.position,
            rotation=self.rotation,
            dimension=self.dimension,
            anchor=self.anchor,
            success=True,  # Reset for forked execution
            result=0       # Reset for forked execution
        )

    def store_result(
        self,
        store_type: str,
        target: str,
        path: str | None
    ) -> None:
        """Store the result value according to execute store subcommand.

        This method handles the result storage logic for execute store commands.
        In a full implementation, this would write to the actual target location
        (storage, entity NBT, or block NBT). For this interpreter, it tracks
        the intent and validates parameters.

        Args:
            store_type: Type of store operation ('result' or 'success')
            target: Target location type and identifier (e.g., "storage minecraft:global")
            path: NBT path within the target, or None for root

        Examples:
            >>> ctx = ExecutionContext(result=5, success=True)
            >>> ctx.store_result("result", "storage minecraft:global", "score")
            # This would store 5 at the specified location

            >>> ctx.store_result("success", "storage minecraft:global", "did_succeed")
            # This would store 1 (true) or 0 (false) based on success
        """
        # Determine the value to store
        if store_type == "result":
            value_to_store = self.result
        elif store_type == "success":
            value_to_store = 1 if self.success else 0
        else:
            raise ValueError(f"Invalid store_type: {store_type}. Must be 'result' or 'success'")

        # In a full implementation, this would interact with GameState to store the value
        # For now, we validate the parameters and could log the operation
        if not target:
            raise ValueError("Target cannot be empty for store operation")

        # The actual storage would happen through the GameState, but we've tracked the intent
        # This method exists primarily to encapsulate the store logic
        pass

    def set_position(self, x: float, y: float, z: float) -> None:
        """Update the execution position.

        Args:
            x: X coordinate
            y: Y coordinate
            z: Z coordinate
        """
        self.position = (x, y, z)

    def set_rotation(self, yaw: float, pitch: float) -> None:
        """Update the execution rotation.

        Args:
            yaw: Yaw angle (horizontal rotation)
            pitch: Pitch angle (vertical rotation)
        """
        self.rotation = (yaw, pitch)

    def set_dimension(self, dimension: str) -> None:
        """Update the execution dimension.

        Args:
            dimension: Dimension identifier
        """
        self.dimension = dimension

    def set_anchor(self, anchor: str) -> None:
        """Update the execution anchor.

        Args:
            anchor: Anchor point ('eyes' or 'feet')
        """
        if anchor not in ("eyes", "feet"):
            raise ValueError(f"Invalid anchor: {anchor}. Must be 'eyes' or 'feet'")
        self.anchor = anchor

    def update_from_context(self, other: ExecutionContext) -> None:
        """Update this context from another context.

        This is used when applying multiple execute subcommands in sequence.
        Each subcommand modifies the context, and this method helps apply
        those modifications.

        Args:
            other: The context to copy properties from
        """
        self.executor = other.executor
        self.position = other.position
        self.rotation = other.rotation
        self.dimension = other.dimension
        self.anchor = other.anchor
        # Note: success and result are typically not inherited when updating
        # from subcommands, as they represent the result of command execution

    def clone(self) -> ExecutionContext:
        """Create a complete copy of this context.

        Returns:
            A new ExecutionContext with identical values
        """
        return ExecutionContext(
            executor=self.executor,
            position=self.position,
            rotation=self.rotation,
            dimension=self.dimension,
            anchor=self.anchor,
            success=self.success,
            result=self.result
        )

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"ExecutionContext("
            f"executor={self.executor!r}, "
            f"position={self.position}, "
            f"rotation={self.rotation}, "
            f"dimension={self.dimension!r}, "
            f"anchor={self.anchor!r}, "
            f"success={self.success}, "
            f"result={self.result})"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return (
            f"Executor: {self.executor}\n"
            f"Position: {self.position}\n"
            f"Rotation: {self.rotation}\n"
            f"Dimension: {self.dimension}\n"
            f"Anchor: {self.anchor}\n"
            f"Success: {self.success}\n"
            f"Result: {self.result}"
        )