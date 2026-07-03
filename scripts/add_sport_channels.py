#!/usr/bin/env python
import os
import sys
import logging

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_admin import add_sport_channel
from utils.supabase_utils import get_channels_from_supabase, get_channel_by_id

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def add_sample_channels():
    """Add sample sport TV channels to Supabase"""
    # List of sample channels to add
    channels = [
        {
            "name": "Sky Sports Premier League",
            "category": "Football",
            "description": "Live coverage of Premier League matches",
            "stream_url": "https://example.com/sky-sports-pl",
            "logo_url": "https://example.com/images/sky-sports-pl.png"
        },
        {
            "name": "BT Sport 1",
            "category": "Sports",
            "description": "Live sports coverage including Premier League, Champions League",
            "stream_url": "https://example.com/bt-sport-1",
            "logo_url": "https://example.com/images/bt-sport-1.png"
        },
        {
            "name": "ESPN",
            "category": "Sports",
            "description": "American sports network with coverage of NBA, NFL, MLB",
            "stream_url": "https://example.com/espn",
            "logo_url": "https://example.com/images/espn.png"
        },
        {
            "name": "beIN Sports",
            "category": "Football",
            "description": "Sports channel with focus on football leagues worldwide",
            "stream_url": "https://example.com/bein-sports",
            "logo_url": "https://example.com/images/bein-sports.png"
        },
        {
            "name": "NBA TV",
            "category": "Basketball",
            "description": "24-hour basketball channel featuring NBA games",
            "stream_url": "https://example.com/nba-tv",
            "logo_url": "https://example.com/images/nba-tv.png"
        },
        {
            "name": "Tennis Channel",
            "category": "Tennis",
            "description": "Channel dedicated to tennis tournaments worldwide",
            "stream_url": "https://example.com/tennis-channel",
            "logo_url": "https://example.com/images/tennis-channel.png"
        }
    ]
    
    # Add each channel to Supabase
    for channel in channels:
        logging.info(f"Adding channel: {channel['name']}")
        result = add_sport_channel(
            name=channel["name"],
            category=channel["category"],
            description=channel["description"],
            stream_url=channel["stream_url"],
            logo_url=channel["logo_url"]
        )
        
        if result["success"]:
            logging.info(f"Successfully added channel: {channel['name']}")
        else:
            logging.error(f"Failed to add channel {channel['name']}: {result.get('error')}")
    
    logging.info("Finished adding sample channels")

def add_custom_channel():
    """Add a custom sport TV channel with user input"""
    print("Add a new Sport TV channel to Supabase")
    print("-" * 40)
    
    name = input("Channel name: ")
    
    # Show category options
    print("\nCategory options:")
    categories = ["Sports", "Football", "Basketball", "Tennis", "Formula 1", "Other"]
    for i, cat in enumerate(categories, 1):
        print(f"{i}. {cat}")
    
    category_choice = int(input("\nSelect category (number): "))
    category = categories[category_choice - 1] if 1 <= category_choice <= len(categories) else "Other"
    
    description = input("\nChannel description: ")
    stream_url = input("Stream URL: ")
    logo_url = input("Logo URL: ")
    
    print("\nAdding channel to Supabase...")
    result = add_sport_channel(
        name=name,
        category=category,
        description=description,
        stream_url=stream_url,
        logo_url=logo_url
    )
    
    if result["success"]:
        print(f"\nSuccess! Channel '{name}' added to Supabase.")
    else:
        print(f"\nError adding channel: {result.get('error')}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Add sport TV channels to Supabase")
    parser.add_argument("--sample", action="store_true", help="Add sample channels")
    parser.add_argument("--custom", action="store_true", help="Add a custom channel with interactive prompts")
    
    args = parser.parse_args()
    
    if args.sample:
        add_sample_channels()
    elif args.custom:
        add_custom_channel()
    else:
        parser.print_help() 