"""CLI module for mcfunction interpreter.

Provides command-line interface for:
- Loading datapacks and executing functions
- Interactive REPL with commands for testing and debugging
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from mcfunction.datapack import DataPack, load_datapack
from mcfunction.interpreter.context import ExecutionContext
from mcfunction.interpreter.executor import Interpreter
from mcfunction.interpreter.state import GameState
from mcfunction.parser import parse_command_from_tokens, tokenize


def load_functions_from_datapack(datapack: DataPack) -> dict[str, list]:
    """Load all functions from a datapack into the interpreter.

    Args:
        datapack: The loaded datapack

    Returns:
        Dictionary mapping function paths to parsed command lists
    """
    functions = {}

    for namespace in datapack.namespaces:
        functions_dir = Path(datapack.path) / "data" / namespace / "functions"

        if not functions_dir.exists():
            continue

        # Find all .mcfunction files recursively
        for mcfunction_file in functions_dir.rglob("*.mcfunction"):
            # Calculate function path relative to functions dir
            relative_path = mcfunction_file.relative_to(functions_dir)
            # Remove .mcfunction extension and convert path separators
            function_path = str(relative_path.with_suffix("")).replace(os.sep, "/")
            full_path = f"{namespace}:{function_path}"

            try:
                commands = load_function_from_file(mcfunction_file)
                functions[full_path] = commands
            except Exception as e:
                print(f"[WARN] Failed to load function {full_path}: {e}")

    return functions


def load_function_from_file(file_path: Path) -> list:
    """Load and parse a single .mcfunction file.

    Args:
        file_path: Path to the .mcfunction file

    Returns:
        List of parsed command AST nodes
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    commands = []
    for line in content.splitlines():
        # Skip empty lines and comments
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        try:
            # Tokenize the command
            tokens = tokenize(line)
            if not tokens:
                continue

            # Filter out whitespace tokens for parse_command_from_tokens
            non_ws_tokens = [t for t in tokens if t.type != 'WHITESPACE']
            if not non_ws_tokens:
                continue

            # Parse the command
            command = parse_command_from_tokens(non_ws_tokens)
            if command:
                commands.append(command)
        except Exception as e:
            print(f"[WARN] Failed to parse command '{line}': {e}")

    return commands


