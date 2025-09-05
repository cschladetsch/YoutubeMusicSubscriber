#!/usr/bin/env python3
"""YouTube Music Manager - Clean CLI for managing subscriptions."""

import argparse
import logging
import sys
from pathlib import Path

from lib.models import Config
from lib.youtube import YouTubeMusicClient
from lib.sync import SyncEngine


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('youtube_music_manager.log')
        ]
    )
    
    # Reduce selenium logging noise
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


def cmd_sync(args):
    """Sync subscriptions command."""
    config = Config(
        artists_file=args.artists_file,
        verbose=args.verbose,
        dry_run=args.dry_run,
        delay_between_actions=args.delay
    )
    
    setup_logging(config.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting YouTube Music Manager")
    
    with YouTubeMusicClient(headless=not args.browser) as client:
        if not args.browser:
            logger.info("Running in headless mode")
        
        client.navigate_to_music()
        
        if args.interactive:
            input("Please log in to YouTube Music in the browser, then press Enter to continue...")
        
        engine = SyncEngine(client, config)
        result = engine.sync()
        
        # Print results
        print("\n" + "="*50)
        print("SYNC RESULTS")
        print("="*50)
        
        if result.success_count > 0:
            print(f"✅ Successful actions: {result.success_count}")
        
        if result.skip_count > 0:
            print(f"⏭️  Skipped actions: {result.skip_count}")
        
        if result.error_count > 0:
            print(f"❌ Errors: {result.error_count}")
            for error in result.errors:
                print(f"   • {error}")
        
        if not result.errors:
            print("🎉 Sync completed successfully!")
            return 0
        else:
            print("⚠️  Sync completed with errors")
            return 1


def cmd_list(args):
    """List current subscriptions command."""
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    with YouTubeMusicClient(headless=not args.browser) as client:
        client.navigate_to_music()
        
        if args.interactive:
            input("Please log in to YouTube Music, then press Enter to continue...")
        
        subscriptions = client.get_subscriptions()
        
        print("\n" + "="*50)
        print(f"CURRENT SUBSCRIPTIONS ({len(subscriptions)})")
        print("="*50)
        
        for i, artist in enumerate(subscriptions, 1):
            print(f"{i:3d}. {artist.name}")
            if args.verbose and artist.url:
                print(f"     {artist.url}")
        
        # Save to file if requested
        if args.output:
            output_file = Path(args.output)
            with output_file.open('w', encoding='utf-8') as f:
                for artist in subscriptions:
                    f.write(f"{artist.name}\n")
            print(f"\n💾 Saved to {output_file}")
    
    return 0


def cmd_validate(args):
    """Validate artists file command."""
    setup_logging(args.verbose)
    
    artists_file = Path(args.artists_file)
    if not artists_file.exists():
        print(f"❌ File not found: {artists_file}")
        return 1
    
    artists = []
    errors = []
    
    with artists_file.open('r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                from lib.models import Artist
                artist = Artist.from_line(line)
                artists.append(artist)
            except Exception as e:
                errors.append(f"Line {line_num}: {line} - {e}")
    
    print(f"\n📋 Validation Results for {artists_file}")
    print("="*50)
    print(f"✅ Valid artists: {len(artists)}")
    
    if errors:
        print(f"❌ Errors: {len(errors)}")
        for error in errors:
            print(f"   • {error}")
        return 1
    else:
        print("🎉 All entries are valid!")
        
        if args.verbose:
            print("\nArtists found:")
            for i, artist in enumerate(artists, 1):
                tags_str = f" (tags: {', '.join(artist.tags)})" if artist.tags else ""
                print(f"{i:3d}. {artist.name}{tags_str}")
    
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="YouTube Music Manager - Sync subscriptions from text file"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--artists-file", 
        default="artists.txt",
        help="Path to artists file (default: artists.txt)"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync subscriptions')
    sync_parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be done without making changes"
    )
    sync_parser.add_argument(
        "--browser", 
        action="store_true",
        help="Show browser (default: headless)"
    )
    sync_parser.add_argument(
        "--interactive", 
        action="store_true",
        help="Pause for manual login"
    )
    sync_parser.add_argument(
        "--delay", 
        type=float, 
        default=2.0,
        help="Delay between actions in seconds (default: 2.0)"
    )
    
    # List command
    list_parser = subparsers.add_parser('list', help='List current subscriptions')
    list_parser.add_argument(
        "--browser", 
        action="store_true",
        help="Show browser (default: headless)"
    )
    list_parser.add_argument(
        "--interactive", 
        action="store_true",
        help="Pause for manual login"
    )
    list_parser.add_argument(
        "--output", "-o",
        help="Save list to file"
    )
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate artists file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'sync':
            return cmd_sync(args)
        elif args.command == 'list':
            return cmd_list(args)
        elif args.command == 'validate':
            return cmd_validate(args)
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())