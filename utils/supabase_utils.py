import logging
import requests
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY


def _supabase_configured():
    return bool(SUPABASE_URL and (SUPABASE_KEY or SUPABASE_SERVICE_KEY))

def get_channels_from_supabase():
    """
    Fetch all TV channels from Supabase database
    """
    if not _supabase_configured():
        logging.warning("Supabase is not configured; using fallback channel data.")
        all_channels = []
        for category in get_fallback_categories():
            all_channels.extend(get_sample_channels_for_category(category))
        return all_channels
    try:
        logging.info(f"Connecting to Supabase at {SUPABASE_URL}")
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/channels?select=*",
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        logging.info(f"Retrieved {len(data)} channels from Supabase")
        return data
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error fetching channels from Supabase: {e}")
        if e.response:
            logging.error(f"Response: {e.response.status_code} - {e.response.text}")
        
        # Return sample data for all categories
        all_channels = []
        for category in get_fallback_categories():
            all_channels.extend(get_sample_channels_for_category(category))
        return all_channels
    except Exception as e:
        logging.error(f"Error fetching channels from Supabase: {e}")
        
        # Return sample data for all categories
        all_channels = []
        for category in get_fallback_categories():
            all_channels.extend(get_sample_channels_for_category(category))
        return all_channels

def get_channel_by_id(channel_id):
    """
    Fetch a specific channel by ID
    """
    if not _supabase_configured():
        for category in get_fallback_categories():
            for channel in get_sample_channels_for_category(category):
                if str(channel.get("id")) == str(channel_id):
                    return channel
        return None
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/channels?id=eq.{channel_id}&select=*",
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        return data[0] if data else None
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error fetching channel {channel_id} from Supabase: {e}")
        if e.response:
            logging.error(f"Response: {e.response.status_code} - {e.response.text}")
        
        # Try to find the channel in sample data
        for category in get_fallback_categories():
            for channel in get_sample_channels_for_category(category):
                if str(channel.get("id")) == str(channel_id):
                    return channel
        return None
    except Exception as e:
        logging.error(f"Error fetching channel {channel_id} from Supabase: {e}")
        
        # Try to find the channel in sample data
        for category in get_fallback_categories():
            for channel in get_sample_channels_for_category(category):
                if str(channel.get("id")) == str(channel_id):
                    return channel
        return None

def get_channels_by_name_prefix(prefix=""):
    """
    Fetch channels filtered by the first letter of their name
    """
    try:
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        if not prefix:
            # Return all channels if no prefix specified
            return get_channels_from_supabase()
        
        # Filter channels starting with this prefix in name_fa
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/channels?name_fa=like.{prefix}%&select=*",
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        logging.info(f"Retrieved {len(data)} channels with prefix '{prefix}'")
        
        if not data:
            # If no data from Supabase, use fallback data
            sample_channels = get_sample_channels_for_prefix(prefix)
            logging.info(f"Using {len(sample_channels)} sample channels for prefix '{prefix}'")
            return sample_channels
            
        return data
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error fetching channels by prefix {prefix} from Supabase: {e}")
        if e.response:
            logging.error(f"Response: {e.response.status_code} - {e.response.text}")
        
        # Use fallback data
        sample_channels = get_sample_channels_for_prefix(prefix)
        logging.info(f"Using {len(sample_channels)} sample channels for prefix '{prefix}'")
        return sample_channels
    except Exception as e:
        logging.error(f"Error fetching channels by prefix {prefix} from Supabase: {e}")
        
        # Use fallback data
        sample_channels = get_sample_channels_for_prefix(prefix)
        logging.info(f"Using {len(sample_channels)} sample channels for prefix '{prefix}'")
        return sample_channels