def run_file(datapack_path: str, function_path: str) -> None:
    """Execute a function from a datapack and print execution trace.

    Args:
        datapack_path: Path to the datapack directory
        function_path: Function path in format "namespace:function_name"
    """
    try:
        print(f"Loading datapack from: {datapack_path}")
        datapack = load_datapack(datapack_path)

        print(f"Loaded datapack: {datapack.description}")
        print(f"Format version: {datapack.format}")
        print(f"Namespaces: {', '.join(datapack.namespaces)}")
        print()

        # Load all functions from the datapack
        functions = load_functions_from_datapack(datapack)
        print(f"Loaded {len(functions)} functions")

        # Verify the requested function exists
        if function_path not in functions:
            print(f"[ERROR] Function not found: {function_path}")
            print(f"Available functions: {', '.join(sorted(functions.keys()))}")
            return

        print(f"Executing function: {function_path}")
        print("=" * 60)

        # Set up interpreter and game state
        interpreter = Interpreter(functions)
        state = GameState()
        context = ExecutionContext()

        # Execute the function
        interpreter.execute_function(state, context, function_path)

        # Print execution statistics
        interpreter.print_statistics()

    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
    except ValueError as e:
        print(f"[ERROR] {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


def repl() -> None:
    """Interactive REPL for testing mcfunction commands."""
    print("=" * 60)
    print("MCFUNCTION INTERPRETER - INTERACTIVE REPL")
    print("=" * 60)
    print("Available commands:")
    print("  >>> <command>          - Execute a command directly")
    print("  >>> load <path>        - Load a datapack")
    print("  >>> run <function>     - Run a loaded function")
    print("  >>> scoreboard         - Show scoreboard state")
    print("  >>> storage            - Show storage state")
    print("  >>> stats              - Show execution statistics")
    print("  >>> reset              - Reset game state and interpreter")
    print("  >>> quit / exit        - Exit the REPL")
    print("=" * 60)
    print()

    # REPL state
    interpreter: Optional[Interpreter] = None
    state = GameState()
    context = ExecutionContext()
    loaded_datapack: Optional[DataPack] = None

    while True:
        try:
            # Get input with prompt
            user_input = input(">>> ").strip()

            # Handle empty input
            if not user_input:
                continue

            # Handle exit commands
            if user_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                break

            # Handle load command
            if user_input.startswith("load "):
                datapack_path = user_input[5:].strip()
                try:
                    print(f"Loading datapack: {datapack_path}")
                    loaded_datapack = load_datapack(datapack_path)
                    print(f"✓ Loaded: {loaded_datapack.description}")
                    print(f"  Format: {loaded_datapack.format}")
                    print(f"  Namespaces: {', '.join(loaded_datapack.namespaces)}")

                    # Load functions
                    functions = load_functions_from_datapack(loaded_datapack)
                    interpreter = Interpreter(functions)
                    print(f"  Functions loaded: {len(functions)}")
                except Exception as e:
                    print(f"[ERROR] Failed to load datapack: {e}")
                continue

            # Handle run command
            if user_input.startswith("run "):
                if not interpreter:
                    print("[ERROR] No datapack loaded. Use 'load <path>' first.")
                    continue

                function_path = user_input[4:].strip()
                try:
                    print(f"Running function: {function_path}")
                    interpreter.execute_function(state, context, function_path)
                    interpreter.print_statistics()
                except Exception as e:
                    print(f"[ERROR] Function execution failed: {e}")
                continue

            # Handle scoreboard display
            if user_input == "scoreboard":
                print("\nSCOREBOARD STATE:")
                print("-" * 40)

                if not state.scoreboards.objectives:
                    print("  No objectives")
                else:
                    print("  Objectives:")
                    for name, (criteria, display) in state.scoreboards.objectives.items():
                        display_name = f" ({display})" if display else ""
                        print(f"    {name}{display_name}: {criteria}")

                if state.scoreboards.display_slots:
                    print("\n  Display slots:")
                    for slot, objective in state.scoreboards.display_slots.items():
                        print(f"    {slot}: {objective or '(empty)'}")

                if state.scoreboards.scores:
                    print("\n  Scores:")
                    for (player, objective), score in state.scoreboards.scores.items():
                        print(f"    {player} [{objective}]: {score}")
                else:
                    print("  No scores set")
                continue

            # Handle storage display
            if user_input == "storage":
                print("\nSTORAGE STATE:")
                print("-" * 40)

                if not state.storage.storage:
                    print("  No storage data")
                else:
                    for (namespace, path), data in state.storage.storage.items():
                        print(f"  {namespace}:{path}")
                        # Pretty print NBT data
                        print(f"    {data}")
                continue

            # Handle stats display
            if user_input == "stats":
                if interpreter:
                    interpreter.print_statistics()
                else:
                    print("[INFO] No interpreter active. Load a datapack first.")
                continue

            # Handle reset
            if user_input == "reset":
                print("Resetting game state and interpreter...")
                interpreter = None
                state = GameState()
                context = ExecutionContext()
                loaded_datapack = None
                print("✓ Reset complete")
                continue

            # Direct command execution
            # Try to parse and execute the input as a command
            try:
                tokens = tokenize(user_input)
                if not tokens:
                    print("[ERROR] Empty command")
                    continue

                # Filter out whitespace tokens
                non_ws_tokens = [t for t in tokens if t.type != 'WHITESPACE']
                if not non_ws_tokens:
                    print("[ERROR] Empty command after filtering")
                    continue

                command = parse_command_from_tokens(non_ws_tokens)

                if interpreter is None:
                    interpreter = Interpreter()

                # Execute the command
                interpreter.execute_command(state, context, command)

                print("✓ Command executed successfully")

            except Exception as e:
                print(f"[ERROR] Failed to parse/execute command: {e}")
                print(f"  Error type: {type(e).__name__}")

        except KeyboardInterrupt:
            print("\n[Interrupted] Use 'quit' to exit gracefully")
        except EOFError:
            print("\nEOF received. Goodbye!")
            break
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")


def main() -> None:
    """Main CLI entry point for the mcfun command."""
    if len(sys.argv) == 1:
        # No arguments - start REPL
        repl()
        return

    # Handle help flags
    if sys.argv[1] in ("-h", "--help", "help"):
        print("MCFUNCTION INTERPRETER")
        print("=" * 40)
        print("Usage:")
        print("  mcfun                                    Start interactive REPL")
        print("  mcfun repl                              Start interactive REPL")
        print("  mcfun run <datapack_path> [function]    Run specific function")
        print("  mcfun <datapack_path> [function]        Shorthand run")
        print()
        print("Examples:")
        print("  mcfun test_datapack test:load")
        print("  python -m mcfunction.cli run test_datapack test:load")
        return

    if sys.argv[1] == "repl":
        repl()
    elif sys.argv[1] == "run" and len(sys.argv) >= 3:
        run_file(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "minecraft:load")
    elif sys.argv[1] not in ("repl", "run"):
        # Assume it's a datapack path with optional function path
        datapack_path = sys.argv[1]
        function_path = sys.argv[2] if len(sys.argv) > 2 else "minecraft:load"
        run_file(datapack_path, function_path)
    else:
        print("Use 'mcfun --help' for usage information")


if __name__ == "__main__":
    main()
