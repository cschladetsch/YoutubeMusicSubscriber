# YouTube Music Manager

Clean CLI tool for managing YouTube Music subscriptions from a text file.

## Features

- 🎵 **Sync subscriptions** to match your artist list
- 📋 **List current subscriptions** and export to file  
- ✅ **Validate artist files** before syncing
- 🔍 **Proper error handling** and logging
- 🎛️ **Flexible options** (dry-run, headless, interactive)

## Installation

```bash
pip install -r requirements.txt
```

You'll also need Chrome/Chromium installed for Selenium WebDriver.

## Usage

### Basic Sync
```bash
python3 main.py sync
```

### List Current Subscriptions
```bash
python3 main.py list --output my_artists.txt
```

### Validate Artist File
```bash
python3 main.py validate
```

### Advanced Options
```bash
# Dry run (show what would happen)
python3 main.py sync --dry-run

# Show browser (for debugging)
python3 main.py sync --browser --interactive

# Custom artist file and delays
python3 main.py sync --artists-file my_artists.txt --delay 3.0
```

## Artist File Format

Edit `artists.txt` with one artist per line:

```
# Comments start with #
Faith No More
Nine Inch Nails|metal|industrial
Rammstein|metal
Caravan Palace|electro swing|french

# Tags after | are optional but help with matching
```

## Commands

| Command | Description |
|---------|-------------|
| `sync` | Sync subscriptions to match artist file |
| `list` | Show current subscriptions |
| `validate` | Check artist file format |

## Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would be done without making changes |
| `--browser` | Show browser instead of headless mode |
| `--interactive` | Pause for manual login |
| `--verbose` | Enable detailed logging |
| `--artists-file FILE` | Use custom artist file (default: artists.txt) |

## Architecture

Clean, testable code structure:

```
lib/
├── models.py    # Data classes (Artist, SyncResult, Config)
├── youtube.py   # YouTube Music client (Selenium-based)
├── sync.py      # Sync engine logic
└── __init__.py

main.py          # CLI interface
requirements.txt # Dependencies
artists.txt      # Your artist list
```

## Logging

Logs are written to `youtube_music_manager.log` and console. Use `--verbose` for detailed output.