def get_channel_first_letters():
    """
    Get all unique first letters from channel names (for grouping)
    """
    try:
        logging.info("Fetching channel first letters from Supabase")
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        # First check if the table exists by getting the table structure
        table_info_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/channels?limit=0",
            headers=headers
        )
        
        if table_info_response.status_code == 404:
            logging.error("The channels table does not exist in Supabase")
            # Create sample data if table doesn't exist
            return get_fallback_first_letters()
        
        # Get all channels
        channels = get_channels_from_supabase()
        
        # Extract unique first letters
        first_letters = set()
        for channel in channels:
            name = channel.get("name_fa", "")
            if not name:
                name = channel.get("name_en", "")
            if name:
                first_letters.add(name[0].upper())
        
        logging.info(f"Found {len(first_letters)} unique first letters: {sorted(first_letters)}")
        
        if not first_letters:
            logging.warning("No first letters found. Using fallback demo first letters.")
            return get_fallback_first_letters()
            
        return sorted(first_letters)
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error fetching channel first letters from Supabase: {e}")
        if e.response:
            logging.error(f"Response: {e.response.status_code} - {e.response.text}")
        # Use fallback categories
        return get_fallback_first_letters()
    except Exception as e:
        logging.error(f"Error fetching channel first letters from Supabase: {e}")
        # Use fallback categories
        return get_fallback_first_letters()

def get_fallback_first_letters():
    """
    Return fallback demo first letters for when Supabase is not available
    """
    return ["ا", "ب", "ت", "ج", "س", "ف"]

def get_fallback_categories():
    """
    Return fallback demo categories for when Supabase is not available
    """
    return ["Sports", "Football", "Basketball", "Tennis"]

def get_sample_channels_for_prefix(prefix):
    """
    Return sample channels for a given prefix when Supabase fails
    """
    all_samples = []
    for category_channels in get_sample_channels_for_category_dict().values():
        all_samples.extend(category_channels)
    
    # Filter by prefix
    return [
        channel for channel in all_samples 
        if channel.get("name_fa", "").startswith(prefix) or 
        channel.get("name_en", "").startswith(prefix)
    ]

def get_sample_channels_for_category(category):
    """
    Return sample channels for a given category when Supabase fails
    """
    return get_sample_channels_for_category_dict().get(category, [])

def get_sample_channels_for_category_dict():
    """
    Return sample channels organized by category
    """
    sample_channels = {
        "Sports": [
            {
                "id": "1",
                "name_en": "ESPN",
                "name_fa": "ای اس پی ان",
                "name_tr": "ESPN",
                "stream_url": "https://example.com/espn",
                "created_at": "2025-03-20T08:26:13.275965+00:00",
                "updated_at": "2025-03-20T08:26:13.275965+00:00"
            },
            {
                "id": "2",
                "name_en": "SKY Sports",
                "name_fa": "اسکای اسپورتس",
                "name_tr": "SKY Sports",
                "stream_url": "https://example.com/sky",
                "created_at": "2025-03-20T08:26:13.275965+00:00",
                "updated_at": "2025-03-20T08:26:13.275965+00:00"
            }
        ],
        "Football": [
            {
                "id": "3",
                "name_en": "BEIN Sports",
                "name_fa": "بین اسپورتس",
                "name_tr": "BEIN Sports",
                "stream_url": "https://example.com/bein",
                "created_at": "2025-03-20T08:26:13.275965+00:00",
                "updated_at": "2025-03-20T08:26:13.275965+00:00"
            },
            {
                "id": "4",
                "name_en": "Premier League TV",
                "name_fa": "تلویزیون لیگ برتر",
                "name_tr": "Premier Lig TV",
                "stream_url": "https://example.com/premier",
                "created_at": "2025-03-20T08:26:13.275965+00:00",
                "updated_at": "2025-03-20T08:26:13.275965+00:00"
            }
        ],
        "Basketball": [
            {
                "id": "5",
                "name_en": "NBA TV",
                "name_fa": "ان بی ای تی وی",
                "name_tr": "NBA TV",
                "stream_url": "https://example.com/nba",
                "created_at": "2025-03-20T08:26:13.275965+00:00",
                "updated_at": "2025-03-20T08:26:13.275965+00:00"
            }
        ],
        "Tennis": [
            {
                "id": "6",
                "name_en": "Tennis Channel",
                "name_fa": "کانال تنیس",
                "name_tr": "Tenis Kanalı",
                "stream_url": "https://example.com/tennis",
                "created_at": "2025-03-20T08:26:13.275965+00:00",
                "updated_at": "2025-03-20T08:26:13.275965+00:00"
            }
        ]
    }
    
    return sample_channels 