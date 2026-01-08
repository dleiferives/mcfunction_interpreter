"""Comprehensive unit tests for all parser modules.

Tests for:
1. NBT parser with nested structures
2. Selector parser with all selector types and arguments
3. Scoreboard parser all subcommands
4. Data parser all operations
5. Function and execute parsers with chains

Uses pytest fixtures for test data and verifies round-trip parsing where possible.
"""

import pytest
from mcfunction.parser.nbt import (
    parse_snbt, NBTByte, NBTShort, NBTInt, NBTLong, NBTFloat, NBTDouble,
    NBTString, NBTByteArray, NBTIntArray, NBTLongArray, NBTList, NBTCompound
)
from mcfunction.parser.selector import (
    parse_selector, EntitySelector, Range, ScoreMatcher
)
from mcfunction.parser.scoreboard import (
    parse_scoreboard_objectives_add,
    parse_scoreboard_objectives_remove,
    parse_scoreboard_objectives_list,
    parse_scoreboard_objectives_setdisplay,
    parse_scoreboard_players_set,
    parse_scoreboard_players_add,
    parse_scoreboard_players_remove,
    parse_scoreboard_players_reset,
    parse_scoreboard_players_operation,
)
from mcfunction.parser.data import (
    parse_data_get,
    parse_data_merge,
    parse_data_modify,
    parse_data_remove,
    parse_data_command,
)
from mcfunction.parser.function_execute import (
    parse_function_call,
    parse_execute,
    parse_command_from_tokens,
)
from mcfunction.parser.chat import (
    parse_say,
    parse_tellraw,
)
from mcfunction.parser.commands import (
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
    Say,
    Tellraw,
)


class TestNBTStructures:
    """Test NBT parser with nested structures and all value types."""

    @pytest.fixture
    def simple_nbt(self):
        """Simple NBT values for testing."""
        return {
            'byte': '{value:127b}',
            'short': '{value:32767s}',
            'int': '{value:100}',
            'long': '{value:9223372036854775807L}',
            'float': '{value:3.14f}',
            'double': '{value:2.718281828d}',
            'string': '{value:"test"}',
            'string_unquoted': '{value:test_string}',
        }

    @pytest.fixture
    def complex_nbt(self):
        """Complex nested NBT structures."""
        return {
            'nested': '{outer:{inner:{deep:"value"}}}',
            'list': '{items:[1,2,3]}',
            'mixed_list': '{items:[1b,2s,3L,4.5f,"test"]}',
            'arrays': '{byte_array:[B;1,2,3],int_array:[I;10,20,30],long_array:[L;100,200,300]}',
            'compound_list': '{entities:[{id:"zombie",Health:20.0f},{id:"skeleton",Health:15.0f}]}',
        }

    def test_all_value_types(self, simple_nbt):
        """Test parsing all NBT value types."""
        results = {k: parse_snbt(v) for k, v in simple_nbt.items()}

        assert isinstance(results['byte'].value['value'], NBTByte)
        assert results['byte'].value['value'].value == 127

        assert isinstance(results['short'].value['value'], NBTShort)
        assert results['short'].value['value'].value == 32767

        assert isinstance(results['int'].value['value'], NBTInt)
        assert results['int'].value['value'].value == 100

        assert isinstance(results['long'].value['value'], NBTLong)
        assert results['long'].value['value'].value == 9223372036854775807

        assert isinstance(results['float'].value['value'], NBTFloat)
        assert results['float'].value['value'].value == 3.14

        assert isinstance(results['double'].value['value'], NBTDouble)
        assert results['double'].value['value'].value == 2.718281828

        assert isinstance(results['string'].value['value'], NBTString)
        assert results['string'].value['value'].value == "test"

        assert isinstance(results['string_unquoted'].value['value'], NBTString)
        assert results['string_unquoted'].value['value'].value == "test_string"

    def test_nested_compounds(self, complex_nbt):
        """Test deeply nested compound structures."""
        result = parse_snbt(complex_nbt['nested'])
        assert isinstance(result, NBTCompound)
        assert isinstance(result.value['outer'], NBTCompound)
        assert isinstance(result.value['outer'].value['inner'], NBTCompound)
        assert result.value['outer'].value['inner'].value['deep'].value == "value"

    def test_list_parsing(self, complex_nbt):
        """Test list parsing with various types."""
        result = parse_snbt(complex_nbt['list'])
        assert isinstance(result, NBTCompound)
        items = result.value['items']
        assert isinstance(items, NBTList)
        assert len(items.value) == 3
        assert all(isinstance(v, NBTInt) for v in items.value)

    def test_mixed_list(self, complex_nbt):
        """Test list with mixed types."""
        result = parse_snbt(complex_nbt['mixed_list'])
        items = result.value['items'].value
        assert isinstance(items[0], NBTByte)
        assert isinstance(items[1], NBTShort)
        assert isinstance(items[2], NBTLong)
        assert isinstance(items[3], NBTFloat)
        assert isinstance(items[4], NBTString)

    def test_typed_arrays(self, complex_nbt):
        """Test byte, int, and long arrays."""
        result = parse_snbt(complex_nbt['arrays'])
        byte_arr = result.value['byte_array']
        int_arr = result.value['int_array']
        long_arr = result.value['long_array']

        assert isinstance(byte_arr, NBTByteArray)
        assert len(byte_arr.value) == 3
        assert isinstance(int_arr, NBTIntArray)
        assert len(int_arr.value) == 3
        assert isinstance(long_arr, NBTLongArray)
        assert len(long_arr.value) == 3

    def test_compound_list(self, complex_nbt):
        """Test list of compounds."""
        result = parse_snbt(complex_nbt['compound_list'])
        entities = result.value['entities'].value
        assert len(entities) == 2
        assert all(isinstance(e, NBTCompound) for e in entities)
        assert entities[0].value['id'].value == "zombie"
        assert entities[1].value['Health'].value == 15.0

    def test_round_trip_simple(self):
        """Test that simple NBT can be parsed and converted back to string."""
        original = '{id:"minecraft:stone",Count:1b}'
        parsed = parse_snbt(original)
        # The string representation should be parseable again
        str_repr = str(parsed)
        reparsed = parse_snbt(str_repr)
        # Check structure is preserved
        assert isinstance(reparsed, NBTCompound)
        assert "id" in reparsed.value
        assert "Count" in reparsed.value

    def test_round_trip_complex(self):
        """Test round-trip for complex nested structures."""
        original = '{data:{inventory:[{Slot:0b,id:"minecraft:diamond"}],level:5}}'
        parsed = parse_snbt(original)
        str_repr = str(parsed)
        reparsed = parse_snbt(str_repr)
        assert isinstance(reparsed, NBTCompound)
        assert "data" in reparsed.value
        assert "inventory" in reparsed.value["data"].value


