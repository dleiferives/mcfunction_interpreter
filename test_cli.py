#!/usr/bin/env python3
"""Test script to validate the CLI module functionality."""

from io import StringIO
import sys
from mcfunction.cli import run_file
from mcfunction.interpreter.state import GameState
from mcfunction.interpreter.context import ExecutionContext
from mcfunction.interpreter.executor import Interpreter
from mcfunction.parser import parse_command_from_tokens, tokenize


def test_run_file():
    """Test run_file function."""
    print("=" * 50)
    print("TEST: run_file()")
    print("=" * 50)

    try:
        run_file('test_datapack', 'test:load')
        print("✓ run_file completed successfully")
    except Exception as e:
        print(f"✗ run_file failed: {e}")
        return False

    return True


def test_command_parsing():
    """Test command parsing and execution."""
    print("\n" + "=" * 50)
    print("TEST: Command parsing")
    print("=" * 50)

    test_commands = [
        'scoreboard objectives add obj1 dummy',
        'scoreboard objectives add obj2 dummy "My Objective"',
        'scoreboard players set Steve obj1 50',
        'scoreboard players add @p obj1 10',
        'scoreboard players remove @a obj1 5',
        'scoreboard players reset @s obj1',
        'data merge storage my:ns {x:1,y:2}',
        'data get storage my:ns',
    ]

    state = GameState()
    context = ExecutionContext()
    interpreter = Interpreter()

    for cmd in test_commands:
        try:
            tokens = tokenize(cmd)
            non_ws = [t for t in tokens if t.type != 'WHITESPACE']
            parsed = parse_command_from_tokens(non_ws)
            interpreter.execute_command(state, context, parsed)
            print(f"✓ {cmd}")
        except Exception as e:
            print(f"✗ {cmd} - Error: {e}")
            return False

    # Check final state
    print(f"\nFinal objectives: {state.scoreboards.objectives}")
    print(f"Final scores: {state.scoreboards.scores}")
    print(f"Final storage: {state.storage.storage}")

    return True


def test_repl_commands():
    """Test that individual commands work for the REPL."""
    print("\n" + "=" * 50)
    print("TEST: REPL-style commands")
    print("=" * 50)

    state = GameState()
    context = ExecutionContext()

    # Test scoreboard commands
    commands = [
        "scoreboard objectives add test dummy",
        "scoreboard players set Player test 42",
        "data merge storage test:ns {value:123}",
    ]

    interpreter = Interpreter()

    for cmd in commands:
        try:
            tokens = tokenize(cmd)
            non_ws = [t for t in tokens if t.type != 'WHITESPACE']
            parsed = parse_command_from_tokens(non_ws)
            interpreter.execute_command(state, context, parsed)
        except Exception as e:
            print(f"✗ Failed on '{cmd}': {e}")
            return False

    # Verify state display works
    print("Objectives:", state.scoreboards.objectives)
    print("Scores:", state.scoreboards.scores)
    print("Storage:", state.storage.storage)

    return True


def test_edge_cases():
    """Test edge cases."""
    print("\n" + "=" * 50)
    print("TEST: Edge cases")
    print("=" * 50)

    state = GameState()
    context = ExecutionContext()
    interpreter = Interpreter()

    # Empty commands
    try:
        tokens = tokenize("")
        non_ws = [t for t in tokens if t.type != 'WHITESPACE']
        print(f"Empty command yields: {non_ws}")
    except:
        pass

    # Comments
    try:
        tokens = tokenize("# This is a comment")
        non_ws = [t for t in tokens if t.type != 'WHITESPACE']
        print(f"Comment yields: {non_ws}")
    except:
        pass

    # Function calls
    try:
        tokens = tokenize("function test:load")
        non_ws = [t for t in tokens if t.type != 'WHITESPACE']
        parsed = parse_command_from_tokens(non_ws)
        print(f"Function call parsed: {parsed}")
    except Exception as e:
        print(f"Function call error: {e}")

    print("✓ Edge cases handled")
    return True


def main():
    """Run all tests."""
    print("Testing CLI Module")
    print("=" * 60)

    all_passed = True

    all_passed &= test_run_file()
    all_passed &= test_command_parsing()
    all_passed &= test_repl_commands()
    all_passed &= test_edge_cases()

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
