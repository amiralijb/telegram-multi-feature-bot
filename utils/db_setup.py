#!/usr/bin/env python
import os
import sys
import logging
import requests
import json

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SUPABASE_URL, SUPABASE_SERVICE_KEY


def _supabase_configured():
    return bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_table_exists():
    """
    Check if the channels table already exists
    
    Returns:
        bool: True if the table exists, False otherwise
    """
    if not _supabase_configured():
        return False
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Try to get data from the table with a limit of 0
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/channels?limit=0",
            headers=headers
        )
        
        # If we get a 200 response, the table exists
        return response.status_code == 200
        
    except Exception as e:
        logger.error(f"Error checking if table exists: {e}")
        return False

def insert_sample_channels():
    """
    Insert sample sport TV channels data.
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not _supabase_configured():
        return False
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    # Sample channels data
    channels = [
        {
            "name": "beIN SPORTS 1",
            "category": "Football",
            "description": "Main beIN SPORTS channel featuring premium football matches",
            "stream_url": "https://example.com/bein1-stream",
            "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/BeIN_Sports_logo.svg/1280px-BeIN_Sports_logo.svg.png"
        },
        {
            "name": "beIN SPORTS 2",
            "category": "Football",
            "description": "Secondary beIN SPORTS channel for football coverage",
            "stream_url": "https://example.com/bein2-stream",
            "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/BeIN_Sports_logo.svg/1280px-BeIN_Sports_logo.svg.png"
        },
        {
            "name": "ESPN",
            "category": "Sports",
            "description": "Comprehensive sports coverage from ESPN",
            "stream_url": "https://example.com/espn-stream",
            "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/ESPN_logo.svg/1280px-ESPN_logo.svg.png"
        },
        {
            "name": "EuroSport",
            "category": "Sports",
            "description": "European sports coverage",
            "stream_url": "https://example.com/eurosport-stream",
            "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Eurosport_logo_2015.svg/1280px-Eurosport_logo_2015.svg.png"
        },
        {
            "name": "NBA TV",
            "category": "Basketball",
            "description": "Official channel of the NBA",
            "stream_url": "https://example.com/nba-stream",
            "logo_url": "https://upload.wikimedia.org/wikipedia/en/thumb/d/d2/NBA_TV.svg/1280px-NBA_TV.svg.png"
        },
        {
            "name": "S Sport",
            "category": "Football",
            "description": "Turkish sports channel with Premier League coverage",
            "stream_url": "https://example.com/ssport-stream",
            "logo_url": "https://upload.wikimedia.org/wikipedia/tr/0/05/S_Sport_logo.png"
        },
        {
            "name": "TRT Spor",
            "category": "Sports",
            "description": "Turkish national sports channel",
            "stream_url": "https://example.com/trtspor-stream",
            "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/TRT_Spor_logo_%282022%29.svg/1280px-TRT_Spor_logo_%282022%29.svg.png"
        }
    ]
    
    # Insert each channel individually to avoid batch insert issues
    success_count = 0
    for channel in channels:
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/channels",
            headers=headers,
                json=channel
            )
            
            if response.status_code in [200, 201, 204]:
                success_count += 1
                logger.info(f"Added channel: {channel['name']}")
            else:
                logger.error(f"Failed to add {channel['name']}: {response.text}")
                
        except Exception as e:
            logger.error(f"Exception adding channel {channel['name']}: {e}")
    
    logger.info(f"Successfully added {success_count} out of {len(channels)} sample channels")
    return success_count > 0

if __name__ == "__main__":
    print("Checking Supabase setup for Sport TV channels...")
    
    # Check if table exists
    if check_table_exists():
        print("✅ Channels table exists in Supabase")
        
        # Insert sample data if requested
        if len(sys.argv) > 1 and sys.argv[1] == "--with-samples":
            if insert_sample_channels():
                print("✅ Added sample channels successfully")
            else:
                print("❌ Failed to add sample channels")
    else:
        print("❌ Channels table does not exist in Supabase")
        print("\n📝 Instructions to create the table:")
        print("1. Go to your Supabase dashboard: https://app.supabase.io")
        print("2. Select your project")
        print("3. Go to 'Table Editor' in the left sidebar")
        print("4. Click 'New Table'")
        print("5. Set the following:")
        print("   - Name: channels")
        print("   - Columns:")
        print("     - id (uuid, primary key, default: gen_random_uuid())")
        print("     - name (text, not null)")
        print("     - category (text, not null)")
        print("     - description (text)")
        print("     - stream_url (text, not null)")
        print("     - logo_url (text)")
        print("     - created_at (timestamptz, default: now())")
        print("6. Click 'Save'")
        print("\nAfter creating the table, run this script again with --with-samples to add sample data.")
    
    print("\n✨ Setup check complete!")
    print("\nYou can now use the Sport TV functionality in your bot.")
    print("Use 'Sport TV 📺' option in the main menu to access TV channels.") 