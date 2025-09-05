# YouTube Music Artist Subscriber

A simple browser script to bulk subscribe to artists on YouTube Music.

## Files

- `artists.txt` - List of artists to subscribe to (one per line)
- `youtube_music_subscriber.js` - Browser script for automated subscription

## How to Use

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

## Artist List

The script will process these 16 artists:
- Gramatik
- Too Many Zooz  
- Funky Destination
- Meute
- Opiuo
- Parov Stelar
- Otyken
- Adhesive Wombat
- Rammstein
- Odd Chap
- Stupid Human
- Caravan Palace
- Ice Paper
- Phoenix Legend
- The Hu
- Ummet Ozcan

## Adding More Artists

Edit `artists.txt` and add new artists (one per line), then regenerate the script if needed.

## Notes

- Make sure you're logged into YouTube Music
- Some artists might already be subscribed - the script will handle this
- The script respects rate limits with delays between requests
- Works with any modern browser (Chrome, Firefox, Safari, etc.)