class TestSelectorParser:
    """Test selector parser with all types and arguments."""

    @pytest.fixture
    def basic_selectors(self):
        """Basic selector types without arguments."""
        return {
            'all_players': '@a',
            'all_entities': '@e',
            'nearest_player': '@p',
            'random_player': '@r',
            'self': '@s',
        }

    @pytest.fixture
    def typed_selectors(self):
        """Selectors with type arguments."""
        return {
            'zombie': '@e[type=zombie]',
            'minecraft_zombie': '@e[type="minecraft:zombie"]',
            'custom_mob': "@e[type='custom_mob']",
            'skeleton': '@e[type=skeleton]',
        }

    @pytest.fixture
    def complex_selectors(self):
        """Complex selectors with multiple arguments."""
        return {
            'full': '@e[type=zombie,distance=..10,x=100,y=64,z=100,scores={kills=5..20}]',
            'players_with_tag': '@a[tag=admin,limit=1,sort=nearest]',
            'rotations': '@e[x_rotation=-30..30,y_rotation=-180..180]',
            'box': '@e[x=10,y=20,z=30,dx=5,dy=3,dz=7]',
            'mixed': '@a[name="Steve",distance=5..,tag=!dead]',
        }

    def test_all_selector_types(self, basic_selectors):
        """Test all basic selector types (@a, @e, @p, @r, @s)."""
        for name, selector_str in basic_selectors.items():
            result = parse_selector(selector_str)
            assert result.selector_type == selector_str[1]
            assert result.arguments == {}

    def test_type_argument_parsing(self, typed_selectors):
        """Test type argument with various quoting."""
        for name, selector_str in typed_selectors.items():
            result = parse_selector(selector_str)
            assert result.selector_type == "e"
            assert "type" in result.arguments
            assert result.arguments["type"] in ["zombie", "minecraft:zombie", "custom_mob", "skeleton"]

    def test_distance_ranges(self):
        """Test distance argument with range syntax."""
        selectors = [
            ('@e[distance=5]', 5, 5),
            ('@e[distance=..10]', None, 10),
            ('@e[distance=5..]', 5, None),
            ('@e[distance=5..10]', 5, 10),
        ]
        for selector_str, expected_min, expected_max in selectors:
            result = parse_selector(selector_str)
            distance = result.arguments["distance"]
            assert isinstance(distance, Range)
            assert distance.min == expected_min
            assert distance.max == expected_max

    def test_complex_arguments(self, complex_selectors):
        """Test selectors with multiple argument types."""
        result = parse_selector(complex_selectors['full'])
        assert result.selector_type == "e"
        assert result.arguments["type"] == "zombie"
        assert isinstance(result.arguments["distance"], Range)
        assert result.arguments["coordinates"] == (100.0, 64.0, 100.0)
        assert "scores" in result.arguments
        assert "kills" in result.arguments["scores"]

    def test_scores_argument(self):
        """Test scores argument with various formats."""
        result = parse_selector("@e[scores={kills=5,deaths=10..20}]")
        scores = result.arguments["scores"]
        assert "kills" in scores
        assert "deaths" in scores
        assert scores["kills"].value == 5
        assert isinstance(scores["deaths"].value, Range)

    def test_coordinate_parsing(self):
        """Test coordinate argument parsing."""
        # Single coordinate
        result = parse_selector("@e[x=10]")
        assert result.arguments["coordinates"] == (10.0,)

        # Multiple coordinates
        result = parse_selector("@e[x=10,y=20,z=30]")
        assert result.arguments["coordinates"] == (10.0, 20.0, 30.0)

        # Partial coordinates
        result = parse_selector("@e[x=10,z=30]")
        assert result.arguments["coordinates"] == (10.0, 0.0, 30.0)

    def test_limit_and_sort(self):
        """Test limit and sort arguments."""
        result = parse_selector("@a[limit=5,sort=nearest]")
        assert result.arguments["limit"] == 5
        assert result.arguments["sort"] == "nearest"

    def test_float_values(self):
        """Test float arguments like dx, dy, dz."""
        result = parse_selector("@e[x=10,dx=5.5,dy=2.3]")
        coords = result.arguments["coordinates"]
        assert coords[0] == 10.0
        assert result.arguments["dx"] == 5.5
        assert result.arguments["dy"] == 2.3

    def test_negative_values(self):
        """Test negative values in ranges and coordinates."""
        result = parse_selector("@e[x=-5,y=-10.5,x_rotation=-90..90]")
        coords = result.arguments["coordinates"]
        assert coords == (-5.0, -10.5)
        rot = result.arguments["x_rotation"]
        assert rot.min == -90
        assert rot.max == 90

    def test_validation_errors(self):
        """Test that invalid selectors raise appropriate errors."""
        with pytest.raises(ValueError, match="must start with @"):
            parse_selector("a")

        with pytest.raises(ValueError, match="Invalid selector type"):
            parse_selector("@z")

        with pytest.raises(ValueError, match="must end with"):
            parse_selector("@a[type=zombie")

    def test_whitespace_handling(self):
        """Test whitespace tolerance."""
        result = parse_selector("@e[ type = zombie , distance = ..10 ]")
        assert result.arguments["type"] == "zombie"
        assert isinstance(result.arguments["distance"], Range)

    def test_tag_argument(self):
        """Test tag argument parsing."""
        result = parse_selector("@e[tag=red_team]")
        assert result.arguments["tag"] == "red_team"

        result = parse_selector('@e[tag="special_mob"]')
        assert result.arguments["tag"] == "special_mob"

    def test_name_argument(self):
        """Test name argument parsing."""
        result = parse_selector("@a[name=Steve]")
        assert result.arguments["name"] == "Steve"

        result = parse_selector('@a[name="The Ender Dragon"]')
        assert result.arguments["name"] == "The Ender Dragon"


