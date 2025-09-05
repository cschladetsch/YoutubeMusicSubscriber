#!/usr/bin/env python3
"""
YouTube Music Artist Subscriber

This program reads a newline-separated list of artists from a file
and subscribes to them all using the ytmusicapi.

Prerequisites:
- pip install ytmusicapi
- Authentication setup (run: ytmusicapi oauth)

Usage:
- Create a text file with artist names, one per line
- Run: python subscribe_artists.py artists.txt
"""

import sys
import time
from pathlib import Path
from ytmusicapi import YTMusic

class ArtistSubscriber:
    def __init__(self):
        try:
            # Initialize YTMusic with OAuth credentials
            self.ytmusic = YTMusic("oauth.json")
        except Exception as e:
            print(f"Error initializing YTMusic: {e}")
            print("Make sure you've run 'ytmusicapi oauth' to set up authentication")
            sys.exit(1)

    def search_artist(self, artist_name):
        """Search for an artist and return the first match."""
        try:
            search_results = self.ytmusic.search(artist_name, filter="artists", limit=1)
            if search_results:
                return search_results[0]
            return None
        except Exception as e:
            print(f"Error searching for {artist_name}: {e}")
            return None

    def subscribe_to_artist(self, artist_id):
        """Subscribe to an artist by their ID."""
        try:
            result = self.ytmusic.subscribe_artists([artist_id])
            return result
        except Exception as e:
            print(f"Error subscribing to artist: {e}")
            return False

    def process_artists_file(self, filename):
        """Read artists from file and subscribe to each one."""
        file_path = Path(filename)
        
        if not file_path.exists():
            print(f"Error: File '{filename}' not found")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            artists = [line.strip() for line in f if line.strip()]

        if not artists:
            print("No artists found in the file")
            return

        print(f"Found {len(artists)} artists to subscribe to:")
        for artist in artists:
            print(f"  - {artist}")
        print()

        successful = 0
        failed = 0

        for artist_name in artists:
            print(f"Processing: {artist_name}...", end=" ")
            
            # Search for the artist
            artist_info = self.search_artist(artist_name)
            if not artist_info:
                print("❌ Not found")
                failed += 1
                continue

            # Subscribe to the artist
            if self.subscribe_to_artist(artist_info['browseId']):
                print(f"✅ Subscribed to {artist_info['artist']}")
                successful += 1
            else:
                print("❌ Failed to subscribe")
                failed += 1

            # Be respectful to the API - add a small delay
            time.sleep(0.5)

        print(f"\nSummary:")
        print(f"Successfully subscribed: {successful}")
        print(f"Failed: {failed}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python subscribe_artists.py <artists_file.txt>")
        print("\nExample artists.txt content:")
        print("The Beatles")
        print("Pink Floyd")
        print("Led Zeppelin")
        print("Queen")
        sys.exit(1)

    filename = sys.argv[1]
    subscriber = ArtistSubscriber()
    subscriber.process_artists_file(filename)

if __name__ == "__main__":
    main()
