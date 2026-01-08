"""Function and execute command parsers for Minecraft commands.

This module provides parsers for:
- function calls: function <namespace:path>
- execute commands with full subcommand chain parsing including:
  - as <selector>
  - at <selector>
  - align <axes>
  - anchored <anchor>
  - facing <pos|selector> [eyes|feet]
  - in <dimension>
  - on <target>
  - positioned <pos|selector>
  - rotated <rot|selector>
  - summon <entity>
  - if/unless conditions (block, data, entity, score)
  - store result/success
  - run <command>
"""

from __future__ import annotations

from typing import Optional, Union, Any

from mcfunction.parser.commands import (
    FunctionCall,
    Execute,
    ExecuteAs,
    ExecuteAt,
    ExecuteAlign,
    ExecuteAnchored,
    ExecuteFacing,
    ExecuteIf,
    ExecuteUnless,
    ExecutePositioned,
    ExecuteRotated,
    ExecuteStore,
    ExecuteIn,
    ExecuteOn,
    ExecuteSummon,
    ExecuteSubcommand,
    # Import all command types for the Execute.command field
    ScoreboardObjectivesAdd,
    ScoreboardObjectivesRemove,
    ScoreboardObjectivesList,
    ScoreboardObjectivesSetDisplay,
    ScoreboardPlayersSet,
    ScoreboardPlayersAdd,
    ScoreboardPlayersRemove,
    ScoreboardPlayersReset,
    ScoreboardPlayersOperation,
    DataGet,
    DataMerge,
    DataModify,
    DataRemove,
)
from mcfunction.parser.lexer import tokenize_compact, TokenType
from mcfunction.parser.selector import parse_selector, EntitySelector


