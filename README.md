# YouTube Music Artist Subscriber

A simple browser script to bulk subscribe to artists on YouTube Music from a text file list.

## Files

- `artists.txt` - List of artists to subscribe to (one per line)
- `simple_subscribe.py` - Generator script that creates the browser JavaScript
- `youtube_music_subscriber.js` - Generated browser script (created by running the Python script)

## Requirements

- Python 3.x
- A web browser with YouTube Music access

## How to Use

### Step 1: Edit Your Artist List
1. Edit `artists.txt` and add/remove artists (one per line)
2. Example:
   ```
   Gramatik
   Too Many Zooz
   Funky Destination
   ```

### Step 2: Generate Browser Script
```bash
python3 simple_subscribe.py
```
This reads `artists.txt` and generates `youtube_music_subscriber.js`

### Step 3: Run in Browser
1. **Open YouTube Music** in your browser and log in
2. **Open Developer Console** (Press F12 → Console tab)
3. **Copy and paste** the entire contents of `youtube_music_subscriber.js`
4. **Choose a method:**
   - `subscribeNext()` - Process artists one at a time
   - `subscribeAll()` - Open all artists in separate tabs

## Methods

### Method 1: One by One (`subscribeNext()`)
- Searches for one artist at a time
- You click "Subscribe" and then run `subscribeNext()` for the next artist
- Slower but more controlled

### Method 2: All at Once (`subscribeAll()`)
- Opens all artists in separate browser tabs
- You can quickly click through each tab and subscribe
- Faster for bulk operations

## Workflow for Updates

1. **Edit** `artists.txt` (add/remove artists)
2. **Run** `python3 simple_subscribe.py` 
3. **Copy/paste** the updated `youtube_music_subscriber.js` into browser console

## Notes

- Browser JavaScript cannot read local files due to security restrictions, so the generator approach is required
- Make sure you're logged into YouTube Music
- Some artists might already be subscribed - the script will handle this
- The script respects rate limits with delays between requests
- Works with any modern browser (Chrome, Firefox, Safari, etc.)
