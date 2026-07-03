#!/usr/bin/env python
import os
import sys
import logging

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_utils import get_channels_from_supabase
from utils.supabase_admin import update_sport_channel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# New URL for all channels
BETREWARD_URL = "https://betrewardtv.live/"

def update_all_channel_links():
    """Update all channel links to BetReward TV URL"""
    print(f"Updating all channel links to: {BETREWARD_URL}")
    
    # Get all channels
    channels = get_channels_from_supabase()
    
    if not channels:
        print("❌ No channels found in the database.")
        return False
    
    print(f"Found {len(channels)} channels to update.")
    
    # Update each channel
    success_count = 0
    for channel in channels:
        channel_id = channel.get("id")
        channel_name = channel.get("name_fa", "") or channel.get("name_en", "") or channel.get("name_tr", "") or "Unknown"
        
        # Skip if no ID
        if not channel_id:
            logger.warning(f"Skipping channel with no ID: {channel_name}")
            continue
        
        # Prepare update data
        update_data = {
            "stream_url": BETREWARD_URL
        }
        
        # Update channel
        print(f"Updating channel: {channel_name} (ID: {channel_id})")
        result = update_sport_channel(channel_id, update_data)
        
        if result["success"]:
            success_count += 1
            logger.info(f"Successfully updated channel: {channel_name}")
        else:
            logger.error(f"Failed to update channel {channel_name}: {result.get('error')}")
    
    print(f"\n✅ Successfully updated {success_count} out of {len(channels)} channels.")
    return success_count > 0

if __name__ == "__main__":
    print("Starting channel links update process...\n")
    
    # Update all channel links
    if update_all_channel_links():
        print("\n✨ Channel update completed successfully!")
        print(f"All channels now point to: {BETREWARD_URL}")
    else:
        print("\n❌ Failed to update channel links.")
        sys.exit(1) 