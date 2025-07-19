# Books Formatting Integration

This document describes the automatic formatting setup for books files (`.jsonl`) that is integrated into the simulation workflow.

## Overview

Every time you run `make run GAME=<game_name>`, the system will automatically format all `.jsonl` files in the specified game directory after the simulation completes.

## What it does

1. **Runs the simulation** - Executes the normal game simulation process
2. **Formats books files** - Automatically formats all `.jsonl` files found in the game directory
3. **Smart JSON formatting** - Pretty-prints JSON while keeping simple name objects like `{"name": "L1"}` compact on single lines

## Files involved

- **Makefile** - Updated `run` target to include formatting step
- **scripts/format_books_json.py** - Python script that handles the formatting logic with advanced JSON processing

## How it works

The formatting script (`scripts/format_books_json.py`) performs the following:

1. **JSONL Processing** - Searches for all `.jsonl` files in the specified game directory
2. **JSON Parsing** - Uses Python's built-in `json` module to safely parse each line
3. **Smart Formatting** - Pretty-prints JSON with 2-space indentation while keeping simple objects compact:
   - Simple name objects like `{"name": "L1"}` stay on single lines
   - Complex objects are pretty-printed for readability
4. **Error Recovery** - Includes advanced error handling and JSONL reconstruction for corrupted files
5. **Format Validation** - Ensures output maintains valid JSONL format (one JSON object per line)

## Benefits

- **Smart formatting** - Pretty-printed JSON for readability with compact simple objects
- **Consistent structure** - All books files have uniform formatting standards
- **Version control friendly** - Readable format is better for code reviews and diffs
- **Automatic** - No manual intervention required
- **Robust** - Advanced error handling and JSONL reconstruction capabilities
- **Fast** - Efficient Python JSON processing

## Example formatting

**Before formatting** (raw JSONL):
```json
{"id": 1, "events": [{"type": "reveal", "board": [[{"name": "L1"}, {"name": "H1"}]]}]}
```

**After formatting**:
```json
{
  "id": 1,
  "events": [
    {
      "type": "reveal", 
      "board": [
        [
          {"name": "L1"},
          {"name": "H1"}
        ]
      ]
    }
  ]
}
```

Notice how simple name objects like `{"name": "L1"}` remain compact on single lines while the overall structure is pretty-printed.

## Usage

Simply run your simulation as usual:

```bash
make run GAME=0_0_tower_defense
```

The formatting will happen automatically after the simulation completes.

## Requirements

- **Python 3** - For running the formatting script (uses built-in json module)
- **Virtual environment** - Script runs in the project's Python virtual environment

## Error handling

- **Graceful failures** - If formatting fails for any reason, a warning is displayed but the build continues
- **JSONL reconstruction** - Automatically attempts to repair corrupted JSONL files
- **Invalid line skipping** - Lines that cannot be parsed as valid JSON are skipped with warnings
- **Detailed error reporting** - Shows specific error messages and line numbers for debugging

## Example output

```
Formatting books files...
  Formatting: games/0_0_tower_defense/library/books/books_bonus.jsonl
  ✅ Formatted: games/0_0_tower_defense/library/books/books_bonus.jsonl (100 lines processed)
  Formatting: games/0_0_tower_defense/library/books/books_base.jsonl
  ✅ Formatted: games/0_0_tower_defense/library/books/books_base.jsonl (100 lines processed)
Books formatting complete! (200 total lines processed)
```
