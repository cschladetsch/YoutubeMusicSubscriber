"""Sync engine for YouTube Music subscriptions."""

import logging
import time
from pathlib import Path
from typing import List, Set

from .models import Artist, SyncAction, SyncActionType, SyncResult, Config, SubscriptionStatus
from .youtube import YouTubeMusicClient


logger = logging.getLogger(__name__)


class SyncEngine:
    """Engine for synchronizing YouTube Music subscriptions."""
    
    def __init__(self, client: YouTubeMusicClient, config: Config):
        """Initialize the sync engine."""
        self.client = client
        self.config = config
    
    def load_target_artists(self) -> List[Artist]:
        """Load target artists from file."""
        artists_file = Path(self.config.artists_file)
        
        if not artists_file.exists():
            raise FileNotFoundError(f"Artists file not found: {artists_file}")
        
        artists = []
        with artists_file.open('r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                try:
                    artist = Artist.from_line(line)
                    artists.append(artist)
                    logger.debug(f"Loaded artist: {artist.name} (tags: {artist.tags})")
                except Exception as e:
                    logger.warning(f"Skipping invalid line {line_num}: {line} - {e}")
        
        logger.info(f"Loaded {len(artists)} target artists from {artists_file}")
        return artists
    
    def get_current_subscriptions(self) -> List[Artist]:
        """Get current YouTube Music subscriptions."""
        logger.info("Fetching current subscriptions...")
        current = self.client.get_subscriptions()
        logger.info(f"Found {len(current)} current subscriptions")
        return current
    
    def plan_sync(self, target_artists: List[Artist], current_subscriptions: List[Artist]) -> List[SyncAction]:
        """Plan sync actions needed."""
        logger.info("Planning sync actions...")
        
        # Create lookup sets for efficient comparison
        current_names = {sub.name.lower() for sub in current_subscriptions}
        target_names = {artist.name.lower() for artist in target_artists}
        
        actions = []
        
        # Artists to subscribe to
        for artist in target_artists:
            if artist.name.lower() not in current_names:
                actions.append(SyncAction(
                    artist=artist,
                    action=SyncActionType.SUBSCRIBE,
                    reason="Not currently subscribed"
                ))
            else:
                actions.append(SyncAction(
                    artist=artist,
                    action=SyncActionType.SKIP,
                    reason="Already subscribed"
                ))
        
        # Artists to unsubscribe from (if not in target list)
        for subscription in current_subscriptions:
            if subscription.name.lower() not in target_names:
                actions.append(SyncAction(
                    artist=subscription,
                    action=SyncActionType.UNSUBSCRIBE,
                    reason="Not in target list"
                ))
        
        subscribe_count = len([a for a in actions if a.action == SyncActionType.SUBSCRIBE])
        unsubscribe_count = len([a for a in actions if a.action == SyncActionType.UNSUBSCRIBE])
        skip_count = len([a for a in actions if a.action == SyncActionType.SKIP])
        
        logger.info(f"Planned actions: {subscribe_count} subscribe, {unsubscribe_count} unsubscribe, {skip_count} skip")
        
        return actions
    
    def execute_sync(self, actions: List[SyncAction]) -> SyncResult:
        """Execute sync actions."""
        logger.info("Executing sync actions...")
        
        result = SyncResult()
        
        if self.config.dry_run:
            logger.info("DRY RUN MODE - No actual changes will be made")
        
        for i, planned_action in enumerate(actions, 1):
            if planned_action.action == SyncActionType.SKIP:
                logger.debug(f"[{i}/{len(actions)}] Skipping {planned_action.artist.name}: {planned_action.reason}")
                result.actions_taken.append(planned_action)
                continue
            
            logger.info(f"[{i}/{len(actions)}] {planned_action.action.value.title()} {planned_action.artist.name}")
            
            if self.config.dry_run:
                result.actions_taken.append(planned_action)
                continue
            
            try:
                success = False
                
                if planned_action.action == SyncActionType.SUBSCRIBE:
                    # First search for the artist to get URL
                    found_artist = self.client.search_artist(planned_action.artist.name)
                    if found_artist:
                        planned_action.artist.url = found_artist.url
                        planned_action.artist.id = found_artist.id
                        success = self.client.subscribe_to_artist(planned_action.artist)
                        if success:
                            result.actions_taken.append(planned_action)
                            logger.info(f"✅ Successfully {planned_action.action.value}d {planned_action.artist.name}")
                        else:
                            result.errors.append(f"Failed to {planned_action.action.value} {planned_action.artist.name}")
                            logger.error(f"❌ Failed to {planned_action.action.value} {planned_action.artist.name}")
                    else:
                        result.errors.append(f"Could not find artist: {planned_action.artist.name}")
                
                elif planned_action.action == SyncActionType.UNSUBSCRIBE:
                    # TODO: Implement unsubscribe functionality
                    logger.warning(f"Unsubscribe not yet implemented for: {planned_action.artist.name}")
                    result.errors.append(f"Unsubscribe not implemented: {planned_action.artist.name}")
                
                # Rate limiting
                if self.config.delay_between_actions > 0:
                    time.sleep(self.config.delay_between_actions)
                    
            except Exception as e:
                error_msg = f"Error {planned_action.action.value}ing {planned_action.artist.name}: {e}"
                result.errors.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        logger.info(f"Sync complete: {result.success_count} successful, {result.error_count} errors, {result.skip_count} skipped")
        
        return result
    
    def sync(self) -> SyncResult:
        """Perform complete sync operation."""
        logger.info("Starting YouTube Music sync...")
        
        try:
            # Load target artists
            target_artists = self.load_target_artists()
            
            # Get current subscriptions
            current_subscriptions = self.get_current_subscriptions()
            
            # Plan sync actions
            actions = self.plan_sync(target_artists, current_subscriptions)
            
            # Execute sync
            result = self.execute_sync(actions)
            
            return result
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            result = SyncResult()
            result.errors.append(f"Sync failed: {e}")
            return result