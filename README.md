# MCFunction Interpreter

A Python interpreter for Minecraft datapacks that executes `.mcfunction` files with full support for `function`, `execute`, `scoreboard`, and `data` commands.

## Installation

```bash
pip install -e .
```

Or with dev dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

### Command Line

Execute a specific function from a datapack:

```bash
mcfun examples/my_datapack mynamespace:main
```

### Interactive REPL

Start an interactive session:

```bash
mcfun
```

In the REPL:
- `load <datapack_path>` - Load a datapack
- `run <function_name>` - Execute a function
- `scoreboard` - Show scoreboard state
- `storage` - Show data storage
- `quit` - Exit

## Supported Commands

| Command | Status | Notes |
|---------|--------|-------|
| `function` | ✅ Full | Call stack, recursion with limits |
| `execute` | ✅ Full | All subcommands, forking, conditions, store |
| `scoreboard` | ✅ Full | objectives, players, all operations |
| `data` | ✅ Full | storage get/merge/modify/remove |
| `say/tellraw` | ⚠️ Count | Logged, not simulated |
| `tp/teleport` | ⚠️ Count | Logged, position not tracked |
| `summon/kill` | ⚠️ Count | Logged, entities not simulated |
| `give/clear` | ⚠️ Count | Logged, inventory not simulated |

## Example Datapack

```
my_datapack/
├── pack.mcmeta
└── data/
    ├── minecraft/
    │   └── tags/
    │       └── functions/
    │           ├── load.json
    │           └── tick.json
    └── mynamespace/
        ├── functions/
        │   ├── main.mcfunction
        │   └── loop.mcfunction
        └── tags/
            └── functions/
                └── mytag.json
```

pack.mcmeta:
```json
{
  "pack": {
    "description": "Test datapack",
    "pack_format": 88
  }
}
```

main.mcfunction:
```mcfunction
scoreboard objectives add timer dummy
scoreboard players set #global timer 100
execute as @a run scoreboard players add @s timer 1
```

## Data Types

### Scoreboard Operations
All 9 operations are supported:
- `=` (assignment)
- `+=`, `-=`, `*=`, `/=`, `%=` (arithmetic)
- `><` (swap)
- `>`, `<` (max/min comparison)

### NBT/SNBT
Full support for parsing SNBT:
```snbt
{id:"minecraft:stone",Count:1b,tag:{display:{Name:'{"text":"Test"}'}}}
```

### Entity Selectors
Syntax-only validation:
- `@a`, `@e`, `@p`, `@r`, `@s`
- `@e[type=zombie,distance=..10]`
- `@a[scores={timer=5..10}]`

### Resource Locations
Format: `namespace:path`
- `minecraft:load`
- `mynamespace:loop`
- `my_datapack:data`

## Limitations

- No entity simulation (selectors parse but don't resolve)
- No block placement/breaking
- No player movement
- No chat/command block output
- No actual game world interaction

## Testing

```bash
pytest tests/
```

## License

MIT
