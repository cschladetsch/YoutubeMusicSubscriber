"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_artists_file():
    """Create a temporary artists file for testing."""
    content = """# Test artists file
Artist One
Artist Two|rock|metal
Artist Three|pop

# Another comment
Artist Four|indie|alternative
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    os.unlink(temp_file)


@pytest.fixture
def temp_empty_file():
    """Create a temporary empty file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup
    os.unlink(temp_file)


@pytest.fixture
def sample_artists():
    """Provide sample artist data for testing."""
    from ytmusic_manager.models import Artist, SubscriptionStatus
    
    return [
        Artist(name="Test Artist 1", id="id1", status=SubscriptionStatus.SUBSCRIBED),
        Artist(name="Test Artist 2", id="id2", status=SubscriptionStatus.NOT_SUBSCRIBED, tags=["rock"]),
        Artist(name="Test Artist 3", id="id3", status=SubscriptionStatus.UNKNOWN, tags=["pop", "indie"])
    ]


@pytest.fixture(autouse=True)
def suppress_selenium_logs():
    """Suppress noisy selenium logs during testing."""
    import logging
    logging.getLogger('selenium').setLevel(logging.CRITICAL)
    logging.getLogger('urllib3').setLevel(logging.CRITICAL)


@pytest.fixture
def mock_webdriver():
    """Provide a mock WebDriver for testing."""
    from unittest.mock import Mock
    
    driver = Mock()
    driver.get = Mock()
    driver.find_element = Mock()
    driver.find_elements = Mock()
    driver.execute_script = Mock()
    driver.quit = Mock()
    
    return driver