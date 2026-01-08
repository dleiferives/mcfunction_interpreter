"""Minecraft function execution and state management."""

# Type-only imports for forward references
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcfunction.interpreter.context import ExecutionContext
    from mcfunction.interpreter.executor import execute_command, execute_function

from mcfunction.interpreter.state import GameState

__all__ = ["GameState", "ExecutionContext", "execute_command", "execute_function"]
