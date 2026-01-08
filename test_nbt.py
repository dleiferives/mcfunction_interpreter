#!/usr/bin/env python3
from mcfunction.parser.nbt import parse_snbt

tests = [
    '{id:"minecraft:stone",Count:1b}',
    "{'nested':'value'}",
    '{arr:[I;1,2,3]}',
    '{a:1b,b:2s,c:3,d:4L,e:5.5f}',
    '[B;1,2,3]',
    '{display:{Name:\'{"text":"Test"}\'}}',
]

print('NBT Parser Tests:')
for t in tests:
    try:
        result = parse_snbt(t)
        print(f'✓ {t}')
        print(f'  -> {result}')
    except Exception as e:
        print(f'✗ {t}')
        print(f'  ERROR: {e}')
    print()
