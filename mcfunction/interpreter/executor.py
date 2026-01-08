"""Minecraft command executor module.

This module provides the main execution engine for Minecraft commands,
including command dispatch, function execution, and statistics tracking.
"""

from __future__ import annotations

import sys
from typing import Optional

from mcfunction.interpreter.builtins import (
    exec_data_get,
    exec_data_merge,
    exec_data_modify,
    exec_data_remove,
    exec_execute_chain,
    exec_execute_run,
    exec_scoreboard_objectives_add,
    exec_scoreboard_objectives_list,
    exec_scoreboard_objectives_remove,
    exec_scoreboard_objectives_setdisplay,
    exec_scoreboard_players_add,
    exec_scoreboard_players_operation,
    exec_scoreboard_players_remove,
    exec_scoreboard_players_reset,
    exec_scoreboard_players_set,
    exec_say,
    exec_tellraw,
)
from mcfunction.interpreter.context import ExecutionContext
from mcfunction.interpreter.state import GameState
from mcfunction.parser.commands import (
    Command,
    DataGet,
    DataMerge,
    DataModify,
    DataRemove,
    Execute,
    FunctionCall,
    ScoreboardObjectivesAdd,
    ScoreboardObjectivesList,
    ScoreboardObjectivesRemove,
    ScoreboardObjectivesSetDisplay,
    ScoreboardPlayersAdd,
    ScoreboardPlayersOperation,
    ScoreboardPlayersRemove,
    ScoreboardPlayersReset,
    ScoreboardPlayersSet,
    Say,
    Tellraw,
)


