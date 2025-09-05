# Development Guide

This guide covers development setup, workflows, and contribution guidelines for YouTube Music Manager.

## Development Setup

### Prerequisites

- Python 3.8+ 
- Chrome/Chromium browser
- Git

### Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd youtube-music-manager

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dependencies
pip install -e .

# Install development tools
pip install pytest pytest-cov black isort flake8 mypy build
```

### Verify Installation

```bash
# Test the CLI works
ytmusic-manager --help

# Run tests
make test

# Check code quality
make lint
```

## Development Workflow

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines

3. **Add tests** for new functionality:
   ```bash
   # Add unit tests in tests/test_*.py
   # Run tests to ensure they pass
   make test
   ```

4. **Update documentation** if needed:
   - Update README.md for user-facing changes
   - Update CHANGELOG.md for notable changes
   - Add docstrings for new functions/classes

5. **Check code quality**:
   ```bash
   make lint    # Check for issues
   make format  # Auto-format code
   ```

### Code Style Guidelines

- **Type hints**: All public functions should have type annotations
- **Docstrings**: Use Google-style docstrings for classes and public methods
- **Variable names**: Use descriptive names (no abbreviations)
- **Error handling**: Always handle exceptions gracefully
- **Logging**: Use appropriate log levels for different message types

### Example Code Style

```python
def sync_artists(self, target_artists: List[Artist]) -> SyncResult:
    """Synchronize YouTube Music subscriptions with target artists.
    
    Args:
        target_artists: List of artists to subscribe to
        
    Returns:
        Result object containing sync status and any errors
        
    Raises:
        BrowserAutomationError: If browser automation fails
    """
    logger.info(f"Starting sync for {len(target_artists)} artists")
    
    try:
        # Implementation here
        return SyncResult(success=True)
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise BrowserAutomationError(f"Failed to sync artists: {e}")
```

## Testing

### Running Tests

```bash
# All tests
make test

# Specific test file
pytest tests/test_models.py -v

# With coverage
make coverage

# Only unit tests (skip integration)
make test-unit
```

### Writing Tests

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test complete workflows
- **Use mocks**: Mock external dependencies (browser, file system)
- **Test edge cases**: Empty inputs, errors, timeouts

### Test Structure

```python
class TestSyncEngine:
    """Tests for SyncEngine class."""
    
    @pytest.fixture
    def sync_engine(self):
        """Create sync engine for testing."""
        config = Config(dry_run=True)
        client = Mock(spec=YouTubeMusicClient)
        return SyncEngine(client, config)
    
    def test_sync_success(self, sync_engine):
        """Test successful sync operation."""
        # Arrange
        target_artists = [Artist(name="Test Artist")]
        
        # Act
        result = sync_engine.sync_artists(target_artists)
        
        # Assert
        assert result.success is True
        assert len(result.errors) == 0
```

## Architecture Guidelines

### Module Organization

- **models.py**: Data structures and domain objects
- **sync.py**: Business logic and orchestration
- **youtube.py**: External integrations (browser automation)
- **cli.py**: User interface and command handling

### Design Patterns

- **Dependency Injection**: Pass dependencies to constructors
- **Context Managers**: Use for resource management (browser sessions)
- **Factory Methods**: For complex object creation
- **Command Pattern**: For actions that can be queued/logged

### Error Handling

- **Specific exceptions**: Create domain-specific exception types
- **Graceful degradation**: Continue processing when possible
- **User-friendly messages**: Translate technical errors for users
- **Comprehensive logging**: Log at appropriate levels

## Release Process

### Version Management

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes to public API
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Creating a Release

1. **Update version** in `pyproject.toml` and `setup.py`
2. **Update CHANGELOG.md** with release notes
3. **Run full test suite**: `make test`
4. **Build package**: `python -m build`
5. **Create git tag**: `git tag -a v1.0.0 -m "Release v1.0.0"`
6. **Push tag**: `git push origin v1.0.0`

### Pre-release Checklist

- [ ] All tests passing
- [ ] Code coverage above 85%
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated
- [ ] No outstanding security issues

## Troubleshooting Development Issues

### Common Problems

**Import errors after refactoring**:
```bash
# Reinstall in development mode
pip install -e .
```

**Tests failing after dependency changes**:
```bash
# Clear pytest cache
rm -rf .pytest_cache/
# Reinstall dependencies
pip install -r requirements.txt
```

**Browser automation issues**:
```bash
# Clear webdriver cache
rm -rf ~/.wdm/
# Test with visible browser
ytmusic-manager --show-browser sync --dry-run
```

### Debug Mode

For debugging browser automation issues:

```bash
# Run with maximum verbosity and visible browser
ytmusic-manager --verbose --show-browser sync --delay 5 --dry-run
```

## Contributing Guidelines

### Before Contributing

1. Check existing issues and PRs to avoid duplicates
2. Discuss significant changes in an issue first
3. Follow the code style guidelines
4. Add tests for new functionality
5. Update documentation as needed

### Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes following the guidelines above
4. Ensure all tests pass and code quality checks pass
5. Write a clear PR description explaining the changes
6. Submit the pull request

### Code Review Criteria

- Code follows style guidelines and patterns
- Changes are well-tested
- Documentation is updated
- No breaking changes without discussion
- Security considerations addressed

## Getting Help

- Check existing documentation first
- Search closed issues for similar problems
- Create a new issue with detailed reproduction steps
- Include logs and system information for bug reports

---

This development guide will be updated as the project evolves. For questions or suggestions about the development process, please open an issue.