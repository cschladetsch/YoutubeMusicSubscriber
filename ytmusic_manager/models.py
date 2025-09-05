"""Data models for YouTube Music Manager."""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class SubscriptionStatus(Enum):
    """Subscription status for an artist."""
    SUBSCRIBED = "subscribed"
    NOT_SUBSCRIBED = "not_subscribed"
    UNKNOWN = "unknown"


class SyncActionType(Enum):
    """Actions that can be taken during sync."""
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SKIP = "skip"


@dataclass
class Artist:
    """Represents a music artist."""
    name: str
    id: Optional[str] = None
    status: SubscriptionStatus = SubscriptionStatus.UNKNOWN
    tags: List[str] = field(default_factory=list)
    url: Optional[str] = None
    
    def __str__(self) -> str:
        return self.name
    
    @classmethod
    def from_line(cls, line: str) -> "Artist":
        """Create Artist from text line with optional tags."""
        if "|" in line:
            parts = line.split("|")
            name = parts[0].strip()
            tags = [tag.strip() for tag in parts[1:] if tag.strip()]
            return cls(name=name, tags=tags)
        else:
            return cls(name=line.strip())


@dataclass
class SyncAction:
    """Represents a sync action to be taken."""
    artist: Artist
    action: SyncActionType
    reason: str


@dataclass
class SyncResult:
    """Result of a sync operation."""
    actions_taken: List[SyncAction] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def success_count(self) -> int:
        """Number of successful actions."""
        return len([a for a in self.actions_taken if a.action != SyncActionType.SKIP])
    
    @property
    def skip_count(self) -> int:
        """Number of skipped actions."""
        return len([a for a in self.actions_taken if a.action == SyncActionType.SKIP])
    
    @property
    def error_count(self) -> int:
        """Number of errors."""
        return len(self.errors)
    
    @property
    def total_processed(self) -> int:
        """Total number of items processed."""
        return len(self.actions_taken)


@dataclass
class Config:
    """Configuration for the YouTube Music Manager."""
    artists_file: str = "artists.txt"
    max_retries: int = 3
    delay_between_actions: float = 2.0
    verbose: bool = False
    dry_run: bool = False