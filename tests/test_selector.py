"""Tests for entity selector parser."""

import pytest
from mcfunction.parser.selector import (
    EntitySelector,
    Range,
    ScoreMatcher,
    parse_selector,
)


class TestBasicSelectors:
    """Test basic selector types without arguments."""

    def test_all_players(self):
        result = parse_selector("@a")
        assert result.selector_type == "a"
        assert result.arguments == {}

    def test_all_entities(self):
        result = parse_selector("@e")
        assert result.selector_type == "e"
        assert result.arguments == {}

    def test_nearest_player(self):
        result = parse_selector("@p")
        assert result.selector_type == "p"
        assert result.arguments == {}

    def test_random_player(self):
        result = parse_selector("@r")
        assert result.selector_type == "r"
        assert result.arguments == {}

    def test_self(self):
        result = parse_selector("@s")
        assert result.selector_type == "s"
        assert result.arguments == {}


class TestTypeArgument:
    """Test type argument parsing."""

    def test_type_unquoted(self):
        result = parse_selector("@e[type=zombie]")
        assert result.selector_type == "e"
        assert result.arguments["type"] == "zombie"

    def test_type_quoted(self):
        result = parse_selector('@e[type="minecraft:zombie"]')
        assert result.selector_type == "e"
        assert result.arguments["type"] == "minecraft:zombie"

    def test_type_single_quote(self):
        result = parse_selector("@e[type='custom_mob']")
        assert result.selector_type == "e"
        assert result.arguments["type"] == "custom_mob"


class TestMultipleArguments:
    """Test selectors with multiple arguments."""

    def test_type_and_distance(self):
        result = parse_selector("@e[type=zombie,distance=..10]")
        assert result.selector_type == "e"
        assert result.arguments["type"] == "zombie"
        assert isinstance(result.arguments["distance"], Range)
        assert result.arguments["distance"].min is None
        assert result.arguments["distance"].max == 10

    def test_multiple_different_types(self):
        result = parse_selector("@a[tag=red_team,limit=5,sort=nearest]")
        assert result.selector_type == "a"
        assert result.arguments["tag"] == "red_team"
        assert result.arguments["limit"] == 5
        assert result.arguments["sort"] == "nearest"


class TestRangeParsing:
    """Test range argument parsing."""

    def test_range_exact(self):
        result = parse_selector("@e[distance=5]")
        range_val = result.arguments["distance"]
        assert isinstance(range_val, Range)
        assert range_val.min == 5
        assert range_val.max == 5

    def test_range_max_only(self):
        result = parse_selector("@e[distance=..10]")
        range_val = result.arguments["distance"]
        assert isinstance(range_val, Range)
        assert range_val.min is None
        assert range_val.max == 10

    def test_range_min_only(self):
        result = parse_selector("@e[distance=5..]")
        range_val = result.arguments["distance"]
        assert isinstance(range_val, Range)
        assert range_val.min == 5
        assert range_val.max is None

    def test_range_both(self):
        result = parse_selector("@e[distance=5..10]")
        range_val = result.arguments["distance"]
        assert isinstance(range_val, Range)
        assert range_val.min == 5
        assert range_val.max == 10

    def test_negative_range(self):
        result = parse_selector("@e[x_rotation=-30..30]")
        range_val = result.arguments["x_rotation"]
        assert isinstance(range_val, Range)
        assert range_val.min == -30
        assert range_val.max == 30