class TestScoreboardParser:
    """Test all scoreboard parser functions."""

    @pytest.fixture
    def objectives_commands(self):
        """Scoreboard objectives subcommands."""
        return {
            'add': 'scoreboard objectives add test dummy',
            'add_display': 'scoreboard objectives add test dummy "Test Objective"',
            'remove': 'scoreboard objectives remove test',
            'list': 'scoreboard objectives list',
            'setdisplay': 'scoreboard objectives setdisplay sidebar test',
            'setdisplay_clear': 'scoreboard objectives setdisplay sidebar',
        }

    @pytest.fixture
    def players_commands(self):
        """Scoreboard players subcommands."""
        return {
            'set': 'scoreboard players set @a test 100',
            'add': 'scoreboard players add @p deaths 1',
            'remove': 'scoreboard players remove @e[type=zombie] health 5',
            'reset': 'scoreboard players reset @a',
            'reset_objective': 'scoreboard players reset @a test',
            'operation': 'scoreboard players operation @a test = @p stats',
        }

    def test_objectives_add(self, objectives_commands):
        """Test objectives add commands."""
        result = parse_scoreboard_objectives_add(objectives_commands['add'])
        assert result.objective == "test"
        assert result.criteria == "dummy"
        assert result.display_name is None

        result = parse_scoreboard_objectives_add(objectives_commands['add_display'])
        assert result.objective == "test"
        assert result.criteria == "dummy"
        assert result.display_name == '"Test Objective"'

    def test_objectives_remove(self, objectives_commands):
        """Test objectives remove command."""
        result = parse_scoreboard_objectives_remove(objectives_commands['remove'])
        assert result.objective == "test"

    def test_objectives_list(self, objectives_commands):
        """Test objectives list command."""
        result = parse_scoreboard_objectives_list(objectives_commands['list'])
        # Should return empty object
        assert result is not None

    def test_objectives_setdisplay(self, objectives_commands):
        """Test objectives setdisplay commands."""
        result = parse_scoreboard_objectives_setdisplay(objectives_commands['setdisplay'])
        assert result.slot == "sidebar"
        assert result.objective == "test"

        result = parse_scoreboard_objectives_setdisplay(objectives_commands['setdisplay_clear'])
        assert result.slot == "sidebar"
        assert result.objective is None

    def test_players_set(self, players_commands):
        """Test players set command."""
        result = parse_scoreboard_players_set(players_commands['set'])
        assert result.targets == "@a"
        assert result.objective == "test"
        assert result.score == 100

    def test_players_add(self, players_commands):
        """Test players add command."""
        result = parse_scoreboard_players_add(players_commands['add'])
        assert result.targets == "@p"
        assert result.objective == "deaths"
        assert result.score == 1

    def test_players_remove(self, players_commands):
        """Test players remove command."""
        result = parse_scoreboard_players_remove(players_commands['remove'])
        assert result.targets == "@e[type=zombie]"
        assert result.objective == "health"
        assert result.score == 5

    def test_players_reset(self, players_commands):
        """Test players reset commands."""
        result = parse_scoreboard_players_reset(players_commands['reset'])
        assert result.targets == "@a"
        assert result.objective is None

        result = parse_scoreboard_players_reset(players_commands['reset_objective'])
        assert result.targets == "@a"
        assert result.objective == "test"

    def test_players_operation(self, players_commands):
        """Test players operation command."""
        result = parse_scoreboard_players_operation(players_commands['operation'])
        assert result.targets == "@a"
        assert result.target_objective == "test"
        assert result.operation == "="
        assert result.source == "@p"
        assert result.source_objective == "stats"

    def test_operation_types(self):
        """Test all operation types."""
        operations = [
            ("scoreboard players operation @a test = @p stats", "="),
            ("scoreboard players operation @a test += @p stats", "+="),
            ("scoreboard players operation @a test -= @p stats", "-="),
            ("scoreboard players operation @a test *= @p stats", "*="),
            ("scoreboard players operation @a test /= @p stats", "/="),
            ("scoreboard players operation @a test %= @p stats", "%="),
            ("scoreboard players operation @a test >< @p stats", "><"),
            ("scoreboard players operation @a test < @p stats", "<"),
            ("scoreboard players operation @a test > @p stats", ">"),
        ]
        for cmd, expected_op in operations:
            result = parse_scoreboard_players_operation(cmd)
            assert result.operation == expected_op