class ExecuteParser:
    """Parser for execute command chains."""

    def __init__(self, tokens):
        """Initialize parser with token list."""
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset: int = 0) -> Optional[str]:
        """Peek at token value at offset from current position."""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx].value
        return None

    def peek_type(self, offset: int = 0) -> Optional[str]:
        """Peek at token type at offset from current position."""
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx].type
        return None

    def consume(self) -> str:
        """Consume and return current token value."""
        if self.pos < len(self.tokens):
            val = self.tokens[self.pos].value
            self.pos += 1
            return val
        raise ValueError("Unexpected end of tokens")

    def consume_if(self, expected_value: str) -> bool:
        """Consume token if it matches expected value, return True if consumed."""
        if self.peek() == expected_value:
            self.consume()
            return True
        return False

    def expect(self, expected_value: str) -> str:
        """Expect and consume a specific token value."""
        if self.peek() != expected_value:
            raise ValueError(f"Expected '{expected_value}', got '{self.peek()}'")
        return self.consume()

    def parse_selector(self) -> EntitySelector:
        """Parse and validate a selector token."""
        token_type = self.peek_type()
        value = self.peek()

        if token_type != TokenType.SELECTOR:
            raise ValueError(f"Expected selector, got '{value}' (type: {token_type})")

        selector = self.consume()
        try:
            return parse_selector(selector)
        except ValueError as e:
            raise ValueError(f"Invalid selector '{selector}': {e}")

    def parse_coordinates(self) -> tuple[float, float, float]:
        """Parse x, y, z coordinates."""
        coords = []
        for _ in range(3):
            token_type = self.peek_type()
            value = self.peek()

            if token_type in (TokenType.INTEGER, TokenType.FLOAT):
                try:
                    coords.append(float(self.consume()))
                except ValueError:
                    raise ValueError(f"Invalid coordinate value: '{value}'")
            elif token_type in (TokenType.COORDINATE_RELATIVE, TokenType.COORDINATE_LOCAL):
                # Handle ~, ~5, ^, ^2.5
                coord_str = self.consume()
                if coord_str in ("~", "^"):
                    coords.append(0.0)  # Relative to current position
                else:
                    # Has offset
                    offset = coord_str[1:]
                    if offset:
                        try:
                            coords.append(float(offset))
                        except ValueError:
                            raise ValueError(f"Invalid coordinate offset: '{coord_str}'")
                    else:
                        coords.append(0.0)
            else:
                raise ValueError(f"Expected coordinate, got '{value}' (type: {token_type})")

        return tuple(coords)

    def parse_rotation(self) -> tuple[Optional[float], Optional[float]]:
        """Parse yaw and pitch rotation."""
        yaw = None
        pitch = None

        # Parse yaw
        token_type = self.peek_type()
        value = self.peek()

        if token_type in (TokenType.INTEGER, TokenType.FLOAT):
            yaw = float(self.consume())
        else:
            raise ValueError(f"Expected rotation value, got '{value}' (type: {token_type})")

        # Parse pitch (if present)
        if self.pos < len(self.tokens):
            token_type = self.peek_type()
            if token_type in (TokenType.INTEGER, TokenType.FLOAT):
                pitch = float(self.consume())

        return yaw, pitch

    def parse_axes(self) -> str:
        """Parse alignment axes like 'xyz', 'xy', 'xz', etc."""
        value = self.peek()
        if not value or len(value) not in [2, 3]:
            raise ValueError(f"Invalid axes: '{value}'. Expected 2-3 characters from 'xyz'")

        # Validate axes are x, y, z
        valid_axes = set('xyz')
        if not all(c in valid_axes for c in value):
            raise ValueError(f"Invalid axes: '{value}'. Must be from 'xyz'")

        # Check for duplicates
        if len(set(value)) != len(value):
            raise ValueError(f"Duplicate axes in '{value}'")

        # Ensure order is x, y, z
        expected = ''.join(sorted(value))
        if value != expected:
            raise ValueError(f"Axes must be in sorted order: xyz, xy, xz, yz. Got '{value}'")

        return self.consume()

    def parse_anchor(self) -> str:
        """Parse anchor type 'eyes' or 'feet'."""
        value = self.peek()
        if value not in ("eyes", "feet"):
            raise ValueError(f"Invalid anchor '{value}'. Expected 'eyes' or 'feet'")
        return self.consume()

    def parse_dimension(self) -> str:
        """Parse dimension like 'overworld', 'the_nether', 'the_end'."""
        token_type = self.peek_type()
        value = self.peek()

        if token_type not in (TokenType.IDENTIFIER, TokenType.RESOURCE_LOCATION, TokenType.KEYWORD):
            raise ValueError(f"Expected dimension, got '{value}' (type: {token_type})")

        return self.consume()

    def parse_if_unless_condition(self, keyword: str) -> Union[ExecuteIf, ExecuteUnless]:
        """Parse if/unless conditions."""
        condition_type = self.peek()
        condition_args = {}

        if condition_type == "block":
            self.consume()
            # block <x> <y> <z> <block>
            coords = self.parse_coordinates()
            block = self.consume()
            condition_args = {
                "x": coords[0],
                "y": coords[1],
                "z": coords[2],
                "block": block,
            }

        elif condition_type == "data":
            self.consume()
            # data <source> <path>
            source_type = self.consume()
            if source_type not in ("storage", "entity", "block"):
                raise ValueError(f"Invalid data source: '{source_type}'")

            if source_type == "storage":
                storage_path = self.consume()
                location = f"storage {storage_path}"
            elif source_type == "entity":
                selector = self.parse_selector()
                location = f"entity {selector}"
            else:  # block
                coords = self.parse_coordinates()
                location = f"block {coords[0]} {coords[1]} {coords[2]}"

            # Parse NBT path
            path_tokens = []
            while self.pos < len(self.tokens):
                token = self.peek()
                if token in ("run", "as", "at", "align", "anchored", "facing",
                            "in", "on", "positioned", "rotated", "summon",
                            "if", "unless", "store"):
                    break
                path_tokens.append(self.consume())

            if not path_tokens:
                raise ValueError("Expected NBT path")

            condition_args = {
                "source": location,
                "path": "".join(path_tokens),
            }

        elif condition_type == "entity":
            self.consume()
            selector = self.parse_selector()
            condition_args = {"selector": selector}

        elif condition_type == "score":
            self.consume()
            # score <target> <targetObjective> <operator> <value|source> [<sourceObjective>]
            target = self.parse_selector_or_name()
            target_obj = self.consume()
            operator = self.parse_comparison_operator()

            # Check if it's 'matches' (always followed by value) or value vs source
            if operator == "matches":
                # matches <value> (e.g., matches 1.., matches 5, matches ..10)
                source_value = self.peek()
                if source_value is None:
                    raise ValueError("Expected value after 'matches'")

                # Parse as value or range
                from mcfunction.parser.selector import Range
                # Check if it looks like a range
                if ".." in source_value or source_value.replace("-", "").replace(".", "").isdigit():
                    # This is a value/range, parse it properly
                    # For now, we'll store it as a string since the exact type depends on context
                    source = source_value
                    source_obj = None
                else:
                    source = source_value
                    source_obj = None
                self.consume()
            else:
                # <operator> <source> <sourceObjective>
                # or <operator> <value>
                # Check if next token is a selector
                next_token_type = self.peek_type()
                if next_token_type == TokenType.SELECTOR:
                    source = self.parse_selector_or_name()
                    source_obj = self.consume()
                else:
                    # It's a value
                    source = self.consume()
                    source_obj = None

            condition_args = {
                "target": target,
                "target_objective": target_obj,
                "operator": operator,
                "source": source,
                "source_objective": source_obj,
            }

        else:
            raise ValueError(f"Invalid condition type: '{condition_type}'")

        if keyword == "if":
            return ExecuteIf(condition_type, condition_args)
        else:
            return ExecuteUnless(condition_type, condition_args)

    def parse_selector_or_name(self) -> Union[EntitySelector, str]:
        """Parse a selector or player name."""
        token_type = self.peek_type()

        if token_type == TokenType.SELECTOR:
            return self.parse_selector()
        elif token_type in (TokenType.IDENTIFIER, TokenType.PLAYER_NAME, TokenType.KEYWORD):
            return self.consume()
        else:
            raise ValueError(f"Expected selector or name, got '{self.peek()}'")

    def parse_comparison_operator(self) -> str:
        """Parse comparison operators: <, >, =, <=, >=, matches."""
        value = self.peek()

        # Check for 'matches' keyword
        if value == "matches":
            return self.consume()

        # Check for <=, >=, =, <, >
        if value in ("<", ">", "="):
            self.consume()
            # Check for <= or >=
            if value in ("<", ">") and self.peek() == "=":
                op = value + self.consume()
                return op
            return value

        raise ValueError(f"Invalid comparison operator: '{value}'")

    def parse_store_command(self, keyword: str) -> ExecuteStore:
        """Parse store result/success commands."""
        # Parse 'result' or 'success'
        store_type = self.consume()
        if store_type not in ("result", "success"):
            raise ValueError(f"Expected 'result' or 'success', got '{store_type}'")

        # Parse target type
        target_type = self.consume()
        if target_type not in ("storage", "entity", "block", "bossbar", "score"):
            raise ValueError(f"Invalid store target: '{target_type}'")

        # Parse target and optional path
        target = ""
        path = None
        type_str = None
        scale = None

        if target_type == "storage":
            storage_path = self.consume()
            target = f"storage {storage_path}"
        elif target_type == "entity":
            raw_selector = self.peek()
            selector = self.parse_selector()
            target = f"entity {raw_selector}"
        elif target_type == "block":
            coords = self.parse_coordinates()
            target = f"block {coords[0]} {coords[1]} {coords[2]}"
        elif target_type == "bossbar":
            # bossbar <value> <max|value>
            value = self.consume()
            max_or_value = self.consume()
            target = f"bossbar {value} {max_or_value}"
        elif target_type == "score":
            # score <target> <objective>
            # Get the raw target token before parsing
            raw_target = self.peek()
            target_sel = self.parse_selector_or_name()
            # If it's a selector, raw_target already has the full selector string
            # If it's a player name, it's just the name
            obj = self.consume()
            target = f"score {raw_target} {obj}"

        # Optional: parse NBT path (for storage/entity/block, not for bossbar or score)
        if target_type not in ("bossbar", "score") and self.pos < len(self.tokens):
            # Peek ahead to see if next token is a path or a type keyword
            next_token = self.peek()
            next_type = self.peek_type()

            # If it looks like a path (not a type keyword or end marker)
            if next_type not in (TokenType.KEYWORD, TokenType.SELECTOR) and next_token not in ("run",):
                path_tokens = []
                while self.pos < len(self.tokens):
                    token = self.peek()
                    token_type = self.peek_type()

                    # Stop at keywords that mark next subcommand or end
                    if token in ("run", "as", "at", "align", "anchored", "facing",
                                "in", "on", "positioned", "rotated", "summon",
                                "if", "unless", "store"):
                        break

                    # Stop at type specification
                    if token in ("byte", "short", "int", "long", "float", "double", "var"):
                        break

                    path_tokens.append(self.consume())

                if path_tokens:
                    path = "".join(path_tokens)

        # Optional: parse type and scale
        if self.pos < len(self.tokens):
            type_keywords = ("byte", "short", "int", "long", "float", "double", "var")
            if self.peek() in type_keywords:
                type_str = self.consume()

                # Optional scale
                if self.pos < len(self.tokens):
                    token_type = self.peek_type()
                    if token_type in (TokenType.INTEGER, TokenType.FLOAT):
                        try:
                            scale = float(self.consume())
                        except ValueError:
                            pass

        return ExecuteStore(
            store_type=store_type,
            target=target,
            path=path,
            type=type_str,
            scale=scale
        )

    def parse_execute_subcommand(self) -> Optional[ExecuteSubcommand]:
        """Parse a single execute subcommand."""
        keyword = self.peek()
        if not keyword:
            return None

        subcommands = {
            "as": self._parse_as,
            "at": self._parse_at,
            "align": self._parse_align,
            "anchored": self._parse_anchored,
            "facing": self._parse_facing,
            "in": self._parse_in,
            "on": self._parse_on,
            "positioned": self._parse_positioned,
            "rotated": self._parse_rotated,
            "summon": self._parse_summon,
            "if": self._parse_if,
            "unless": self._parse_unless,
            "store": self._parse_store,
        }

        if keyword in subcommands:
            return subcommands[keyword]()
        else:
            # Not an execute subcommand
            return None

    def _parse_as(self) -> ExecuteAs:
        """Parse 'as <selector>'."""
        self.consume()  # consume 'as'
        selector = self.parse_selector()
        return ExecuteAs(selector)

    def _parse_at(self) -> ExecuteAt:
        """Parse 'at <selector>'."""
        self.consume()  # consume 'at'
        selector = self.parse_selector()
        return ExecuteAt(selector)

    def _parse_align(self) -> ExecuteAlign:
        """Parse 'align <axes>'."""
        self.consume()  # consume 'align'
        axes = self.parse_axes()
        return ExecuteAlign(axes)

    def _parse_anchored(self) -> ExecuteAnchored:
        """Parse 'anchored <anchor>'."""
        self.consume()  # consume 'anchored'
        anchor = self.parse_anchor()
        return ExecuteAnchored(anchor)

    def _parse_facing(self) -> ExecuteFacing:
        """Parse 'facing <pos|selector> [eyes|feet]'."""
        self.consume()  # consume 'facing'

        # Check if it's a selector or coordinates
        if self.peek_type() == TokenType.SELECTOR:
            selector = self.parse_selector()
            anchor = None
            if self.peek() in ("eyes", "feet"):
                anchor = self.consume()
            return ExecuteFacing(target=selector, anchor=anchor)
        else:
            # Parse coordinates
            coords = self.parse_coordinates()
            anchor = None
            if self.peek() in ("eyes", "feet"):
                anchor = self.consume()
            return ExecuteFacing(x=coords[0], y=coords[1], z=coords[2], anchor=anchor)

    def _parse_in(self) -> ExecuteIn:
        """Parse 'in <dimension>'."""
        self.consume()  # consume 'in'
        dimension = self.parse_dimension()
        return ExecuteIn(dimension)

    def _parse_on(self) -> ExecuteOn:
        """Parse 'on <target>'."""
        self.consume()  # consume 'on'
        target = self.consume()

        # Valid targets for 'on'
        valid_targets = {"block", "entity", "bossbar", "storage", "players"}
        if target not in valid_targets:
            raise ValueError(f"Invalid target for 'on': '{target}'. Expected one of {valid_targets}")

        return ExecuteOn(target)

    def _parse_positioned(self) -> ExecutePositioned:
        """Parse 'positioned <pos|selector>'."""
        self.consume()  # consume 'positioned'

        # Check if it's a selector
        if self.peek_type() == TokenType.SELECTOR:
            selector = self.parse_selector()
            return ExecutePositioned(selector)
        else:
            # Parse coordinates
            coords = self.parse_coordinates()
            return ExecutePositioned(None, coords[0], coords[1], coords[2])

    def _parse_rotated(self) -> ExecuteRotated:
        """Parse 'rotated <rot|selector>'."""
        self.consume()  # consume 'rotated'

        # Check if it's a selector
        if self.peek_type() == TokenType.SELECTOR:
            selector = self.parse_selector()
            return ExecuteRotated(selector=selector)
        else:
            # Parse rotation
            yaw, pitch = self.parse_rotation()
            return ExecuteRotated(yaw, pitch)

    def _parse_summon(self) -> ExecuteSummon:
        """Parse 'summon <entity>'."""
        self.consume()  # consume 'summon'
        entity = self.consume()
        return ExecuteSummon(entity)

    def _parse_if(self) -> ExecuteIf:
        """Parse 'if <condition>'."""
        self.consume()  # consume 'if'
        return self.parse_if_unless_condition("if")

    def _parse_unless(self) -> ExecuteUnless:
        """Parse 'unless <condition>'."""
        self.consume()  # consume 'unless'
        return self.parse_if_unless_condition("unless")

    def _parse_store(self) -> ExecuteStore:
        """Parse 'store <result|success> ...'."""
        self.consume()  # consume 'store'
        return self.parse_store_command("store")

    def parse_subcommand_chain(self) -> list[ExecuteSubcommand]:
        """Parse the full chain of execute subcommands."""
        subcommands = []

        while self.pos < len(self.tokens):
            # Check for 'run' keyword which ends the subcommand chain
            if self.peek() == "run":
                break

            subcommand = self.parse_execute_subcommand()
            if subcommand:
                subcommands.append(subcommand)
            else:
                # No more subcommands
                break

        return subcommands

    def parse_run_command(self) -> Any:
        """Parse the command after 'run'."""
        if not self.consume_if("run"):
            raise ValueError("Expected 'run' keyword")

        # Parse remaining tokens as a command
        remaining_tokens = self.tokens[self.pos:]
        if not remaining_tokens:
            return None  # Empty command chain

        return parse_command_from_tokens(remaining_tokens)


