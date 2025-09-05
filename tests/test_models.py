"""Tests for data models."""

import pytest
from ytmusic_manager.models import Artist, SyncAction, SyncActionType, SyncResult, Config, SubscriptionStatus


class TestArtist:
    """Tests for Artist model."""
    
    def test_artist_creation_basic(self):
        """Test basic artist creation."""
        artist = Artist(name="Test Artist")
        assert artist.name == "Test Artist"
        assert artist.id is None
        assert artist.status == SubscriptionStatus.UNKNOWN
        assert artist.tags == []
        assert artist.url is None
    
    def test_artist_creation_full(self):
        """Test artist creation with all fields."""
        artist = Artist(
            name="Test Artist",
            id="test_id",
            status=SubscriptionStatus.SUBSCRIBED,
            tags=["rock", "metal"],
            url="https://example.com"
        )
        assert artist.name == "Test Artist"
        assert artist.id == "test_id"
        assert artist.status == SubscriptionStatus.SUBSCRIBED
        assert artist.tags == ["rock", "metal"]
        assert artist.url == "https://example.com"
    
    def test_artist_str(self):
        """Test string representation."""
        artist = Artist(name="Test Artist")
        assert str(artist) == "Test Artist"
    
    def test_from_line_basic(self):
        """Test creating artist from simple line."""
        artist = Artist.from_line("Simple Artist")
        assert artist.name == "Simple Artist"
        assert artist.tags == []
    
    def test_from_line_with_tags(self):
        """Test creating artist from line with tags."""
        artist = Artist.from_line("Artist Name|rock|metal|indie")
        assert artist.name == "Artist Name"
        assert artist.tags == ["rock", "metal", "indie"]
    
    def test_from_line_with_empty_tags(self):
        """Test creating artist from line with empty tags."""
        artist = Artist.from_line("Artist Name||rock||metal|")
        assert artist.name == "Artist Name"
        assert artist.tags == ["rock", "metal"]
    
    def test_from_line_whitespace(self):
        """Test creating artist from line with whitespace."""
        artist = Artist.from_line("  Artist Name  | rock | metal  ")
        assert artist.name == "Artist Name"
        assert artist.tags == ["rock", "metal"]


class TestSyncAction:
    """Tests for SyncAction model."""
    
    def test_sync_action_creation(self):
        """Test sync action creation."""
        artist = Artist(name="Test Artist")
        action = SyncAction(
            artist=artist,
            action=SyncActionType.SUBSCRIBE,
            reason="Test reason"
        )
        assert action.artist == artist
        assert action.action == SyncActionType.SUBSCRIBE
        assert action.reason == "Test reason"


class TestSyncResult:
    """Tests for SyncResult model."""
    
    def test_sync_result_empty(self):
        """Test empty sync result."""
        result = SyncResult()
        assert result.actions_taken == []
        assert result.errors == []
        assert result.success_count == 0
        assert result.skip_count == 0
        assert result.error_count == 0
        assert result.total_processed == 0
    
    def test_sync_result_with_actions(self):
        """Test sync result with various actions."""
        artist1 = Artist(name="Artist 1")
        artist2 = Artist(name="Artist 2")
        artist3 = Artist(name="Artist 3")
        
        result = SyncResult()
        result.actions_taken = [
            SyncAction(artist1, SyncActionType.SUBSCRIBE, "reason"),
            SyncAction(artist2, SyncActionType.UNSUBSCRIBE, "reason"),
            SyncAction(artist3, SyncActionType.SKIP, "reason")
        ]
        result.errors = ["Error 1", "Error 2"]
        
        assert result.success_count == 2  # subscribe + unsubscribe
        assert result.skip_count == 1
        assert result.error_count == 2
        assert result.total_processed == 3


class TestConfig:
    """Tests for Config model."""
    
    def test_config_defaults(self):
        """Test config with default values."""
        config = Config()
        assert config.artists_file == "artists.txt"
        assert config.max_retries == 3
        assert config.delay_between_actions == 2.0
        assert config.verbose is False
        assert config.dry_run is False
    
    def test_config_custom_values(self):
        """Test config with custom values."""
        config = Config(
            artists_file="custom.txt",
            max_retries=5,
            delay_between_actions=1.5,
            verbose=True,
            dry_run=True
        )
        assert config.artists_file == "custom.txt"
        assert config.max_retries == 5
        assert config.delay_between_actions == 1.5
        assert config.verbose is True
        assert config.dry_run is True


class TestEnums:
    """Tests for enum classes."""
    
    def test_subscription_status_values(self):
        """Test SubscriptionStatus enum values."""
        assert SubscriptionStatus.SUBSCRIBED.value == "subscribed"
        assert SubscriptionStatus.NOT_SUBSCRIBED.value == "not_subscribed"
        assert SubscriptionStatus.UNKNOWN.value == "unknown"
    
    def test_sync_action_values(self):
        """Test SyncActionType enum values."""
        assert SyncActionType.SUBSCRIBE.value == "subscribe"
        assert SyncActionType.UNSUBSCRIBE.value == "unsubscribe"
        assert SyncActionType.SKIP.value == "skip"