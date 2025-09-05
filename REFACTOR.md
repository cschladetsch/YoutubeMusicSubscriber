# Refactor Plan

## Current Issues (Code Smells)

### 🤮 Architecture Problems
- **String concatenation for JS generation**: Python building JavaScript strings
- **Console script injection**: Using browser console as primary interface
- **Brittle DOM scraping**: Fragile selectors that pick up UI noise
- **No separation of concerns**: Everything mixed together
- **No error handling**: Silent failures everywhere
- **No data validation**: Bad input handling

### 🤮 Code Quality Issues
- **Magic strings everywhere**: Hardcoded selectors and delays
- **No type safety**: Python dict/list manipulation without structure
- **No testing**: Impossible to test browser automation
- **Poor abstractions**: Direct DOM manipulation mixed with business logic

## Better Architecture

### Option A: Web Extension
```
├── manifest.json           # Extension manifest
├── background.js           # Service worker
├── content-script.js       # YouTube Music injection
├── popup/
│   ├── popup.html         # UI for artist management
│   ├── popup.js           # Popup logic
│   └── popup.css          # Styling
└── lib/
    ├── api.js             # YouTube Music API wrapper
    ├── storage.js         # Local storage management
    └── sync.js            # Sync logic
```

### Option B: Desktop App (Electron)
```
├── main.js                # Main process
├── renderer/
│   ├── index.html         # UI
│   ├── renderer.js        # Renderer process
│   └── style.css          # Styling
└── lib/
    ├── youtube-api.js     # API integration
    ├── file-manager.js    # artists.txt handling
    └── sync-engine.js     # Sync logic
```

### Option C: Clean CLI Tool
```
├── main.py                # CLI interface
├── lib/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── youtube.py         # YouTube Music interface
│   ├── sync.py            # Sync engine
│   └── models.py          # Data models
├── tests/                 # Unit tests
└── requirements.txt
```

## Recommended: Option C (Clean CLI)

### Why CLI?
- **Testable**: Can unit test all components
- **Maintainable**: Clear separation of concerns  
- **Robust**: Proper error handling and validation
- **Type-safe**: Use dataclasses and type hints
- **Extensible**: Easy to add features

### Core Classes
```python
@dataclass
class Artist:
    name: str
    id: Optional[str] = None
    subscribed: bool = False
    tags: List[str] = field(default_factory=list)

class YouTubeMusicClient:
    def search_artist(self, name: str) -> Optional[Artist]
    def subscribe(self, artist: Artist) -> bool
    def get_subscriptions() -> List[Artist]

class SyncEngine:
    def __init__(self, client: YouTubeMusicClient)
    def sync(self, target_artists: List[Artist]) -> SyncResult
```

Should I implement the clean CLI version?