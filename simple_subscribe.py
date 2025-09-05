#!/usr/bin/env python3
"""
YouTube Music Artist Subscriber Generator
Reads artists.txt and generates youtube_music_subscriber.js
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
    
    # Fix any merged artist names (like "Parov StelarOtyken")
    fixed_artists = []
    for artist in artists:
        if "Parov StelarOtyken" in artist:
            fixed_artists.extend(["Parov Stelar", "Otyken"])
        else:
            fixed_artists.append(artist)
    
    return fixed_artists

def generate_browser_script(artists):
    """Generate browser JavaScript for subscribing to artists"""
    script = '''// YouTube Music Artist Subscriber
// Auto-generated from artists.txt

const artists = [
'''
    
    for artist in artists:
        script += f'    "{artist}",\n'
    
    script += '''];

let currentIndex = 0;

function subscribeNext() {
    if (currentIndex >= artists.length) {
        console.log("✅ All artists processed!");
        return;
    }
    
    const artist = artists[currentIndex++];
    console.log(`🎵 Processing ${currentIndex}/${artists.length}: ${artist}`);
    
    // Open search in current tab
    const searchUrl = `https://music.youtube.com/search?q=${encodeURIComponent(artist + " music")}`;
    window.location.href = searchUrl;
    
    // Wait for user to subscribe, then continue
    console.log("👆 Click Subscribe button, then run subscribeNext() to continue");
}

// Auto-continue version (opens new tabs)
function subscribeAll() {
    artists.forEach((artist, index) => {
        setTimeout(() => {
            console.log(`🎵 Opening: ${artist}`);
            window.open(`https://music.youtube.com/search?q=${encodeURIComponent(artist)}`, '_blank');
        }, index * 2000); // 2 second delay between opens
    });
}

console.log("🎵 YouTube Music Artist Subscriber Ready!");
console.log(`📋 Found ${artists.length} artists from artists.txt`);
console.log("Commands:");
console.log("  subscribeNext() - Process one artist at a time");
console.log("  subscribeAll()  - Open all artists in new tabs");
console.log("");
console.log("Starting with first artist...");
subscribeNext();
'''
    
    return script

def main():
    print("🎵 YouTube Music Artist Subscriber Generator")
    print("=" * 50)
    
    # Load artists
    artists = load_artists()
    if not artists:
        return
    
    print(f"📋 Found {len(artists)} artists:")
    for i, artist in enumerate(artists, 1):
        print(f"  {i:2d}. {artist}")
    
    print("\n" + "=" * 50)
    print("🌐 Generating browser script...")
    
    # Generate browser automation script
    script = generate_browser_script(artists)
    
    # Save to file
    script_file = Path("youtube_music_subscriber.js")
    with open(script_file, 'w') as f:
        f.write(script)
    
    print(f"✅ Script saved to: {script_file}")
    print("\n📋 Instructions:")
    print("1. Open YouTube Music in your browser")
    print("2. Open browser console (F12 → Console)")
    print(f"3. Copy and paste the contents of {script_file}")
    print("4. Choose subscribeNext() or subscribeAll()")

if __name__ == "__main__":
    main()