class TestDataParser:
    """Test data command parser with all operations."""

    @pytest.fixture
    def data_commands(self):
        """Data commands for testing."""
        return {
            'get': 'data get entity @s Health',
            'get_storage': 'data get storage minecraft:global data',
            'merge': 'data merge entity @s {Health:20.0f}',
            'modify_set': 'data modify entity @s Health set value 20',
            'modify_append': 'data modify entity @s Inventory append value {id:"minecraft:diamond"}',
            'modify_prepend': 'data modify entity @s Inventory prepend value {id:"minecraft:stone"}',
            'modify_insert': 'data modify entity @s Inventory insert 0 from entity @s SelectedItem',
            'modify_merge': 'data modify entity @s Tags merge value ["test"]',
            'remove': 'data remove entity @s Inventory[0]',
        }

    def test_data_get(self, data_commands):
        """Test data get operations."""
        result = parse_data_command(data_commands['get'])
        assert result.target == "entity @s"
        assert result.path == "Health"

        result = parse_data_command(data_commands['get_storage'])
        assert result.target == "storage minecraft:global"
        assert result.path == "data"

    def test_data_merge(self, data_commands):
        """Test data merge operation."""
        result = parse_data_command(data_commands['merge'])
        assert result.target == "entity @s"
        assert isinstance(result.nbt, NBTCompound)
        assert "Health" in result.nbt.value

    def test_data_modify_set(self, data_commands):
        """Test data modify set operation."""
        result = parse_data_command(data_commands['modify_set'])
        assert result.target == "entity @s"
        assert result.path == "Health"
        assert result.operation == "set"
        assert result.value is not None
        assert isinstance(result.value, NBTInt)

    def test_data_modify_append(self, data_commands):
        """Test data modify append operation."""
        result = parse_data_command(data_commands['modify_append'])
        assert result.target == "entity @s"
        assert result.path == "Inventory"
        assert result.operation == "append"
        assert result.value is not None
        assert isinstance(result.value, NBTCompound)

    def test_data_modify_prepend(self, data_commands):
        """Test data modify prepend operation."""
        result = parse_data_command(data_commands['modify_prepend'])
        assert result.operation == "prepend"
        assert result.value is not None

    def test_data_modify_insert(self, data_commands):
        """Test data modify insert operation."""
        result = parse_data_command(data_commands['modify_insert'])
        assert result.operation == "insert"
        assert result.source is not None
        assert result.index == 0

    def test_data_modify_merge(self, data_commands):
        """Test data modify merge operation."""
        result = parse_data_command(data_commands['modify_merge'])
        assert result.operation == "merge"
        assert result.value is not None

    def test_data_remove(self, data_commands):
        """Test data remove operation."""
        result = parse_data_command(data_commands['remove'])
        assert result.target == "entity @s"
        assert result.path == "Inventory[0]"

    def test_block_location(self):
        """Test data commands with block coordinates."""
        result = parse_data_command("data get block 10 64 20 Inventory")
        assert result.target == "block 10 64 20"
        assert result.path == "Inventory"

    def test_relative_coordinates(self):
        """Test data commands with relative coordinates."""
        result = parse_data_command("data get block ~ ~ ~ Items")
        assert result.target == "block ~ ~ ~"
        assert result.path == "Items"