class ExecutionStatistics:
    """Tracks execution statistics for commands and functions."""

    def __init__(self):
        """Initialize empty statistics."""
        self.total_commands: int = 0
        self.unknown_commands: int = 0
        self.successful_commands: int = 0
        self.function_calls: int = 0
        self.max_recursion_depth: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage."""
        if self.total_commands == 0:
            return 0.0
        return (self.successful_commands / self.total_commands) * 100.0

    def increment_total(self) -> None:
        """Increment total command counter."""
        self.total_commands += 1

    def increment_unknown(self) -> None:
        """Increment unknown command counter."""
        self.unknown_commands += 1

    def increment_success(self) -> None:
        """Increment successful command counter."""
        self.successful_commands += 1

    def increment_function_calls(self) -> None:
        """Increment function call counter."""
        self.function_calls += 1

    def update_max_depth(self, depth: int) -> None:
        """Update max recursion depth if new depth is greater."""
        if depth > self.max_recursion_depth:
            self.max_recursion_depth = depth

    def __repr__(self) -> str:
        """String representation of statistics."""
        return (
            f"ExecutionStatistics("
            f"total={self.total_commands}, "
            f"unknown={self.unknown_commands}, "
            f"success_rate={self.success_rate:.1f}%, "
            f"function_calls={self.function_calls}, "
            f"max_depth={self.max_recursion_depth})"
        )


class FunctionRegistry:
    """Registry for storing and retrieving loaded functions."""

    def __init__(self):
        """Initialize empty function registry."""
        # Maps function_path -> list of command AST nodes
        self.functions: dict[str, list[Command]] = {}

    def load_function(self, function_path: str, commands: list[Command]) -> None:
        """Load a function into the registry.

        Args:
            function_path: The function path (e.g., "minecraft:tick", "my_ns:loop")
            commands: List of parsed command AST nodes
        """
        self.functions[function_path] = commands

    def get_function(self, function_path: str) -> Optional[list[Command]]:
        """Get a function's commands from the registry.

        Args:
            function_path: The function path to retrieve

        Returns:
            List of commands, or None if not found
        """
        return self.functions.get(function_path)

    def has_function(self, function_path: str) -> bool:
        """Check if a function exists in the registry.

        Args:
            function_path: The function path to check

        Returns:
            True if function exists, False otherwise
        """
        return function_path in self.functions

    def __repr__(self) -> str:
        """String representation."""
        return f"FunctionRegistry({len(self.functions)} functions)"


class FunctionCallStack:
    """Manages the function call stack with recursion detection."""

    MAX_DEPTH = 100

    def __init__(self):
        """Initialize empty call stack."""
        self.stack: list[str] = []

    def push(self, function_path: str) -> bool:
        """Push a function onto the call stack.

        Args:
            function_path: The function path being called

        Returns:
            True if push succeeded, False if would exceed max depth
        """
        # Check recursion depth
        current_depth = len(self.stack)
        if current_depth >= self.MAX_DEPTH:
            return False

        # Check for recursion (same function already on stack)
        if function_path in self.stack:
            # Still allow it but track it as potential issue
            pass

        self.stack.append(function_path)
        return True

    def pop(self) -> Optional[str]:
        """Pop the top function from the call stack.

        Returns:
            The popped function path, or None if stack is empty
        """
        if self.stack:
            return self.stack.pop()
        return None

    def depth(self) -> int:
        """Get current call stack depth."""
        return len(self.stack)

    def peek(self) -> Optional[str]:
        """Get the current function at the top of the stack."""
        if self.stack:
            return self.stack[-1]
        return None

    def is_empty(self) -> bool:
        """Check if the call stack is empty."""
        return len(self.stack) == 0

    def clear(self) -> None:
        """Clear the entire call stack."""
        self.stack.clear()


# Global execution context for the interpreter
class Interpreter:
    """Main interpreter class that manages execution state and configuration."""

    def __init__(self, functions: Optional[dict[str, list[Command]]] = None):
        """Initialize the interpreter.

        Args:
            functions: Optional dictionary of function_path -> commands to preload
        """
        self.registry = FunctionRegistry()
        if functions:
            for path, cmds in functions.items():
                self.registry.load_function(path, cmds)

        self.call_stack = FunctionCallStack()
        self.statistics = ExecutionStatistics()

    def execute_command(
        self,
        state: GameState,
        context: ExecutionContext,
        command: Command
    ) -> None:
        """Execute a single command.

        This is the main dispatch function that routes commands to their
        appropriate builtin executors.

        Args:
            state: The current game state
            context: The execution context
            command: The command AST node to execute
        """
        self.statistics.increment_total()

        try:
            # Dispatch based on command type
            if isinstance(command, ScoreboardObjectivesAdd):
                exec_scoreboard_objectives_add(
                    state, command.objective, command.criteria, command.display_name
                )
                self.statistics.increment_success()

            elif isinstance(command, ScoreboardObjectivesRemove):
                exec_scoreboard_objectives_remove(state, command.objective)
                self.statistics.increment_success()

            elif isinstance(command, ScoreboardObjectivesList):
                exec_scoreboard_objectives_list(state)
                self.statistics.increment_success()

            elif isinstance(command, ScoreboardObjectivesSetDisplay):
                exec_scoreboard_objectives_setdisplay(
                    state, command.slot, command.objective
                )
                self.statistics.increment_success()

            elif isinstance(command, ScoreboardPlayersSet):
                exec_scoreboard_players_set(
                    state, command.targets, command.objective, command.score
                )
                self.statistics.increment_success()

            elif isinstance(command, ScoreboardPlayersAdd):
                exec_scoreboard_players_add(
                    state, command.targets, command.objective, command.score
                )
                self.statistics.increment_success()

            elif isinstance(command, ScoreboardPlayersRemove):
                exec_scoreboard_players_remove(
                    state, command.targets, command.objective, command.score
                )
                self.statistics.increment_success()

            elif isinstance(command, ScoreboardPlayersReset):
                exec_scoreboard_players_reset(
                    state, command.targets, command.objective
                )
                self.statistics.increment_success()

            elif isinstance(command, ScoreboardPlayersOperation):
                exec_scoreboard_players_operation(
                    state,
                    command.targets,
                    command.target_objective,
                    command.operation,
                    command.source,
                    command.source_objective,
                )
                self.statistics.increment_success()

            elif isinstance(command, DataGet):
                result = exec_data_get(state, command.target, command.path)
                # Store result in context for potential store operations
                context.result = 0  # Simplified - would convert NBT to int
                context.success = True
                self.statistics.increment_success()

            elif isinstance(command, DataMerge):
                exec_data_merge(state, command.target, command.nbt)
                self.statistics.increment_success()

            elif isinstance(command, DataModify):
                exec_data_modify(
                    state,
                    command.target,
                    command.path,
                    command.operation,
                    command.source,
                    command.value,
                    command.index,
                )
                self.statistics.increment_success()

            elif isinstance(command, DataRemove):
                exec_data_remove(state, command.target, command.path)
                self.statistics.increment_success()

            elif isinstance(command, Execute):
                # Execute command chain
                contexts = exec_execute_chain(state, context, command)
                # Execute the final command for each context
                if command.command:
                    exec_execute_run(state, contexts, command.command)
                self.statistics.increment_success()

            elif isinstance(command, FunctionCall):
                # Execute function call - use internal method to avoid double error handling
                self._execute_function(state, context, command.function_path)
                self.statistics.increment_success()

            elif isinstance(command, Say):
                exec_say(state, command.message)
                self.statistics.increment_success()

            elif isinstance(command, Tellraw):
                exec_tellraw(state, command.targets, command.message)
                self.statistics.increment_success()

            else:
                # Unknown command type
                self._handle_unknown_command(command)

        except (RecursionError, ValueError) as e:
            # Critical errors that should propagate
            # RecursionError: Function recursion depth exceeded
            # ValueError: Critical issues like missing functions
            raise
        except Exception as e:
            # Command execution failed but non-critical
            # We still consider it "executed" but not successful
            # For this interpreter, we'll print the error and continue
            print(f"[ERROR] Command execution failed: {e}")
            # Don't increment success, but don't mark as unknown either

    def execute_function(
        self,
        state: GameState,
        context: ExecutionContext,
        function_path: str
    ) -> None:
        """Execute a function by path with full error handling.

        This is the user-facing method that catches exceptions and tracks statistics.
        It calls the internal _execute_function method for the actual execution.

        Args:
            state: The current game state
            context: The execution context
            function_path: The function path to execute (e.g., "minecraft:tick")

        Raises:
            RecursionError: If maximum recursion depth is exceeded
            ValueError: If the function is not found
        """
        try:
            self._execute_function(state, context, function_path)
        except Exception as e:
            # Handle execution errors
            print(f"[ERROR] Function execution failed: {e}")
            raise

    def _execute_function(
        self,
        state: GameState,
        context: ExecutionContext,
        function_path: str
    ) -> None:
        """Execute a function by path (internal implementation).

        This function manages the call stack, checks for recursion depth,
        and executes all commands in the function sequentially.

        Args:
            state: The current game state
            context: The execution context
            function_path: The function path to execute (e.g., "minecraft:tick")

        Raises:
            RecursionError: If maximum recursion depth is exceeded
            ValueError: If the function is not found
        """
        self.statistics.increment_function_calls()

        # Check call stack depth before pushing
        current_depth = self.call_stack.depth()
        self.statistics.update_max_depth(current_depth)

        # Push onto call stack
        if not self.call_stack.push(function_path):
            raise RecursionError(
                f"Maximum function recursion depth exceeded ({self.call_stack.MAX_DEPTH}). "
                f"Call stack: {' -> '.join(self.call_stack.stack)} -> {function_path}"
            )

        try:
            # Get function commands
            commands = self.registry.get_function(function_path)
            if commands is None:
                raise ValueError(f"Function not found: {function_path}")

            # Execute each command in the function
            for command in commands:
                self.execute_command(state, context, command)

        finally:
            # Always pop from stack, even on error
            self.call_stack.pop()

    def _handle_unknown_command(self, command: Command) -> None:
        """Handle an unknown or unsupported command type.

        Args:
            command: The unknown command
        """
        self.statistics.increment_unknown()

        # Get command type name for logging
        command_type = type(command).__name__
        print(f"[WARN] Unknown command: {command_type}")
        print(f"       Command data: {command}")

    def load_function(self, function_path: str, commands: list[Command]) -> None:
        """Load a function into the interpreter's registry.

        Args:
            function_path: The function path
            commands: List of parsed command AST nodes
        """
        self.registry.load_function(function_path, commands)

    def get_statistics(self) -> ExecutionStatistics:
        """Get current execution statistics.

        Returns:
            The current execution statistics
        """
        return self.statistics

    def print_statistics(self) -> None:
        """Print execution statistics to console."""
        stats = self.statistics
        print("\n" + "=" * 60)
        print("EXECUTION STATISTICS")
        print("=" * 60)
        print(f"Total commands executed: {stats.total_commands}")
        print(f"Successful commands:     {stats.successful_commands}")
        print(f"Unknown commands:        {stats.unknown_commands}")
        print(f"Success rate:            {stats.success_rate:.1f}%")
        print(f"Function calls:          {stats.function_calls}")
        print(f"Max recursion depth:     {stats.max_recursion_depth}")
        print("=" * 60)

    def reset_statistics(self) -> None:
        """Reset all execution statistics."""
        self.statistics = ExecutionStatistics()


# Convenience functions for backward compatibility with task requirements
def execute_command(
    state: GameState,
    context: ExecutionContext,
    command: Command
) -> None:
    """Execute a single command.

    This is the main entry point for command execution that dispatches
    to the appropriate builtin executors.

    Args:
        state: The current game state
        context: The execution context
        command: The command AST node to execute
    """
    # Create a minimal interpreter for single command execution
    interpreter = Interpreter()
    interpreter.execute_command(state, context, command)


def execute_function(
    state: GameState,
    context: ExecutionContext,
    function_path: str,
    registry: Optional[FunctionRegistry] = None
) -> None:
    """Execute a function by path with call stack management.

    This function provides the main entry point for function execution
    with recursion detection and call stack management.

    Args:
        state: The current game state
        context: The execution context
        function_path: The function path to execute
        registry: Optional function registry to use (creates temporary one if None)

    Raises:
        RecursionError: If maximum recursion depth (100) is exceeded
        ValueError: If the function is not found
    """
    if registry is None:
        registry = FunctionRegistry()

    interpreter = Interpreter()
    interpreter.registry = registry
    # Use internal method to propagate errors properly
    interpreter._execute_function(state, context, function_path)


# Create default interpreter instance for convenience
_default_interpreter = Interpreter()


def get_default_interpreter() -> Interpreter:
    """Get the default interpreter instance.

    Returns:
        The default Interpreter instance
    """
    return _default_interpreter
