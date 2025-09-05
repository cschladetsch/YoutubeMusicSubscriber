# YouTube Music Manager

A professional CLI tool for managing YouTube Music artist subscriptions through automated browser interaction.

## Overview

YouTube Music Manager allows you to synchronize your YouTube Music subscriptions with a local text file. It compares your target artist list against your current subscriptions and automatically manages the differences - subscribing to new artists and optionally unsubscribing from those not in your list.

## Key Features

- **Smart Synchronization** - Compare target artists with current subscriptions
- **Dry Run Mode** - Preview changes before making them (enabled by default)
- **Browser Automation** - Reliable Selenium WebDriver-based interaction
- **Flexible Format** - Support artist tags and metadata in your files
- **Professional CLI** - Clean command-line interface with multiple operations
- **Comprehensive Testing** - Well-tested codebase with 89% coverage
- **Cross-Platform** - Works on Windows, macOS, and Linux

## Installation

### Prerequisites

- Python 3.8 or higher
- Chrome or Chromium browser
- Active YouTube Music account (logged in to Chrome)

### Install from Source

```bash
# Clone the repository
git clone <repository-url>
cd youtube-music-manager

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e .
```

### Verify Installation

```bash
# Test the installation
ytmusic-manager --help

# Validate your artists file
ytmusic-manager validate

# Alternative: Use the convenience script (automatically activates venv)
./run --help
```

## Quick Start

### 1. Create Your Artists File

Create an `artists.txt` file with one artist per line:

```text
# My favorite artists
Faith No More
Nine Inch Nails|industrial|metal
Radiohead
Tool|progressive|metal

# Electronic artists
Aphex Twin|electronic|ambient
Boards of Canada|electronic|idm
```

**Format Rules:**
- One artist name per line
- Use `|` to separate artist name from optional tags
- Lines starting with `#` are comments (ignored)
- Empty lines are ignored
- Tags are for organization (not used in matching)

### 2. Preview Your Changes

```bash
# See what would be changed (safe dry-run mode)
ytmusic-manager sync

# Get more detailed output
ytmusic-manager --verbose sync

# Alternative: Use convenience script
./run sync
```

### 3. Apply Changes

```bash
# Actually make the changes
ytmusic-manager sync --no-dry-run

# Or with convenience script
./run sync --no-dry-run
```

## Commands

### `sync` - Synchronize Subscriptions

Compares your artists file with current YouTube Music subscriptions.

```bash
ytmusic-manager sync [OPTIONS]
```

**Options:**
- `--artists-file FILE` - Artists file path (default: `artists.txt`)
- `--dry-run` - Preview changes without applying them (default behavior)
- `--no-dry-run` - Actually apply the changes
- `--delay SECONDS` - Delay between actions in seconds (default: 2.0)
- `--interactive` - Ask for confirmation before making changes

**Examples:**
```bash
# Preview sync (safe, default behavior)
ytmusic-manager sync

# Actually apply changes
ytmusic-manager sync --no-dry-run

# Use custom artists file with slower pace
ytmusic-manager sync --artists-file my_artists.txt --delay 3
```

### `list` - Show Current Subscriptions

Lists all artists you're currently subscribed to on YouTube Music.

```bash
ytmusic-manager list [OPTIONS]
```

**Options:**
- `--output FILE` - Save list to a file

**Examples:**
```bash
# Show current subscriptions
ytmusic-manager list

# Save to file
ytmusic-manager list --output current_subscriptions.txt
```

### `validate` - Check Artists File

Validates the format of your artists file without making any changes.

```bash
ytmusic-manager validate [OPTIONS]
```

**Options:**
- `--artists-file FILE` - File to validate (default: `artists.txt`)

### Global Options

- `--verbose, -v` - Enable detailed logging output
- `--show-browser` - Show browser window (default: headless mode)
- `--version` - Show version information
- `--help` - Show help information

## Configuration

### Environment Variables

You can set these environment variables to change default behavior:

