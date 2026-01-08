# Test function for CLI
scoreboard objectives add dummy_obj dummy "Test Objective"
scoreboard players set @p dummy_obj 42
scoreboard players add @p dummy_obj 8
data merge storage test:global {hello:"world", value:123}
