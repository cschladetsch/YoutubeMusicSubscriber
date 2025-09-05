# YouTube Music Auto-Sync

Automatically sync your YouTube Music subscriptions to match a text file list of artists.

## Files

- `artists.txt` - List of artists to subscribe to (one per line)
- `auto_sync.py` - Generator script that creates the browser JavaScript
- `auto_sync.js` - Generated browser script (auto-opens all artist tabs)

## Requirements

- Python 3.x
- A web browser with YouTube Music access

## How to Use

### Step 1: Edit Your Artist List
Edit `artists.txt` and add/remove artists (one per line):
```
Faith No More
Nine Inch Nails
Rammstein
```

### Step 2: Generate Auto-Sync Script
```bash
python3 auto_sync.py
```
This reads `artists.txt` and generates `auto_sync.js`

### Step 3: Auto-Sync in Browser
1. **Open YouTube Music** in your browser and log in
2. **Open Developer Console** (Press F12 → Console tab)
3. **Copy and paste** the entire contents of `auto_sync.js`
4. **All artist tabs open automatically** with 2-second delays
5. **Subscribe to each artist** in the opened tabs

## Workflow for Updates

1. **Edit** `artists.txt` (add/remove artists)
2. **Run** `python3 auto_sync.py` to regenerate the script
3. **Copy/paste** the updated `auto_sync.js` into browser console

## Notes

- The script automatically opens all artists in separate tabs
- No manual commands needed - just paste and it works
- Make sure you're logged into YouTube Music
- Works with any modern browser (Chrome, Firefox, Safari, etc.)
- 2-second delays between tab opens to avoid overwhelming the browser
