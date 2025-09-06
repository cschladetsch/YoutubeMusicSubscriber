# YouTube Music Manager

A professional CLI tool for managing YouTube Music artist subscriptions using the YouTube Data API v3.

## Demo

[Demo1](resources/demo.txt)


## Overview

YouTube Music Manager allows you to synchronize your YouTube Music subscriptions with a local text file. It compares your target artist list against your current subscriptions and automatically manages the differences - subscribing to new artists and optionally unsubscribing from those not in your list.

## Key Features

- **Smart Synchronization** - Compare target artists with current subscriptions
- **Dry Run Mode** - Preview changes before making them (enabled by default)
- **YouTube Data API Integration** - Direct API access for reliable operations
- **OAuth2 Authentication** - Secure Google account authentication
- **Flexible Format** - Support artist tags and metadata in your files
- **Professional CLI** - Clean command-line interface with multiple operations
- **Error Handling** - Comprehensive error reporting and recovery
- **Cross-Platform** - Works on Windows, macOS, and Linux

## Installation

### Prerequisites

- Rust (latest stable version)
- Google Cloud Console project with YouTube Data API v3 enabled
- OAuth2 credentials (client_secret.json)
- Active YouTube account

### Setup Google Cloud Credentials

1. **Create a Google Cloud Console project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the **YouTube Data API v3**

2. **Create OAuth2 credentials**:
   - Go to **APIs & Services** > **Credentials**
   - Click **Create Credentials** > **OAuth 2.0 Client IDs**
   - Choose **Desktop application**
   - Download the JSON file

3. **Add test users (for development)**:
   - Go to **APIs & Services** > **OAuth consent screen**
   - Scroll to **Test users** section
   - Click **ADD USERS** and add your email address

4. **Setup credentials**:
   ```bash
   # Copy downloaded file to project root
   cp ~/Downloads/client_secret_*.json client_secret.json
   ```

### Install from Source

```bash
# Clone the repository
git clone git@github.com:cschladetsch/YoutubeMusicSubscriber.git
cd youtube-music-manager

# Build the project
cargo build --release
```

### Verify Installation

```bash
# Test the installation
cargo run -- --help

# Validate your artists file
cargo run -- validate

# Alternative: Use the convenience script (recommended)
./run --help
./run validate
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

# Alternative: Use convenience script (recommended)
./run sync
./run --verbose sync
```

### 3. Apply Changes

```bash
# Actually make the changes
ytmusic-manager sync --no-dry-run

# Or with convenience script (recommended)
./run sync --no-dry-run
```

## Commands

### `sync` - Synchronize Subscriptions

Compares your artists file with current YouTube Music subscriptions using the YouTube Data API.

```bash
ytmusic-manager sync [OPTIONS]
```

**Options:**
- `--artists-file FILE` - Artists file path (default: `artists.txt`)
- `--dry-run` - Preview changes without applying them (default behavior)
- `--no-dry-run` - Actually apply the changes
- `--delay SECONDS` - Delay between API requests in seconds (default: 2.0)
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

Lists all channels you're currently subscribed to on YouTube using the YouTube Data API.

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
- `--version` - Show version information
- `--help` - Show help information

## Configuration

### Environment Variables

You can set these environment variables to change default behavior:

- `YTMUSIC_ARTISTS_FILE` - Default artists file path
- `YTMUSIC_DELAY` - Default delay between API requests (seconds)

### Logging

Logs are automatically written to:
- **Console**: INFO level and above (DEBUG with `--verbose`)
- **File**: `youtube_music_manager.log` with DEBUG level details

## Important Notes

### Authentication

- **OAuth2 Required**: First-time setup requires browser authentication
- **Token Caching**: Authentication tokens are cached locally for future use
- **Test Users**: Your app must add your email as a test user in Google Cloud Console
- **API Permissions**: Requires YouTube Data API v3 enabled in your Google Cloud project

### Rate Limiting

- **Default Delay**: 2 seconds between API requests
- **Adjustable**: Use `--delay` option to customize timing
- **Purpose**: Prevents hitting YouTube API rate limits

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

**"Failed to read client_secret.json"**
```bash
# Ensure you have the OAuth2 credentials file
# Download from Google Cloud Console and save as client_secret.json
```

**"Error 403: access_denied" during authentication**
```bash
# Add yourself as a test user in Google Cloud Console
# Go to APIs & Services > OAuth consent screen > Test users
```

**"Failed to search for artist" errors**
```bash
# Ensure YouTube Data API v3 is enabled in Google Cloud Console
# Check API quotas and limits
```

**"API request timed out"**
```bash
# Complete browser authentication quickly when prompted
# Check your internet connection
ytmusic-manager --verbose sync --delay 5
```

### Debug Mode

For troubleshooting, run with maximum verbosity:

```bash
ytmusic-manager --verbose sync --dry-run --delay 5
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

# Build the project
cargo build

# Run tests
cargo test
```

### Development Commands

```bash
# Build debug version
cargo build

# Build release version
cargo build --release

# Run tests
cargo test

# Run with logging
RUST_LOG=debug cargo run -- --verbose sync --dry-run

# Check code
cargo clippy
```

### Project Structure

```
youtube-music-manager/
├── src/                     # Rust source code
│   ├── main.rs             # Command-line interface and main logic
│   └── youtube.rs          # YouTube API client and authentication
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md     # Technical architecture
│   └── DEVELOPMENT.md      # Development guide
├── artists.txt             # Example artists file
├── Cargo.toml             # Rust project configuration
├── README.md              # This file
└── CHANGELOG.md           # Version history
```

## Version History

### v0.1.0 (Current)
- Complete rewrite in Rust with professional CLI architecture
- YouTube Data API v3 integration for reliable operations
- OAuth2 authentication with token caching
- Direct API access replacing browser automation
- Comprehensive error handling and logging
- Dry-run mode for safety
- Flexible artist file format with tags
- Cross-platform support

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed development guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Google YouTube Data API v3](https://developers.google.com/youtube/v3) for reliable YouTube integration
- [Rust](https://www.rust-lang.org/) for high-performance system programming
- [Clap](https://clap.rs/) for command-line interface
- [Tokio](https://tokio.rs/) for async runtime

---

**Disclaimer:** This tool is for educational and personal use only. Use responsibly and respect YouTube's Terms of Service. The authors are not responsible for any account restrictions that may result from automated activity.
