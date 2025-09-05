"""Integration tests for the YouTube Music Manager."""

import pytest
import tempfile
import os
from unittest.mock import patch, Mock

from ytmusic_manager.models import Config, Artist, SubscriptionStatus
from ytmusic_manager.sync import SyncEngine
from ytmusic_manager.youtube import YouTubeMusicClient


class TestIntegrationWorkflows:
    """Integration tests for complete workflows."""
    
    def test_complete_sync_workflow_dry_run(self, temp_artists_file):
        """Test complete sync workflow in dry-run mode."""
        # Create config pointing to temp file
        config = Config(artists_file=temp_artists_file, dry_run=True, verbose=True)
        
        # Mock YouTube client
        with patch('ytmusic_manager.youtube.webdriver.Chrome') as mock_chrome:
            mock_driver = Mock()
            mock_chrome.return_value = mock_driver
            
            # Mock current subscriptions
            current_subs = [
                Artist(name="Artist One", status=SubscriptionStatus.SUBSCRIBED),
                Artist(name="Existing Artist", status=SubscriptionStatus.SUBSCRIBED)
            ]
            
            client = YouTubeMusicClient(headless=True)
            client.get_subscriptions = Mock(return_value=current_subs)
            
            # Create sync engine and run
            engine = SyncEngine(client, config)
            result = engine.sync()
            
            # Verify results
            assert result.total_processed > 0
            assert result.error_count == 0  # Should be no errors in dry run
            
            # Should have some subscribe actions for new artists
            subscribe_actions = [a for a in result.actions_taken if a.action.value == "subscribe"]
            skip_actions = [a for a in result.actions_taken if a.action.value == "skip"]
            unsubscribe_actions = [a for a in result.actions_taken if a.action.value == "unsubscribe"]
            
            assert len(subscribe_actions) > 0  # Should want to subscribe to new artists
            assert len(skip_actions) > 0      # Should skip already subscribed
            assert len(unsubscribe_actions) > 0  # Should unsubscribe from "Existing Artist"
    
    def test_file_loading_and_validation(self, temp_artists_file):
        """Test file loading and artist parsing."""
        config = Config(artists_file=temp_artists_file)
        
        with patch('ytmusic_manager.youtube.webdriver.Chrome'):
            client = Mock()
            engine = SyncEngine(client, config)
            
            artists = engine.load_target_artists()
            
            # Should load 4 artists (excluding comments and empty lines)
            assert len(artists) == 4
            
            # Check first artist (no tags)
            assert artists[0].name == "Artist One"
            assert artists[0].tags == []
            
            # Check second artist (with tags)
            assert artists[1].name == "Artist Two"
            assert artists[1].tags == ["rock", "metal"]
            
            # Check third artist (with tags)
            assert artists[2].name == "Artist Three"
            assert artists[2].tags == ["pop"]
            
            # Check fourth artist (with tags)
            assert artists[3].name == "Artist Four"
            assert artists[3].tags == ["indie", "alternative"]
    
    def test_sync_planning_logic(self):
        """Test sync planning with various scenarios."""
        config = Config(dry_run=True)
        
        with patch('ytmusic_manager.youtube.webdriver.Chrome'):
            client = Mock()
            engine = SyncEngine(client, config)
            
            # Target artists
            target_artists = [
                Artist(name="Keep This"),      # Should skip (already subscribed)
                Artist(name="Add This"),       # Should subscribe (new)
                Artist(name="Add That Too")    # Should subscribe (new)
            ]
            
            # Current subscriptions
            current_subscriptions = [
                Artist(name="Keep This", status=SubscriptionStatus.SUBSCRIBED),    # In target
                Artist(name="Remove This", status=SubscriptionStatus.SUBSCRIBED)   # Not in target
            ]
            
            actions = engine.plan_sync(target_artists, current_subscriptions)
            
            # Categorize actions
            subscribe_actions = [a for a in actions if a.action.value == "subscribe"]
            skip_actions = [a for a in actions if a.action.value == "skip"]
            unsubscribe_actions = [a for a in actions if a.action.value == "unsubscribe"]
            
            # Verify planning
            assert len(subscribe_actions) == 2    # "Add This", "Add That Too"
            assert len(skip_actions) == 1         # "Keep This"
            assert len(unsubscribe_actions) == 1  # "Remove This"
            
            # Check specific actions
            subscribe_names = [a.artist.name for a in subscribe_actions]
            assert "Add This" in subscribe_names
            assert "Add That Too" in subscribe_names
            
            assert skip_actions[0].artist.name == "Keep This"
            assert unsubscribe_actions[0].artist.name == "Remove This"
    
    def test_case_insensitive_matching(self):
        """Test that artist matching is case insensitive."""
        config = Config(dry_run=True)
        
        with patch('ytmusic_manager.youtube.webdriver.Chrome'):
            client = Mock()
            engine = SyncEngine(client, config)
            
            # Mixed case target and current
            target_artists = [Artist(name="Artist Name")]
            current_subscriptions = [Artist(name="ARTIST NAME")]
            
            actions = engine.plan_sync(target_artists, current_subscriptions)
            
            # Should recognize as same artist and skip
            skip_actions = [a for a in actions if a.action.value == "skip"]
            assert len(skip_actions) == 1
    
    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_error_handling_file_not_found(self, mock_exists, mock_open):
        """Test error handling when artists file is missing."""
        mock_exists.return_value = False
        
        config = Config(artists_file="nonexistent.txt")
        
        with patch('ytmusic_manager.youtube.webdriver.Chrome'):
            client = Mock()
            engine = SyncEngine(client, config)
            
            with pytest.raises(FileNotFoundError):
                engine.load_target_artists()
    
    def test_empty_artists_file(self, temp_empty_file):
        """Test handling of empty artists file."""
        config = Config(artists_file=temp_empty_file)
        
        with patch('ytmusic_manager.youtube.webdriver.Chrome'):
            client = Mock()
            engine = SyncEngine(client, config)
            
            artists = engine.load_target_artists()
            assert len(artists) == 0
    
    def test_sync_with_empty_target_and_current(self):
        """Test sync behavior with no target artists and no current subscriptions."""
        config = Config(dry_run=True)
        
        with patch('ytmusic_manager.youtube.webdriver.Chrome'):
            client = Mock()
            engine = SyncEngine(client, config)
            
            actions = engine.plan_sync([], [])
            assert len(actions) == 0
    
    def test_config_validation(self):
        """Test configuration validation and defaults."""
        # Test defaults
        config = Config()
        assert config.artists_file == "artists.txt"
        assert config.max_retries == 3
        assert config.delay_between_actions == 2.0
        assert config.verbose is False
        assert config.dry_run is False
        
        # Test custom values
        custom_config = Config(
            artists_file="custom.txt",
            max_retries=5,
            delay_between_actions=1.0,
            verbose=True,
            dry_run=True
        )
        assert custom_config.artists_file == "custom.txt"
        assert custom_config.max_retries == 5
        assert custom_config.delay_between_actions == 1.0
        assert custom_config.verbose is True
        assert custom_config.dry_run is True