class TestFunctionExecuteParser:
    """Test function and execute command parsers with chains."""

    @pytest.fixture
    def function_commands(self):
        """Function call commands."""
        return {
            'basic': 'function minecraft:tick',
            'namespaced': 'function my_namespace:subdir/function',
            'path_only': 'function loop',
        }

    @pytest.fixture
    def execute_commands(self):
        """Execute commands with various subcommands."""
        return {
            'simple': 'execute as @a run function my:loop',
            'chained': 'execute as @a at @s run function my:tick',
            'if_condition': 'execute if entity @e[type=zombie] run function my:zombie_check',
            'unless_condition': 'execute unless score @s test matches 5.. run function my:default',
            'store': 'execute store result score @s test run function my:calc',
            'positioned': 'execute positioned 10 64 20 run function my:at_pos',
            'rotated': 'execute rotated 90 0 run function my:look_east',
            'align': 'execute align xyz run function my:align',
            'anchored': 'execute anchored eyes run function my:anchored',
            'facing_coord': 'execute facing 10 64 20 run function my:face_pos',
            'facing_selector': 'execute facing @p run function my:face_player',
            'in_dim': 'execute in the_nether run function my:nether',
            'on_target': 'execute on entity run function my:on_entity',
            'summon': 'execute summon zombie run function my:summoned',
            'complex': 'execute as @a at @s if score @s health matches 1.. positioned ~ ~1 ~ run function my:check_health',
            'nested_execute': 'execute as @a run execute at @s run function my:nested',
        }

    def test_function_calls(self, function_commands):
        """Test function call parsing."""
        for name, cmd in function_commands.items():
            result = parse_function_call(cmd.replace('function ', ''))
            assert isinstance(result, type(parse_function_call('test')))
            assert result.function_path in ['minecraft:tick', 'my_namespace:subdir/function', 'loop']

    def test_execute_simple(self, execute_commands):
        """Test simple execute command."""
        result = parse_execute(execute_commands['simple'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteAs)
        assert result.subcommands[0].selector.selector_type == "a"

    def test_execute_chained(self, execute_commands):
        """Test execute with multiple subcommands."""
        result = parse_execute(execute_commands['chained'])
        assert len(result.subcommands) == 2
        assert isinstance(result.subcommands[0], ExecuteAs)
        assert isinstance(result.subcommands[1], ExecuteAt)

    def test_execute_if_condition(self, execute_commands):
        """Test execute with if condition."""
        result = parse_execute(execute_commands['if_condition'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteIf)
        assert result.subcommands[0].condition_type == "entity"

    def test_execute_unless_condition(self, execute_commands):
        """Test execute with unless condition."""
        result = parse_execute(execute_commands['unless_condition'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteUnless)
        assert result.subcommands[0].condition_type == "score"

    def test_execute_store(self, execute_commands):
        """Test execute with store."""
        result = parse_execute(execute_commands['store'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteStore)
        assert result.subcommands[0].store_type == "result"
        assert result.subcommands[0].target == "score @s test"

    def test_execute_positioned(self, execute_commands):
        """Test execute positioned."""
        result = parse_execute(execute_commands['positioned'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecutePositioned)
        assert result.subcommands[0].x == 10.0
        assert result.subcommands[0].y == 64.0
        assert result.subcommands[0].z == 20.0

    def test_execute_rotated(self, execute_commands):
        """Test execute rotated."""
        result = parse_execute(execute_commands['rotated'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteRotated)
        assert result.subcommands[0].yaw == 90.0
        assert result.subcommands[0].pitch == 0.0

    def test_execute_align(self, execute_commands):
        """Test execute align."""
        result = parse_execute(execute_commands['align'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteAlign)
        assert result.subcommands[0].axes == "xyz"

    def test_execute_anchored(self, execute_commands):
        """Test execute anchored."""
        result = parse_execute(execute_commands['anchored'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteAnchored)
        assert result.subcommands[0].anchor == "eyes"

    def test_execute_facing_coords(self, execute_commands):
        """Test execute facing coordinates."""
        result = parse_execute(execute_commands['facing_coord'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteFacing)
        assert result.subcommands[0].x == 10.0
        assert result.subcommands[0].y == 64.0
        assert result.subcommands[0].z == 20.0

    def test_execute_facing_selector(self, execute_commands):
        """Test execute facing selector."""
        result = parse_execute(execute_commands['facing_selector'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteFacing)
        assert result.subcommands[0].target is not None
        assert result.subcommands[0].target.selector_type == "p"

    def test_execute_in_dimension(self, execute_commands):
        """Test execute in dimension."""
        result = parse_execute(execute_commands['in_dim'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteIn)
        assert result.subcommands[0].dimension == "the_nether"

    def test_execute_on_target(self, execute_commands):
        """Test execute on target."""
        result = parse_execute(execute_commands['on_target'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteOn)
        assert result.subcommands[0].target == "entity"

    def test_execute_summon(self, execute_commands):
        """Test execute summon."""
        result = parse_execute(execute_commands['summon'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteSummon)
        assert result.subcommands[0].entity == "zombie"

    def test_execute_complex_chain(self, execute_commands):
        """Test complex execute chain with multiple conditions."""
        result = parse_execute(execute_commands['complex'])
        # Should have: as, at, if, positioned
        assert len(result.subcommands) == 4
        assert isinstance(result.subcommands[0], ExecuteAs)
        assert isinstance(result.subcommands[1], ExecuteAt)
        assert isinstance(result.subcommands[2], ExecuteIf)
        assert isinstance(result.subcommands[3], ExecutePositioned)

    def test_nested_execute(self, execute_commands):
        """Test execute containing nested execute."""
        result = parse_execute(execute_commands['nested_execute'])
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteAs)
        # The command should be another Execute
        assert result.command is not None
        assert isinstance(result.command, type(result))  # Nested Execute

    def test_execute_with_score_condition(self):
        """Test execute with score condition."""
        cmd = "execute if score @s test matches 1..10 run function my:range_check"
        result = parse_execute(cmd)
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteIf)
        assert result.subcommands[0].condition_type == "score"

    def test_execute_with_block_condition(self):
        """Test execute with block condition."""
        cmd = "execute if block 10 64 20 minecraft:stone run function my:block_check"
        result = parse_execute(cmd)
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteIf)
        assert result.subcommands[0].condition_type == "block"
        assert result.subcommands[0].condition_args["x"] == 10.0

    def test_execute_with_data_condition(self):
        """Test execute with data condition."""
        cmd = "execute if data entity @s Health run function my:data_check"
        result = parse_execute(cmd)
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteIf)
        assert result.subcommands[0].condition_type == "data"

    def test_store_score_operations(self):
        """Test store with score target."""
        cmd = "execute store result score @s test run function my:calc"
        result = parse_execute(cmd)
        store = result.subcommands[0]
        assert isinstance(store, ExecuteStore)
        assert store.store_type == "result"
        assert store.target == "score @s test"

    def test_store_with_type_and_scale(self):
        """Test store with type and scale."""
        cmd = "execute store result storage minecraft:global value int 2.0 run function my:calc"
        result = parse_execute(cmd)
        store = result.subcommands[0]
        assert isinstance(store, ExecuteStore)
        assert store.type == "int"
        assert store.scale == 2.0

    def test_relative_coordinates_in_execute(self):
        """Test relative coordinates in execute commands."""
        cmd = "execute positioned ~ ~1 ~ run function my:offset"
        result = parse_execute(cmd)
        positioned = result.subcommands[0]
        assert isinstance(positioned, ExecutePositioned)
        # Relative coordinates are parsed as offsets
        assert positioned.x == 0.0
        assert positioned.y == 1.0
        assert positioned.z == 0.0
        assert positioned.selector is None

    def test_anchored_with_facing(self):
        """Test execute chain with anchored and facing."""
        cmd = "execute anchored eyes facing @p run function my:line_of_sight"
        result = parse_execute(cmd)
        assert len(result.subcommands) == 2
        assert isinstance(result.subcommands[0], ExecuteAnchored)
        assert isinstance(result.subcommands[1], ExecuteFacing)

    def test_store_with_path(self):
        """Test store with storage path."""
        cmd = "execute store result storage minecraft:global data.value int run function my:store"
        result = parse_execute(cmd)
        store = result.subcommands[0]
        assert isinstance(store, ExecuteStore)
        assert store.path == "data.value"


class TestRoundTripParsing:
    """Test round-trip parsing where possible."""

    def test_selector_round_trip(self):
        """Test that selectors can be parsed and their components validated."""
        original = "@e[type=zombie,distance=..10,scores={kills=5..20}]"
        result = parse_selector(original)
        # Verify structure
        assert result.selector_type == "e"
        assert result.arguments["type"] == "zombie"
        assert isinstance(result.arguments["distance"], Range)
        assert "scores" in result.arguments
        scores = result.arguments["scores"]
        assert "kills" in scores
        assert isinstance(scores["kills"].value, Range)

    def test_data_command_structure_preservation(self):
        """Test that data commands maintain their structure."""
        # This is more about verifying the parsed structure matches expectations
        cmd = "data modify entity @s Inventory append value {id:\"minecraft:diamond\",Count:1b}"
        result = parse_data_command(cmd)
        assert result.target == "entity @s"
        assert result.path == "Inventory"
        assert result.operation == "append"
        assert isinstance(result.value, NBTCompound)
        assert "id" in result.value.value
        assert "Count" in result.value.value

    def test_scoreboard_command_consistency(self):
        """Test that scoreboard commands maintain consistent structure."""
        cmd = "scoreboard players operation @a stats = @p deaths"
        result = parse_scoreboard_players_operation(cmd)
        assert result.targets == "@a"
        assert result.target_objective == "stats"
        assert result.operation == "="
        assert result.source == "@p"
        assert result.source_objective == "deaths"

    def test_execute_chain_structure(self):
        """Test that execute chain structure is preserved."""
        cmd = "execute as @a at @s if entity @e[type=zombie,distance=..5] run function my:danger"
        result = parse_execute(cmd)
        assert len(result.subcommands) == 3
        assert all(isinstance(cmd, (ExecuteAs, ExecuteAt, ExecuteIf)) for cmd in result.subcommands)
        assert isinstance(result.command, type(parse_function_call('test')))


class TestParserErrorHandling:
    """Test parser error handling and edge cases."""

    def test_nbt_empty_compound(self):
        """Test empty NBT compound."""
        result = parse_snbt("{}")
        assert isinstance(result, NBTCompound)
        assert len(result.value) == 0

    def test_nbt_empty_list(self):
        """Test empty NBT list."""
        result = parse_snbt("[]")
        assert isinstance(result, NBTList)
        assert len(result.value) == 0

    def test_nbt_invalid_syntax(self):
        """Test NBT parsing with invalid syntax."""
        with pytest.raises(ValueError):
            parse_snbt("{key:}")  # Missing value after colon

    def test_selector_invalid(self):
        """Test invalid selector inputs."""
        with pytest.raises(ValueError):
            parse_selector("invalid")

        with pytest.raises(ValueError):
            parse_selector("@[type=zombie]")  # Missing selector type

    def test_scoreboard_invalid_syntax(self):
        """Test scoreboard commands with invalid syntax."""
        with pytest.raises(ValueError):
            parse_scoreboard_objectives_add("scoreboard objectives add")

    def test_data_invalid_command(self):
        """Test data commands with invalid syntax."""
        with pytest.raises(ValueError):
            parse_data_command("data get")

    def test_execute_invalid(self):
        """Test execute commands with invalid syntax."""
        with pytest.raises(ValueError):
            parse_execute("execute")

        with pytest.raises(ValueError):
            parse_execute("execute as @a")

    def test_function_invalid_path(self):
        """Test function calls with invalid paths."""
        with pytest.raises(ValueError):
            parse_function_call("")

        with pytest.raises(ValueError):
            parse_function_call("path with spaces")

    def test_complex_nbt_with_escapes(self):
        """Test NBT with escaped characters."""
        result = parse_snbt('{name:"Test\\\\"}')
        assert result.value["name"].value == 'Test\\'

    def test_selector_with_spaces(self):
        """Test selector parsing with various whitespace patterns."""
        result = parse_selector("@e[ type = zombie , distance = ..10 ]")
        assert result.arguments["type"] == "zombie"
        assert isinstance(result.arguments["distance"], Range)

    def test_data_modify_insert_invalid(self):
        """Test data modify insert without index."""
        with pytest.raises(ValueError):
            parse_data_command("data modify entity @s Inventory insert from entity @s SelectedItem")

    def test_nested_brackets_nbt(self):
        """Test deeply nested NBT structures."""
        deep = '{a:{b:{c:{d:{e:"deep"}}}}}'
        result = parse_snbt(deep)
        assert result.value["a"].value["b"].value["c"].value["d"].value["e"].value == "deep"


class TestComplexRealWorldExamples:
    """Test complex real-world Minecraft commands."""

    def test_zombie_spawner_check(self):
        """Test a realistic zombie spawner check command."""
        cmd = "execute as @e[type=minecraft:zombie] at @s if block ~ ~-1 ~ minecraft:spawner run function my:spawner_nearby"
        result = parse_execute(cmd)
        assert len(result.subcommands) == 3
        assert isinstance(result.subcommands[0], ExecuteAs)
        assert isinstance(result.subcommands[1], ExecuteAt)
        assert isinstance(result.subcommands[2], ExecuteIf)
        assert result.subcommands[2].condition_type == "block"

    def test_player_health_monitor(self):
        """Test player health monitoring with score tracking."""
        cmd = "execute as @a at @s if score @s health matches ..20 run function my:low_health"
        result = parse_execute(cmd)
        assert len(result.subcommands) == 3
        # The command after run is a function call
        assert result.command is not None

    def test_mob_farm_counter(self):
        """Test mob farm with counter and limiting."""
        cmd = "execute if entity @e[type=zombie,scores={kills=..99}] run scoreboard players add @e[type=zombie] kills 1"
        result = parse_execute(cmd)
        assert len(result.subcommands) == 1
        assert isinstance(result.subcommands[0], ExecuteIf)

    def test_storage_data_operations(self):
        """Test complex storage data operations."""
        # Multiple data operations
        get_result = parse_data_command("data get storage my:storage player_data")
        assert get_result.target == "storage my:storage"
        assert get_result.path == "player_data"

        merge_result = parse_data_command("data merge storage my:storage {version:2}")
        assert merge_result.target == "storage my:storage"
        assert isinstance(merge_result.nbt, NBTCompound)

    def test_conditional_execution_chain(self):
        """Test a long chain of conditional execution."""
        cmd = "execute as @a at @s align xyz if block ~ ~ ~ minecraft:air unless entity @e[type=zombie,distance=..10] run function my:safe_area"
        result = parse_execute(cmd)
        assert len(result.subcommands) == 5  # as, at, align, if, unless
        types = [type(sc) for sc in result.subcommands]
        assert ExecuteAs in types
        assert ExecuteAt in types
        assert ExecuteAlign in types
        assert ExecuteIf in types
        assert ExecuteUnless in types

    def test_store_result_in_score(self):
        """Test storing calculation result in scoreboard."""
        cmd = "execute store result score @s calculation run function my:calc"
        result = parse_execute(cmd)
        store = result.subcommands[0]
        assert isinstance(store, ExecuteStore)
        assert store.store_type == "result"
        assert store.target == "score @s calculation"

    def test_complex_nbt_structure(self):
        """Test parsing a realistic NBT structure."""
        nbt = '{id:"minecraft:zombie",Health:20.0f,Attributes:[{Base:20.0,Name:"generic.max_health"}],HandItems:[{id:"minecraft:iron_sword"}]}'
        result = parse_snbt(nbt)
        assert isinstance(result, NBTCompound)
        assert "Attributes" in result.value
        assert isinstance(result.value["Attributes"], NBTList)
        assert len(result.value["Attributes"].value) == 1
        assert "HandItems" in result.value
        assert len(result.value["HandItems"].value) == 1

    def test_selector_with_all_arg_types(self):
        """Test selector combining all argument types."""
        cmd = "@e[type=zombie,distance=5..20,x=100,y=64,z=100,dx=10,dy=5,dz=10,x_rotation=-30..30,scores={kills=10..,deaths=..5},tag=!dead,limit=5,sort=furthest]"
        result = parse_selector(cmd)
        assert result.selector_type == "e"
        assert result.arguments["type"] == "zombie"
        assert isinstance(result.arguments["distance"], Range)
        assert result.arguments["coordinates"] == (100.0, 64.0, 100.0)
        assert result.arguments["dx"] == 10.0
        assert result.arguments["dy"] == 5.0
        assert result.arguments["dz"] == 10.0
        assert isinstance(result.arguments["x_rotation"], Range)
        assert "scores" in result.arguments
        assert "kills" in result.arguments["scores"]
        assert "deaths" in result.arguments["scores"]
        assert result.arguments["tag"] == "!dead"
        assert result.arguments["limit"] == 5
        assert result.arguments["sort"] == "furthest"

    def test_execute_with_store_bossbar(self):
        """Test execute with bossbar store."""
        cmd = "execute store result bossbar minecraft:foo value run function my:calc"
        result = parse_execute(cmd)
        store = result.subcommands[0]
        assert isinstance(store, ExecuteStore)
        assert store.target == "bossbar minecraft:foo value"

    def test_execute_rotated_selector(self):
        """Test execute rotated with selector."""
        cmd = "execute rotated @p run function my:match_rotation"
        result = parse_execute(cmd)
        rotated = result.subcommands[0]
        assert isinstance(rotated, ExecuteRotated)
        assert rotated.selector is not None
        assert rotated.selector.selector_type == "p"


class TestChatCommands:
    """Test chat command parsers (say, tellraw)."""

    def test_parse_say_basic(self):
        """Test basic say command."""
        cmd = "say Hello World!"
        result = parse_say(cmd)
        assert isinstance(result, Say)
        assert result.message == "Hello World!"

    def test_parse_say_message_only(self):
        """Test say command with single word."""
        cmd = "say hello"
        result = parse_say(cmd)
        assert isinstance(result, Say)
        assert result.message == "hello"

    def test_parse_say_empty_args(self):
        """Test say command with no message raises error."""
        with pytest.raises(ValueError, match="say command requires a message"):
            parse_say("say")

    def test_parse_say_long_message(self):
        """Test say command with complex message."""
        cmd = "say This is a longer message with multiple words"
        result = parse_say(cmd)
        assert isinstance(result, Say)
        assert result.message == "This is a longer message with multiple words"

    def test_parse_tellraw_basic(self):
        """Test basic tellraw command."""
        cmd = 'tellraw @a {"text":"Hello!"}'
        result = parse_tellraw(cmd)
        assert isinstance(result, Tellraw)
        assert result.targets == "@a"
        assert result.message == '{"text":"Hello!"}'

    def test_parse_tellraw_player_name(self):
        """Test tellraw with player name instead of selector."""
        cmd = 'tellraw Steve {"text":"Welcome!"}'
        result = parse_tellraw(cmd)
        assert isinstance(result, Tellraw)
        assert result.targets == "Steve"
        assert result.message == '{"text":"Welcome!"}'

    def test_parse_tellraw_complex_json(self):
        """Test tellraw with complex JSON."""
        cmd = 'tellraw @p {"text":"Click me","clickEvent":{"action":"run_command","value":"function my:button"}}'
        result = parse_tellraw(cmd)
        assert isinstance(result, Tellraw)
        assert result.targets == "@p"
        assert '{"text":"Click me"' in result.message

    def test_parse_tellraw_missing_targets(self):
        """Test tellraw without targets raises error."""
        with pytest.raises(ValueError, match="tellraw command requires targets"):
            parse_tellraw("tellraw")

    def test_parse_tellraw_missing_message(self):
        """Test tellraw without message raises error."""
        with pytest.raises(ValueError, match="tellraw command requires a message"):
            parse_tellraw("tellraw @a")

    def test_parse_command_from_tokens_say(self):
        """Test say command via parse_command_from_tokens."""
        from mcfunction.parser.lexer import tokenize_compact
        tokens = tokenize_compact("say Hello from tokens")
        result = parse_command_from_tokens(tokens)
        assert isinstance(result, Say)
        assert result.message == "Hello from tokens"

    def test_parse_command_from_tokens_tellraw(self):
        """Test tellraw command via parse_command_from_tokens."""
        from mcfunction.parser.lexer import tokenize_compact
        tokens = tokenize_compact('tellraw @a {"text":"Test"}')
        result = parse_command_from_tokens(tokens)
        assert isinstance(result, Tellraw)
        assert result.targets == "@a"
        assert result.message == '{"text":"Test"}'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])