def parse_function_call(location: str) -> FunctionCall:
    """Parse a function call command.

    Args:
        location: The function path (e.g., 'minecraft:tick', 'my_namespace:loop')

    Returns:
        FunctionCall AST node

    Raises:
        ValueError: If the function path is invalid

    Examples:
        >>> parse_function_call("minecraft:tick")
        FunctionCall(function_path='minecraft:tick')

        >>> parse_function_call("my_namespace:subdir/function")
        FunctionCall(function_path='my_namespace:subdir/function')
    """
    # Basic validation
    if not location:
        raise ValueError("Function path cannot be empty")

    # Resource location format: [namespace:]path
    # where namespace is lowercase letters, numbers, underscores, hyphens
    # and path is similar but can contain slashes
    parts = location.split(":", 1)

    if len(parts) == 2:
        namespace, path = parts
        if not namespace or not path:
            raise ValueError(f"Invalid function path: '{location}'")
    else:
        # No namespace, just path
        path = location

    # Basic character validation (colon allowed for namespace separator)
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-/.:")
    if not all(c in allowed_chars for c in location):
        raise ValueError(f"Invalid characters in function path: '{location}'")

    return FunctionCall(function_path=location)


def parse_execute(command: str) -> Execute:
    """Parse an execute command with full subcommand chain.

    Args:
        command: The execute command text (e.g., 'execute as @a at @s run function my:loop')

    Returns:
        Execute AST node with subcommands and final command

    Raises:
        ValueError: If the command syntax is invalid

    Examples:
        >>> parse_execute("execute as @a run function my:tick")
        Execute(subcommands=[ExecuteAs(...)], command=FunctionCall(...))

        >>> parse_execute("execute as @a at @s if score @s timer matches 1.. run function my:loop")
        Execute(subcommands=[ExecuteAs(...), ExecuteAt(...), ExecuteIf(...)], command=FunctionCall(...))
    """
    tokens = [t for t in tokenize_compact(command) if t.type not in (TokenType.WHITESPACE, TokenType.NEWLINE)]

    if len(tokens) < 2:
        raise ValueError("Too few tokens for execute command")

    # Verify starts with "execute"
    if tokens[0].value != "execute":
        raise ValueError("Not an execute command")

    # Parse from after "execute"
    parser = ExecuteParser(tokens[1:])

    # Parse subcommand chain
    subcommands = parser.parse_subcommand_chain()

    # Parse the final command (after 'run') - already returns parsed command
    parsed_command = parser.parse_run_command()

    return Execute(subcommands, parsed_command)