class TestEndToEndScenarios:
    """End-to-end test scenarios."""
    
    def test_typical_user_workflow(self, temp_artists_file):
        """Test a typical user workflow from start to finish."""
        # This test simulates what a user would actually do:
        # 1. Create artists file
        # 2. Run sync in dry-run mode
        # 3. Check results
        
        config = Config(artists_file=temp_artists_file, dry_run=True, verbose=False)
        
        with patch('ytmusic_manager.youtube.webdriver.Chrome') as mock_chrome:
            mock_driver = Mock()
            mock_chrome.return_value = mock_driver
            
            # Simulate some existing subscriptions
            existing_subs = [
                Artist(name="Artist One", status=SubscriptionStatus.SUBSCRIBED),  # In file
                Artist(name="Random Artist", status=SubscriptionStatus.SUBSCRIBED)  # Not in file
            ]
            
            with YouTubeMusicClient(headless=True) as client:
                # Mock the get_subscriptions method
                client.get_subscriptions = Mock(return_value=existing_subs)
                
                engine = SyncEngine(client, config)
                
                # Load target artists
                target_artists = engine.load_target_artists()
                assert len(target_artists) == 4
                
                # Get current subscriptions
                current_subs = engine.get_current_subscriptions()
                assert len(current_subs) == 2
                
                # Plan sync
                actions = engine.plan_sync(target_artists, current_subs)
                
                # Should have:
                # - 1 skip (Artist One)
                # - 3 subscribes (Artist Two, Three, Four)
                # - 1 unsubscribe (Random Artist)
                assert len(actions) == 5
                
                # Execute sync (dry run)
                result = engine.execute_sync(actions)
                
                # All actions should be recorded (dry run doesn't fail)
                assert result.total_processed == 5
                assert result.error_count == 0
                
                # Check action distribution
                assert result.success_count == 4  # 3 subscribes + 1 unsubscribe
                assert result.skip_count == 1     # 1 skip
    
    def test_performance_with_large_artist_list(self):
        """Test performance characteristics with a large artist list."""
        # Create a large artists file in memory
        large_artist_content = "\n".join([f"Artist {i}|tag{i}" for i in range(1000)])
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(large_artist_content)
            temp_file = f.name
        
        try:
            config = Config(artists_file=temp_file, dry_run=True)
            
            with patch('ytmusic_manager.youtube.webdriver.Chrome'):
                client = Mock()
                client.get_subscriptions = Mock(return_value=[])  # No current subs
                
                engine = SyncEngine(client, config)
                
                # This should complete reasonably quickly
                import time
                start_time = time.time()
                
                result = engine.sync()
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Should complete within reasonable time (this is a loose check)
                assert duration < 10.0  # 10 seconds should be more than enough
                
                # Should process all 1000 artists
                assert result.total_processed == 1000
                assert result.success_count == 1000  # All should be subscribe actions
        
        finally:
            os.unlink(temp_file)