class TestCoordinateArguments:
    """Test coordinate argument parsing."""

    def test_single_coordinate(self):
        result = parse_selector("@e[x=10]")
        coords = result.arguments["coordinates"]
        assert coords == (10.0,)

    def test_two_coordinates(self):
        result = parse_selector("@e[x=10,y=20]")
        coords = result.arguments["coordinates"]
        assert coords == (10.0, 20.0)

    def test_three_coordinates(self):
        result = parse_selector("@e[x=10,y=20,z=30]")
        coords = result.arguments["coordinates"]
        assert coords == (10.0, 20.0, 30.0)

    def test_coordinates_negative(self):
        result = parse_selector("@e[x=-5.5,z=10.2]")
        coords = result.arguments["coordinates"]
        # x=-5.5, default y=0, z=10.2
        assert coords == (-5.5, 0.0, 10.2)

    def test_coordinates_with_distance(self):
        result = parse_selector("@e[x=100,y=64,z=100,distance=..20]")
        coords = result.arguments["coordinates"]
        assert coords == (100.0, 64.0, 100.0)
        distance = result.arguments["distance"]
        assert isinstance(distance, Range)


class TestScoresArgument:
    """Test scores argument parsing."""

    def test_scores_single(self):
        result = parse_selector("@e[scores={kills=5}]")
        scores = result.arguments["scores"]
        assert isinstance(scores, dict)
        assert "kills" in scores
        assert scores["kills"].objective == "kills"
        assert scores["kills"].value == 5

    def test_scores_multiple(self):
        result = parse_selector("@e[scores={kills=5,deaths=10}]")
        scores = result.arguments["scores"]
        assert len(scores) == 2
        assert scores["kills"].value == 5
        assert scores["deaths"].value == 10

    def test_scores_with_range(self):
        result = parse_selector("@e[scores={kills=10..20}]")
        scores = result.arguments["scores"]
        score = scores["kills"]
        assert isinstance(score.value, Range)
        assert score.value.min == 10
        assert score.value.max == 20

    def test_scores_multiple_with_ranges(self):
        result = parse_selector("@e[scores={kills=5..,deaths=..10}]")
        scores = result.arguments["scores"]
        kills = scores["kills"]
        deaths = scores["deaths"]
        assert isinstance(kills.value, Range)
        assert kills.value.min == 5
        assert kills.value.max is None
        assert isinstance(deaths.value, Range)
        assert deaths.value.min is None
        assert deaths.value.max == 10


class TestComplexSelectors:
    """Test complex real-world selectors."""

    def test_zombies_nearby(self):
        result = parse_selector("@e[type=zombie,distance=..10,x=100,y=64,z=100]")
        assert result.selector_type == "e"
        assert result.arguments["type"] == "zombie"
        assert isinstance(result.arguments["distance"], Range)
        assert result.arguments["coordinates"] == (100.0, 64.0, 100.0)

    def test_players_with_tag_limit(self):
        result = parse_selector("@a[tag=admin,limit=1,sort=nearest]")
        assert result.selector_type == "a"
        assert result.arguments["tag"] == "admin"
        assert result.arguments["limit"] == 1
        assert result.arguments["sort"] == "nearest"

    def test_enderman_with_scores(self):
        result = parse_selector("@e[type=enderman,scores={kills=5..100,mobs_killed=10}]")
        assert result.selector_type == "e"
        assert result.arguments["type"] == "enderman"
        scores = result.arguments["scores"]
        assert scores["kills"].value.min == 5
        assert scores["kills"].value.max == 100
        assert scores["mobs_killed"].value == 10

    def test_distance_rotations(self):
        result = parse_selector("@e[distance=5..20,x_rotation=-90..90]")
        dist = result.arguments["distance"]
        rot = result.arguments["x_rotation"]
        assert dist.min == 5 and dist.max == 20
        assert rot.min == -90 and rot.max == 90


class TestEdgeCases:
    """Test edge cases and special inputs."""

    def test_whitespace_around_equals(self):
        result = parse_selector("@e[type = zombie]")
        assert result.arguments["type"] == "zombie"

    def test_whitespace_around_commas(self):
        result = parse_selector("@e[ type=zombie , distance=..10 ]")
        assert result.arguments["type"] == "zombie"
        assert isinstance(result.arguments["distance"], Range)

    def test_quoted_name(self):
        result = parse_selector('@a[name="Steve"]')
        assert result.arguments["name"] == "Steve"

    def test_single_quoted_name(self):
        result = parse_selector("@a[name='Steve']")
        assert result.arguments["name"] == "Steve"


