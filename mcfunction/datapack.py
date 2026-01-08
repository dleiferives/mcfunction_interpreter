"""Datapack parser and loader for Minecraft datapacks.

This module provides functionality to load and parse Minecraft datapacks,
including pack.mcmeta, namespaces, functions, and function tags.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class FunctionTag:
    """Represents a function tag with its values and optional replace flag."""

    values: List[str]
    replace: bool = False


@dataclass
class DataPack:
    """Represents a Minecraft datapack with its structure and metadata."""

    path: str
    format: int
    description: str
    namespaces: List[str]
    function_tags: Dict[str, FunctionTag] = field(default_factory=dict)


def load_datapack(path: str) -> DataPack:
    """Load a Minecraft datapack from the given path.

    This function reads pack.mcmeta, discovers namespaces, validates function
    directories, and loads function tags (minecraft:load, minecraft:tick, etc.).

    Args:
        path: Path to the datapack directory

    Returns:
        DataPack: The loaded datapack with all metadata and structure

    Raises:
        FileNotFoundError: If pack.mcmeta doesn't exist
        ValueError: If pack.mcmeta is invalid or required structure is missing
    """
    datapack_path = Path(path)

    # Validate datapack directory exists
    if not datapack_path.exists():
        raise FileNotFoundError(f"Datapack directory not found: {path}")

    if not datapack_path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    # Load pack.mcmeta
    pack_meta_path = datapack_path / "pack.mcmeta"
    if not pack_meta_path.exists():
        raise FileNotFoundError(f"pack.mcmeta not found in: {path}")

    try:
        with open(pack_meta_path, 'r', encoding='utf-8') as f:
            pack_meta = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in pack.mcmeta: {e}")
    except Exception as e:
        raise ValueError(f"Failed to read pack.mcmeta: {e}")

    # Extract pack format and description
    if "pack" not in pack_meta:
        raise ValueError("pack.mcmeta missing 'pack' section")

    pack_info = pack_meta["pack"]
    if "pack_format" not in pack_info:
        raise ValueError("pack.mcmeta missing 'pack_format'")

    format_version = pack_info["pack_format"]
    description = pack_info.get("description", "")

    # Discover namespaces
    namespaces = []
    data_dir = datapack_path / "data"

    if data_dir.exists() and data_dir.is_dir():
        for item in data_dir.iterdir():
            if item.is_dir():
                # Check if it's a valid namespace with functions directory
                functions_dir = item / "functions"
                if functions_dir.exists() and functions_dir.is_dir():
                    namespaces.append(item.name)

    # Load function tags
    function_tags = {}

    for namespace in namespaces:
        tags_dir = datapack_path / "data" / namespace / "tags" / "functions"

        if tags_dir.exists() and tags_dir.is_dir():
            for tag_file in tags_dir.glob("*.json"):
                try:
                    with open(tag_file, 'r', encoding='utf-8') as f:
                        tag_data = json.load(f)

                    # Extract tag name (without .json extension)
                    tag_name = f"{namespace}:{tag_file.stem}"

                    # Handle both direct values list and wrapped object
                    if isinstance(tag_data, dict):
                        values = tag_data.get("values", [])
                        replace = tag_data.get("replace", False)
                    elif isinstance(tag_data, list):
                        values = tag_data
                        replace = False
                    else:
                        raise ValueError(f"Invalid tag format in {tag_file}")

                    function_tags[tag_name] = FunctionTag(values=values, replace=replace)

                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON in tag file {tag_file}: {e}")
                except Exception as e:
                    raise ValueError(f"Failed to read tag file {tag_file}: {e}")

    return DataPack(
        path=str(datapack_path.absolute()),
        format=format_version,
        description=description,
        namespaces=namespaces,
        function_tags=function_tags
    )