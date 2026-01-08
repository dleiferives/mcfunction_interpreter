"""Minecraft mcfunction datapack interpreter.

A Python interpreter for executing Minecraft datapack functions with support
for scoreboard operations, data storage, execute commands, and function calls.
"""

__version__ = "0.1.0"

from mcfunction.parser.nbt import parse_snbt
from mcfunction.parser.selector import parse_selector

__all__ = ["parse_snbt", "parse_selector"]
