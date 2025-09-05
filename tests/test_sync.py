"""Tests for sync engine."""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path

from ytmusic_manager.sync import SyncEngine
from ytmusic_manager.models import Artist, SyncAction, SyncActionType, SyncResult, Config, SubscriptionStatus
from ytmusic_manager.youtube import YouTubeMusicClient


class TestSyncEngine:
    """Tests for SyncEngine class."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock YouTube client."""
        return Mock(spec=YouTubeMusicClient)
    
    @pytest.fixture
    def config(self):
        """Create test config."""
        return Config(artists_file="test_artists.txt", dry_run=True)
    
    @pytest.fixture
    def sync_engine(self, mock_client, config):
        """Create sync engine with mocks."""
        return SyncEngine(mock_client, config)
    
    def test_load_target_artists_file_not_found(self, sync_engine):
        """Test loading artists when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            sync_engine.load_target_artists()
    
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.open", new_callable=mock_open, read_data="Artist 1\nArtist 2|rock\n# Comment\n\nArtist 3")
    def test_load_target_artists_success(self, mock_file, mock_exists, sync_engine):
        """Test successful loading of artists."""
        mock_exists.return_value = True
        
        artists = sync_engine.load_target_artists()
        
        assert len(artists) == 3
        assert artists[0].name == "Artist 1"
        assert artists[0].tags == []
        assert artists[1].name == "Artist 2"
        assert artists[1].tags == ["rock"]
        assert artists[2].name == "Artist 3"
    
    @patch("pathlib.Path.exists") 
    @patch("pathlib.Path.open", new_callable=mock_open, read_data="Valid Artist\n\nAnother Artist")
    def test_load_target_artists_with_invalid_lines(self, mock_file, mock_exists, sync_engine):
        """Test loading artists with some invalid lines."""
        mock_exists.return_value = True
        
        # Since there are no actual invalid lines in this test data, we need to simulate an exception
        original_from_line = Artist.from_line
        def mock_from_line(line):
            if "Another Artist" in line:
                raise ValueError("Test exception")
            return original_from_line(line)
        
        with patch("ytmusic_manager.sync.logger") as mock_logger:
            with patch.object(Artist, 'from_line', side_effect=mock_from_line):
                artists = sync_engine.load_target_artists()
        
        assert len(artists) == 1
        assert artists[0].name == "Valid Artist"
        mock_logger.warning.assert_called()
    
    def test_get_current_subscriptions(self, sync_engine, mock_client):
        """Test getting current subscriptions."""
        expected_subs = [
            Artist(name="Current 1", status=SubscriptionStatus.SUBSCRIBED),
            Artist(name="Current 2", status=SubscriptionStatus.SUBSCRIBED)
        ]
        mock_client.get_subscriptions.return_value = expected_subs
        
        result = sync_engine.get_current_subscriptions()
        
        assert result == expected_subs
        mock_client.get_subscriptions.assert_called_once()
    
    def test_plan_sync_subscribe_new_artists(self, sync_engine):
        """Test planning sync actions for new subscriptions."""
        target_artists = [
            Artist(name="New Artist 1"),
            Artist(name="New Artist 2"),
            Artist(name="Existing Artist")
        ]
        current_subscriptions = [
            Artist(name="Existing Artist", status=SubscriptionStatus.SUBSCRIBED),
            Artist(name="Old Artist", status=SubscriptionStatus.SUBSCRIBED)
        ]
        
        actions = sync_engine.plan_sync(target_artists, current_subscriptions)
        
        # Should have 2 subscribe, 1 skip, 1 unsubscribe
        subscribe_actions = [a for a in actions if a.action == SyncActionType.SUBSCRIBE]
        skip_actions = [a for a in actions if a.action == SyncActionType.SKIP]
        unsubscribe_actions = [a for a in actions if a.action == SyncActionType.UNSUBSCRIBE]
        
        assert len(subscribe_actions) == 2
        assert len(skip_actions) == 1
        assert len(unsubscribe_actions) == 1
        
        assert subscribe_actions[0].artist.name == "New Artist 1"
        assert subscribe_actions[1].artist.name == "New Artist 2"
        assert skip_actions[0].artist.name == "Existing Artist"
        assert unsubscribe_actions[0].artist.name == "Old Artist"
    
    def test_plan_sync_case_insensitive(self, sync_engine):
        """Test that sync planning is case insensitive."""
        target_artists = [Artist(name="Artist Name")]
        current_subscriptions = [Artist(name="ARTIST NAME")]
        
        actions = sync_engine.plan_sync(target_artists, current_subscriptions)
        
        skip_actions = [a for a in actions if a.action == SyncActionType.SKIP]
        assert len(skip_actions) == 1
    
    def test_execute_sync_dry_run(self, sync_engine, mock_client):
        """Test executing sync in dry run mode."""
        actions = [
            SyncAction(Artist(name="Artist 1"), SyncActionType.SUBSCRIBE, "reason"),
            SyncAction(Artist(name="Artist 2"), SyncActionType.SKIP, "reason")
        ]
        
        result = sync_engine.execute_sync(actions)
        
        assert len(result.actions_taken) == 2
        assert len(result.errors) == 0
        # Should not call client methods in dry run
        mock_client.search_artist.assert_not_called()
        mock_client.subscribe_to_artist.assert_not_called()
    
    def test_execute_sync_skip_actions(self, sync_engine):
        """Test executing sync with skip actions."""
        sync_engine.config.dry_run = False
        actions = [SyncAction(Artist(name="Artist"), SyncActionType.SKIP, "Already subscribed")]
        
        result = sync_engine.execute_sync(actions)
        
        assert len(result.actions_taken) == 1
        assert result.actions_taken[0].action == SyncActionType.SKIP
    
    def test_execute_sync_subscribe_success(self, sync_engine, mock_client):
        """Test successful subscription execution."""
        sync_engine.config.dry_run = False
        sync_engine.config.delay_between_actions = 0  # No delay in tests
        
        artist = Artist(name="Test Artist")
        actions = [SyncAction(artist, SyncActionType.SUBSCRIBE, "Not subscribed")]
        
        # Mock successful search and subscribe
        found_artist = Artist(name="Test Artist", url="http://example.com", id="test_id")
        mock_client.search_artist.return_value = found_artist
        mock_client.subscribe_to_artist.return_value = True
        
        result = sync_engine.execute_sync(actions)
        
        assert len(result.actions_taken) == 1
        assert len(result.errors) == 0
        mock_client.search_artist.assert_called_once_with("Test Artist")
        mock_client.subscribe_to_artist.assert_called_once()
    
    def test_execute_sync_subscribe_artist_not_found(self, sync_engine, mock_client):
        """Test subscription when artist is not found."""
        sync_engine.config.dry_run = False
        
        artist = Artist(name="Unknown Artist")
        actions = [SyncAction(artist, SyncActionType.SUBSCRIBE, "Not subscribed")]
        
        mock_client.search_artist.return_value = None
        
        result = sync_engine.execute_sync(actions)
        
        assert len(result.actions_taken) == 0
        assert len(result.errors) == 1
        assert "Could not find artist: Unknown Artist" in result.errors[0]
    
    def test_execute_sync_subscribe_failure(self, sync_engine, mock_client):
        """Test subscription failure."""
        sync_engine.config.dry_run = False
        
        artist = Artist(name="Test Artist")
        actions = [SyncAction(artist, SyncActionType.SUBSCRIBE, "Not subscribed")]
        
        found_artist = Artist(name="Test Artist", url="http://example.com")
        mock_client.search_artist.return_value = found_artist
        mock_client.subscribe_to_artist.return_value = False
        
        result = sync_engine.execute_sync(actions)
        
        assert len(result.actions_taken) == 0
        assert len(result.errors) == 1
        assert "Failed to subscribe Test Artist" in result.errors[0]
    
    def test_execute_sync_unsubscribe_not_implemented(self, sync_engine):
        """Test unsubscribe action (not yet implemented)."""
        sync_engine.config.dry_run = False
        
        artist = Artist(name="Test Artist")
        actions = [SyncAction(artist, SyncActionType.UNSUBSCRIBE, "Not in target")]
        
        result = sync_engine.execute_sync(actions)
        
        assert len(result.actions_taken) == 0
        assert len(result.errors) == 1
        assert "Unsubscribe not implemented" in result.errors[0]
    
    def test_execute_sync_exception_handling(self, sync_engine, mock_client):
        """Test exception handling during sync execution."""
        sync_engine.config.dry_run = False
        
        artist = Artist(name="Test Artist")
        actions = [SyncAction(artist, SyncActionType.SUBSCRIBE, "Not subscribed")]
        
        mock_client.search_artist.side_effect = Exception("Network error")
        
        result = sync_engine.execute_sync(actions)
        
        assert len(result.actions_taken) == 0
        assert len(result.errors) == 1
        assert "Network error" in result.errors[0]
    
    @patch.object(SyncEngine, 'load_target_artists')
    @patch.object(SyncEngine, 'get_current_subscriptions')
    @patch.object(SyncEngine, 'plan_sync')
    @patch.object(SyncEngine, 'execute_sync')
    def test_sync_full_workflow(self, mock_execute, mock_plan, mock_current, mock_load, sync_engine):
        """Test complete sync workflow."""
        # Setup mocks
        target_artists = [Artist(name="Target")]
        current_subs = [Artist(name="Current")]
        planned_actions = [SyncAction(Artist(name="Test"), SyncActionType.SKIP, "reason")]
        expected_result = SyncResult()
        
        mock_load.return_value = target_artists
        mock_current.return_value = current_subs
        mock_plan.return_value = planned_actions
        mock_execute.return_value = expected_result
        
        result = sync_engine.sync()
        
        assert result == expected_result
        mock_load.assert_called_once()
        mock_current.assert_called_once()
        mock_plan.assert_called_once_with(target_artists, current_subs)
        mock_execute.assert_called_once_with(planned_actions)
    
    @patch.object(SyncEngine, 'load_target_artists')
    def test_sync_exception_handling(self, mock_load, sync_engine):
        """Test sync exception handling."""
        mock_load.side_effect = Exception("File error")
        
        result = sync_engine.sync()
        
        assert len(result.errors) == 1
        assert "Sync failed: File error" in result.errors[0]