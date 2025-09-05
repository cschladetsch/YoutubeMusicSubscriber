#!/usr/bin/env python3
"""YouTube Music Manager - Clean CLI for managing subscriptions."""

import argparse
import logging
import sys
from pathlib import Path

from .models import Config
from .youtube import YouTubeMusicClient
from .sync import SyncEngine

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('youtube_music_manager.log')
    ]
)

logger = logging.getLogger(__name__)


def cmd_sync(args):
    """Sync subscriptions command."""
    config = Config(
        artists_file=args.artists_file,
        verbose=args.verbose,
        dry_run=args.dry_run,
        delay_between_actions=args.delay
    )
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"Starting sync {'(DRY RUN)' if config.dry_run else ''}")
    
    with YouTubeMusicClient(headless=not args.show_browser) as client:
        sync_engine = SyncEngine(client, config)
        
        if args.interactive and not config.dry_run:
            print("WARNING: This will make real changes to your YouTube Music subscriptions!")
            confirm = input("Are you sure you want to continue? (y/N): ")
            if confirm.lower() != 'y':
                print("Cancelled.")
                return 0
        
        result = sync_engine.sync()
        
        print(f"\nSYNC RESULTS:")
        print(f"Successful actions: {result.success_count}")
        print(f"Skipped: {result.skip_count}")  
        print(f"Errors: {result.error_count}")
        
        if result.errors:
            print(f"\nERRORS:")
            for error in result.errors:
                print(f"  • {error}")
            return 1
        
        return 0


def cmd_list(args):
    """List current subscriptions command."""
    logger.info("Listing current subscriptions")
    
    with YouTubeMusicClient(headless=not args.show_browser) as client:
        subscriptions = client.get_subscriptions()
        
        print(f"\nCURRENT SUBSCRIPTIONS ({len(subscriptions)})")
        print("=" * 50)
        
        for i, artist in enumerate(subscriptions, 1):
            print(f"{i:3d}. {artist.name}")
            if artist.url and args.verbose:
                print(f"     URL: {artist.url}")
        
        if args.output:
            output_file = Path(args.output)
            with output_file.open('w', encoding='utf-8') as f:
                for artist in subscriptions:
                    f.write(f"{artist.name}\n")
            print(f"\nSubscriptions saved to: {output_file}")
    
    return 0


def cmd_validate(args):
    """Validate artists file command."""
    artists_file = Path(args.artists_file)
    
    if not artists_file.exists():
        print(f"ERROR: File not found: {artists_file}")
        return 1
    
    valid_artists = []
    errors = []
    
    with artists_file.open('r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            try:
                from .models import Artist
                artist = Artist.from_line(line)
                valid_artists.append(artist)
                if args.verbose:
                    tags_str = f" (tags: {', '.join(artist.tags)})" if artist.tags else ""
                    print(f"VALID Line {line_num}: {artist.name}{tags_str}")
            except Exception as e:
                error_msg = f"Line {line_num}: {line} - {e}"
                errors.append(error_msg)
                if args.verbose:
                    print(f"ERROR: {error_msg}")
    
    print(f"\nVALIDATION RESULTS:")
    print(f"Valid artists: {len(valid_artists)}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print(f"\nErrors:")
        for error in errors:
            print(f"  • {error}")
        return 1
    else:
        print("All entries are valid!")
        return 0


def create_parser():
    """Create argument parser."""
    # Create a parent parser with global options that will be inherited by subcommands
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    global_parser.add_argument('--show-browser', action='store_true', help='Show browser window (default: headless)')
    
    # Main parser
    parser = argparse.ArgumentParser(
        prog='ytmusic-manager',
        description="YouTube Music Manager - Sync your artist subscriptions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[global_parser],
        epilog="""
Examples:
  %(prog)s sync                    # Sync subscriptions (dry-run by default)  
  %(prog)s sync --no-dry-run       # Actually make changes
  %(prog)s list --show-browser     # Show current subscriptions with visible browser
  %(prog)s validate --verbose      # Check artists.txt file with detailed output
        """
    )
    
    parser.add_argument('--version', action='version', version='%(prog)s 0.1.0')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands', required=True)
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync artist subscriptions', parents=[global_parser])
    sync_parser.add_argument('--artists-file', default='artists.txt', help='Artists file path')
    sync_parser.add_argument('--dry-run', action='store_true', default=True, help='Preview changes without making them')
    sync_parser.add_argument('--no-dry-run', dest='dry_run', action='store_false', help='Actually make changes')
    sync_parser.add_argument('--delay', type=float, default=2.0, help='Delay between actions (seconds)')
    sync_parser.add_argument('--interactive', action='store_true', help='Ask for confirmation')
    sync_parser.set_defaults(func=cmd_sync)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List current subscriptions', parents=[global_parser])
    list_parser.add_argument('--output', '-o', help='Save to file')
    list_parser.set_defaults(func=cmd_list)
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate artists file', parents=[global_parser])
    validate_parser.add_argument('--artists-file', default='artists.txt', help='Artists file path')
    validate_parser.set_defaults(func=cmd_validate)
    
    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nCancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())