class TestValidation:
    """Test validation of invalid inputs."""

    def test_no_at_sign(self):
        with pytest.raises(ValueError, match="must start with @"):
            parse_selector("a")

    def test_invalid_selector_type(self):
        with pytest.raises(ValueError, match="Invalid selector type"):
            parse_selector("@z")

    def test_incomplete_selector(self):
        with pytest.raises(ValueError, match="must have a type character"):
            parse_selector("@")

    def test_missing_bracket(self):
        # Valid case: @a without arguments means "all players"
        # No error should be raised
        result = parse_selector("@a")
        assert result.selector_type == "a"
        assert result.arguments == {}

    def test_incomplete_bracket(self):
        with pytest.raises(ValueError, match="must end with \\]"):
            parse_selector("@a[type=zombie")

    def test_invalid_sort(self):
        with pytest.raises(ValueError, match="Invalid sort value"):
            parse_selector("@a[sort=invalid]")

    def test_empty_scores(self):
        result = parse_selector("@e[scores={}]")
        assert result.arguments["scores"] == {}

    def test_empty_brackets(self):
        result = parse_selector("@e[]")
        assert result.arguments == {}

    def test_malformed_score(self):
        with pytest.raises(ValueError):
            parse_selector("@e[scores={objective}]")  # Missing = and value


class TestRangeStringRepresentation:
    """Test Range __str__ method."""

    def test_range_full(self):
        r = Range(5, 10)
        assert str(r) == "5..10"

    def test_range_min_only(self):
        r = Range(5, None)
        assert str(r) == "5.."

    def test_range_max_only(self):
        r = Range(None, 10)
        assert str(r) == "..10"

    def test_range_empty(self):
        r = Range(None, None)
        assert str(r) == ".."

    def test_range_single(self):
        r = Range(5, 5)
        assert str(r) == "5"


class TestFloatCoordinates:
    """Test parsing coordinates with decimal values."""

    def test_float_x(self):
        result = parse_selector("@e[x=10.5]")
        coords = result.arguments["coordinates"]
        assert coords[0] == 10.5

    def test_multiple_floats(self):
        result = parse_selector("@e[x=-3.14,y=2.718,z=1.414]")
        coords = result.arguments["coordinates"]
        assert coords == (-3.14, 2.718, 1.414)


class TestTagAndName:
    """Test tag and name argument parsing."""

    def test_tag_unquoted(self):
        result = parse_selector("@e[tag=red]")
        assert result.arguments["tag"] == "red"

    def test_tag_quoted(self):
        result = parse_selector('@e[tag="special_mob"]')
        assert result.arguments["tag"] == "special_mob"

    def test_name_unquoted(self):
        result = parse_selector("@e[name=Steve]")
        assert result.arguments["name"] == "Steve"

    def test_name_quoted(self):
        result = parse_selector('@e[name="The Ender Dragon"]')
        assert result.arguments["name"] == "The Ender Dragon"


class TestDxArgument:
    """Test dx/dy/dz arguments (box dimensions)."""

    def test_dx_only(self):
        result = parse_selector("@e[x=10,y=20,z=30,dx=5]")
        assert result.arguments["dx"] == 5.0

    def test_dx_dy_dz(self):
        result = parse_selector("@e[x=10,y=20,z=30,dx=5,dy=3,dz=7]")
        assert result.arguments["dx"] == 5.0
        assert result.arguments["dy"] == 3.0
        assert result.arguments["dz"] == 7.0

    def test_with_coordinates(self):
        result = parse_selector("@e[x=100,y=64,z=100,dx=10,dy=5,dz=10]")
        coords = result.arguments["coordinates"]
        assert coords == (100.0, 64.0, 100.0)
        assert result.arguments["dx"] == 10.0
        assert result.arguments["dy"] == 5.0
        assert result.arguments["dz"] == 10.0
