#!/usr/bin/env python3
"""
Auto-sync script generator
Creates a browser script that automatically syncs subscriptions to match artists.txt
"""

from pathlib import Path

def load_artists():
    """Load artists from artists.txt"""
    artists_file = Path("artists.txt")
    if not artists_file.exists():
        print("❌ artists.txt not found")
        return []
    
    with open(artists_file, 'r') as f:
        artists = [line.strip() for line in f if line.strip()]
    
    return artists

def generate_auto_sync_script(artists):
    """Generate browser JavaScript that automatically syncs"""
    artists_js = ',\n    '.join([f'"{artist}"' for artist in artists])
    
    script = f'''// Auto-Sync YouTube Music Subscriptions
// Paste this in browser console - it will automatically sync everything

const targetArtists = [
    {artists_js}
];

console.log("🎵 Auto-syncing YouTube Music subscriptions...");
console.log(`📋 Target: ${{targetArtists.length}} artists`);

// Automatically open all target artists in tabs for subscribing
targetArtists.forEach((artist, index) => {{
    setTimeout(() => {{
        console.log(`🔔 Opening: ${{artist}}`);
        window.open(`https://music.youtube.com/search?q=${{encodeURIComponent(artist)}}`, '_blank');
    }}, index * 2000); // 2 second delay between tabs
}});

console.log("✅ All artist tabs will open automatically");
console.log("📝 Subscribe to each artist in the opened tabs");
console.log(`🎯 Total tabs opening: ${{targetArtists.length}}`);
'''
    
    return script

def main():
    print("🎵 Auto-Sync Script Generator")
    print("=" * 50)
    
    # Load artists
    artists = load_artists()
    if not artists:
        return
    
    print(f"📋 Found {len(artists)} artists:")
    for i, artist in enumerate(artists, 1):
        print(f"  {i:2d}. {artist}")
    
    print("\n" + "=" * 50)
    print("🌐 Generating auto-sync script...")
    
    # Generate script
    script = generate_auto_sync_script(artists)
    
    # Save to file
    script_file = Path("auto_sync.js")
    with open(script_file, 'w') as f:
        f.write(script)
    
    print(f"✅ Script saved to: {script_file}")
    print("\n📋 Instructions:")
    print("1. Open YouTube Music in your browser")
    print("2. Open browser console (F12 → Console)")
    print(f"3. Copy and paste the contents of {script_file}")
    print("4. All artist tabs will open automatically - just subscribe to each one")

if __name__ == "__main__":
    main()