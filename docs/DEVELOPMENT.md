# Development Guide

This guide covers development setup, workflows, and contribution guidelines for YouTube Music Manager v0.2.0 - Unified Configuration System with SQLite Caching.

## Development Setup

### Prerequisites

- **Rust** (latest stable version) - Install from [rustup.rs](https://rustup.rs/)
- **Git** - Version control system
- **Google Cloud Console project** - For YouTube Data API v3 access
- **Text Editor/IDE** - VS Code with rust-analyzer extension recommended

### Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd youtube-music-manager

# Verify Rust installation
rustc --version
cargo --version

# Setup configuration
cp config.example.json config.json
# Edit config.json with your credentials

# Build the project
cargo build

# Run tests (when implemented)
cargo test

# Test with development config
cargo run -- list
cargo run -- --help
```

### Google Cloud Setup

#### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **YouTube Data API v3**:
   ```bash
   # Or visit: https://console.cloud.google.com/apis/library/youtube.googleapis.com
   ```

#### 2. Create OAuth2 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth 2.0 Client IDs**
3. Choose **Desktop application**
4. Download the JSON file

#### 3. Add Test Users (Development)

1. Go to **APIs & Services** > **OAuth consent screen**
2. Scroll to **Test users** section  
3. Click **ADD USERS** and add your email address

#### 4. Create API Key (Optional, for Search)

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **API Key**
3. Copy the key

#### 5. Configure config.json

1. Copy the example configuration:
   ```bash
   cp config.example.json config.json
   ```

2. Edit `config.json` with your credentials:
   ```json
   {
     "google": {
       "client_secret": {
         "installed": {
           // Paste the entire "installed" section from downloaded OAuth2 file
         }
       },
       "api_key": "paste-your-api-key-here"
     },
     "artists": [
       "Your", "Favorite", "Artists"
     ]
   }
   ```

### Verify Installation

```bash
# Test the CLI help
cargo run -- --help

# List artists from config.json
cargo run -- list

# Validate external artists file (optional)
cargo run -- validate --artists-file artists.txt

# Build optimized release version
cargo build --release

# Run the release version
./target/release/ytmusic-manager list
```

## Development Workflow

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   ```bash
   # Edit source files
   vim src/main.rs
   vim src/youtube.rs
   ```

3. **Test your changes**:
   ```bash
   # Build and test
   cargo build
   cargo run -- validate
   cargo run -- sync --dry-run
   ```

4. **Check code quality**:
   ```bash
   # Format code
   cargo fmt

   # Run linter
   cargo clippy

   # Check for unused dependencies
   cargo machete  # (requires cargo-machete)
   ```

5. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin feature/your-feature-name
   ```

### Code Quality Standards

#### Formatting
```bash
# Auto-format all code
cargo fmt

# Check formatting without making changes
cargo fmt -- --check
```

#### Linting
```bash
# Run Clippy linter
cargo clippy

# Run Clippy with strict settings
cargo clippy -- -D warnings
```

#### Documentation
```bash
# Generate and open documentation
cargo doc --open

# Check documentation links
cargo doc --no-deps
```

## Project Structure

### Source Code Organization

```
src/
├── main.rs              # CLI interface and main application logic
└── youtube.rs           # YouTube API client and authentication

Cargo.toml               # Project dependencies and configuration
```

### Configuration Files

```
client_secret.json       # OAuth2 credentials (from Google Cloud)
api.key                 # YouTube Data API key (optional)
tokencache.json         # OAuth2 token cache (auto-generated)
artists.txt             # Artist list configuration
```

### Documentation

```
docs/
├── ARCHITECTURE.md      # Technical architecture documentation
└── DEVELOPMENT.md       # This file - development guide

README.md               # User-facing documentation
CHANGELOG.md            # Version history and release notes
```

## Testing Strategy

### Current Testing Approach

Since this is an API integration tool, testing primarily involves:

#### Integration Testing
```bash
# Test authentication flow
cargo run -- list

# Test artist file validation
cargo run -- validate

# Test sync planning (dry-run)
cargo run -- sync --dry-run

# Test actual sync operations (with care)
cargo run -- sync --no-dry-run --artists-file test-single-artist.txt
```

#### Manual Testing Checklist

Before releasing:
- [ ] OAuth2 authentication flow works
- [ ] API key search functionality works
- [ ] Artists file parsing handles edge cases
- [ ] Dry-run mode shows accurate plans
- [ ] Actual subscription operations work
- [ ] Error handling provides useful messages
- [ ] CLI help and arguments work correctly

### Future Testing Improvements

#### Unit Testing Framework
```rust
// Example unit test structure
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_artists_file() {
        let content = "Artist 1\nArtist 2|tag1|tag2\n# Comment\n";
        let artists = parse_artists_file(content).unwrap();
        assert_eq!(artists.len(), 2);
        assert_eq!(artists[0], "Artist 1");
        assert_eq!(artists[1], "Artist 2");
    }

    #[tokio::test]
    async fn test_youtube_client_creation() {
        // Mock test for client initialization
        // Would require mocking the OAuth2 flow
    }
}
```

#### Integration Testing
```bash
# Automated integration tests
cargo test --test integration_tests

# Performance testing
cargo test --release --test performance_tests
```

## Debugging Guide

### Common Issues

#### Authentication Problems
```bash
# Clear token cache and re-authenticate
rm tokencache.json
cargo run -- list

# Check OAuth2 credential file
cat client_secret.json | jq .

# Verify API key
cat api.key
```

#### API Issues
```bash
# Enable verbose logging
RUST_LOG=debug cargo run -- --verbose sync --dry-run

# Test API connectivity
curl "https://www.googleapis.com/youtube/v3/search?part=snippet&q=test&key=$(cat api.key)"
```

#### Build Issues
```bash
# Clean build cache
cargo clean

# Update dependencies
cargo update

# Check for outdated dependencies
cargo outdated  # (requires cargo-outdated)
```

### Debugging Tools

#### Logging
```rust
// Add debug logging to code
use log::{debug, info, warn, error};

debug!("Debug information: {:?}", data);
info!("Informational message");
warn!("Warning message");  
error!("Error occurred: {}", error);
```

#### Environment Variables
```bash
# Set log level
export RUST_LOG=debug
cargo run -- sync

# Set log level for specific modules
export RUST_LOG=ytmusic_manager::youtube=debug
cargo run -- sync
```

## Contributing Guidelines

### Code Style

#### Rust Conventions
- Follow standard Rust naming conventions
- Use `cargo fmt` for consistent formatting
- Address all `cargo clippy` warnings
- Add documentation for public APIs
- Use meaningful variable and function names

#### Error Handling
```rust
// Prefer context over generic errors
use anyhow::{Context, Result};

pub fn some_operation() -> Result<()> {
    some_fallible_operation()
        .context("Failed to perform some operation")?;
    Ok(())
}
```

#### Async Code
```rust
// Use async/await consistently
pub async fn async_operation() -> Result<String> {
    let result = api_call().await
        .context("API call failed")?;
    Ok(result)
}
```

### Commit Messages

Use conventional commit format:
```
feat: add new search functionality
fix: resolve authentication token refresh
docs: update API documentation
refactor: simplify error handling logic
test: add integration tests for sync operation
```

### Pull Request Process

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes** with proper testing
4. **Update documentation** if needed
5. **Submit a pull request** with:
   - Clear description of changes
   - Test results/screenshots
   - Any breaking changes noted

### Release Process

#### Version Bumping
```bash
# Update version in Cargo.toml
vim Cargo.toml

# Update CHANGELOG.md
vim CHANGELOG.md

# Build and test
cargo build --release
cargo test
```

#### Creating Releases
```bash
# Commit version changes
git add Cargo.toml CHANGELOG.md
git commit -m "chore: prepare v0.2.0 release"

# Create annotated tag
git tag -a v0.2.0 -m "v0.2.0 - New Features

- Feature 1
- Feature 2
- Bug fixes"

# Push with tags
git push origin main --tags
```

## Performance Optimization

### Profiling

```bash
# Build with profiling enabled
cargo build --release --features profiling

# Profile the application
cargo run --release -- sync --no-dry-run
# Use tools like flamegraph or perf for detailed profiling
```

### Optimization Techniques

#### Async Performance
```rust
// Use concurrent operations where possible
use futures::future::join_all;

let tasks = artists.iter().map(|artist| {
    search_artist(artist)
});

let results = join_all(tasks).await;
```

#### Memory Management
```rust
// Prefer references over cloning when possible
fn process_artist(artist: &str) -> Result<()> {
    // Process without taking ownership
}

// Use Box for large structures
type LargeData = Box<Vec<ComplexStruct>>;
```

## Security Considerations

### Credential Handling
- Never commit credentials to version control
- Use environment variables for sensitive data in CI/CD
- Validate all external input
- Use secure defaults (dry-run mode)

### API Security
- Implement proper rate limiting
- Use minimum required OAuth2 scopes
- Handle authentication errors gracefully
- Log security-relevant events appropriately

## IDE Setup

### VS Code Configuration

Create `.vscode/settings.json`:
```json
{
    "rust-analyzer.checkOnSave.command": "clippy",
    "rust-analyzer.formatting.enable": true,
    "editor.formatOnSave": true,
    "files.exclude": {
        "**/target": true,
        "**/.git": true
    }
}
```

### Recommended Extensions
- **rust-analyzer** - Rust language support
- **CodeLLDB** - Debugging support
- **crates** - Cargo.toml dependency management
- **Error Lens** - Inline error display

## Troubleshooting

### Common Build Errors

#### Linking Errors
```bash
# On Ubuntu/Debian
sudo apt-get install build-essential pkg-config libssl-dev

# On macOS
xcode-select --install
```

#### Dependency Issues
```bash
# Clear Cargo cache
cargo clean

# Remove lock file and regenerate
rm Cargo.lock
cargo update
```

### Runtime Issues

#### Authentication Failures
1. Check client_secret.json format
2. Verify test user is added in Google Cloud Console
3. Clear token cache and re-authenticate
4. Check API quotas and limits

#### API Errors
1. Verify YouTube Data API v3 is enabled
2. Check API key validity and permissions
3. Verify internet connectivity
4. Check for API service outages

---

This development guide should provide everything needed to contribute effectively to the YouTube Music Manager project. For additional questions, please check the existing issues or create a new one.