def parse_command_from_tokens(tokens: list) -> Any:
    """Parse a command from a list of tokens."""
    if not tokens:
        return None

    first_token = tokens[0].value

    # Handle function calls
    if first_token == "function":
        if len(tokens) < 2:
            raise ValueError("Expected function path")
        return parse_function_call(tokens[1].value)

    # Handle scoreboard commands
    if first_token == "scoreboard":
        if len(tokens) < 2:
            raise ValueError("scoreboard requires subcommand")

        second = tokens[1].value
        if second == "objectives":
            if len(tokens) < 3:
                raise ValueError("scoreboard objectives requires subcommand")
            third = tokens[2].value
            if third == "add":
                # Reconstruct text for existing parser
                text = " ".join(t.value for t in tokens)
                from mcfunction.parser.scoreboard import parse_scoreboard_objectives_add
                return parse_scoreboard_objectives_add(text)
            elif third == "remove":
                from mcfunction.parser.scoreboard import parse_scoreboard_objectives_remove
                text = " ".join(t.value for t in tokens)
                return parse_scoreboard_objectives_remove(text)
            elif third == "list":
                from mcfunction.parser.scoreboard import parse_scoreboard_objectives_list
                text = " ".join(t.value for t in tokens)
                return parse_scoreboard_objectives_list(text)
            elif third == "setdisplay":
                from mcfunction.parser.scoreboard import parse_scoreboard_objectives_setdisplay
                text = " ".join(t.value for t in tokens)
                return parse_scoreboard_objectives_setdisplay(text)

        elif second == "players":
            if len(tokens) < 3:
                raise ValueError("scoreboard players requires subcommand")
            third = tokens[2].value
            if third == "set":
                from mcfunction.parser.scoreboard import parse_scoreboard_players_set
                text = " ".join(t.value for t in tokens)
                return parse_scoreboard_players_set(text)
            elif third == "add":
                from mcfunction.parser.scoreboard import parse_scoreboard_players_add
                text = " ".join(t.value for t in tokens)
                return parse_scoreboard_players_add(text)
            elif third == "remove":
                from mcfunction.parser.scoreboard import parse_scoreboard_players_remove
                text = " ".join(t.value for t in tokens)
                return parse_scoreboard_players_remove(text)
            elif third == "reset":
                from mcfunction.parser.scoreboard import parse_scoreboard_players_reset
                text = " ".join(t.value for t in tokens)
                return parse_scoreboard_players_reset(text)
            elif third == "operation":
                from mcfunction.parser.scoreboard import parse_scoreboard_players_operation
                text = " ".join(t.value for t in tokens)
                return parse_scoreboard_players_operation(text)

    # Handle data commands
    if first_token == "data":
        from mcfunction.parser.data import parse_data_command
        text = " ".join(t.value for t in tokens)
        return parse_data_command(text)

    # Handle execute chains within execute (nested)
    if first_token == "execute":
        text = " ".join(t.value for t in tokens)
        return parse_execute(text)

    # Handle say command
    if first_token == "say":
        from mcfunction.parser.commands import Say
        if len(tokens) < 2:
            raise ValueError("say command requires a message")
        # Reconstruct the message from all remaining tokens
        message = " ".join(t.value for t in tokens[1:])
        return Say(message=message)

    # Handle tellraw command
    if first_token == "tellraw":
        from mcfunction.parser.commands import Tellraw
        if len(tokens) < 3:
            raise ValueError("tellraw command requires targets and message")
        targets = tokens[1].value
        # Smart JSON reconstruction - join tokens for message but with minimal spaces
        message_tokens = tokens[2:]
        message_parts = []

        # Reconstruct JSON more intelligently
        for i, t in enumerate(message_tokens):
            val = t.value

            # Special handling for JSON tokens to minimize spaces
            if i > 0:
                prev_token = message_tokens[i-1]
                prev_val = prev_token.value

                # No space before these characters
                if val in ":,}]" or prev_val in "{[,:":
                    message_parts.append(val)
                # No space after these characters
                elif prev_val in "{[,":
                    message_parts.append(val)
                # Default: add space
                else:
                    message_parts.append(" " + val)
            else:
                message_parts.append(val)

        # Join without extra processing
        message = "".join(message_parts) if message_parts else ""
        return Tellraw(targets=targets, message=message)

    # Unknown command
    raise ValueError(f"Unknown command: '{first_token}'")