- `YTMUSIC_ARTISTS_FILE` - Default artists file path
- `YTMUSIC_HEADLESS` - Run browser in headless mode (`true`/`false`)
- `YTMUSIC_DELAY` - Default delay between actions (seconds)

### Logging

Logs are automatically written to:
- **Console**: INFO level and above (DEBUG with `--verbose`)
- **File**: `youtube_music_manager.log` with DEBUG level details

## Important Notes

### Browser Requirements

- **Chrome/Chromium Required**: Uses Chrome browser for automation
- **Automatic Setup**: ChromeDriver is downloaded automatically
- **Login Required**: You must be logged into YouTube Music in your default Chrome profile
- **Headless Mode**: Runs invisibly by default (use `--show-browser` to see browser)

### Rate Limiting

- **Default Delay**: 2 seconds between subscription actions
- **Adjustable**: Use `--delay` option to customize timing
- **Purpose**: Prevents triggering YouTube's anti-automation measures

### Safety Features

- **Dry Run Default**: All sync operations preview changes first
- **Interactive Mode**: Optional confirmation prompts
- **Comprehensive Logging**: All actions are logged for review
- **Error Handling**: Graceful handling of failures with detailed error messages

## Troubleshooting

### Common Issues

**"No such file or directory: artists.txt"**
```bash
# Create the file or specify a different path
ytmusic-manager sync --artists-file /path/to/your/artists.txt
```

**"ChromeDriver not found" or browser issues**
```bash
# Clear webdriver cache and retry
rm -rf ~/.wdm/
ytmusic-manager --show-browser sync --dry-run
```

**"Element not found" errors**
```bash
# YouTube Music interface may have changed
# Try with visible browser to see what's happening
ytmusic-manager --verbose --show-browser sync --delay 5
```

**Slow performance**
```bash
# Increase delay between actions
ytmusic-manager sync --delay 5

# Run in headless mode (default, faster)
ytmusic-manager sync  # Already headless by default
```

### Debug Mode

For troubleshooting, run with maximum verbosity and visible browser:

```bash
ytmusic-manager --verbose --show-browser sync --dry-run --delay 5
```

### Getting Help

1. Check this README and the documentation in `docs/`
2. Validate your artists file: `ytmusic-manager validate --verbose`
3. Try dry-run mode first: `ytmusic-manager --verbose sync`
4. Check the log file: `youtube_music_manager.log`
5. Open an issue with detailed error information

## Development

### Setup Development Environment

```bash
# Clone and setup
git clone <repository-url>
cd youtube-music-manager
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e .

# Install development tools
pip install pytest pytest-cov black isort flake8 mypy build
```

### Development Commands

```bash
# Run tests
make test

# Check code quality
make lint

# Format code
make format

# Run tests with coverage
make coverage

# Build package
make build

# Check release readiness
make release-check
```

### Project Structure

```
youtube-music-manager/
├── ytmusic_manager/          # Main package
│   ├── cli.py               # Command-line interface
│   ├── models.py            # Data models
│   ├── sync.py              # Synchronization engine
│   └── youtube.py           # Browser automation
├── tests/                   # Test suite
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md      # Technical architecture
│   └── DEVELOPMENT.md       # Development guide
├── artists.txt              # Example artists file
├── README.md               # This file
└── CHANGELOG.md            # Version history
```

## Version History

### v0.1.0 (Current)
- Complete rewrite with professional CLI architecture
- Comprehensive test suite (89% coverage)
- Modern Python packaging with `pyproject.toml`
- Browser automation with Selenium WebDriver
- Dry-run mode for safety
- Flexible artist file format with tags
- Cross-platform support

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure code quality: `make lint`
5. Run tests: `make test`
6. Submit a pull request

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Selenium WebDriver](https://selenium.dev/) for browser automation
- [webdriver-manager](https://github.com/SergeyPirogov/webdriver_manager) for automatic driver management

---

**Disclaimer:** This tool is for educational and personal use only. Use responsibly and respect YouTube's Terms of Service. The authors are not responsible for any account restrictions that may result from automated activity.