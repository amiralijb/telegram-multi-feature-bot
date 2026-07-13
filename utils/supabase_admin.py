import logging
import requests
import json
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

def add_sport_channel(name, category, description, stream_url, logo_url):
    """
    Add a new sport TV channel to Supabase
    
    Args:
        name (str): Channel name
        category (str): Channel category (Sports, Football, Basketball, Tennis, etc.)
        description (str): Channel description
        stream_url (str): URL for the live stream
        logo_url (str): URL for the channel logo
    
    Returns:
        dict: The created channel data or error message
    """
    if not _supabase_configured():
        return {"success": False, "error": "Supabase is not configured."}

    if not _supabase_configured():
        return {"success": False, "error": "Supabase is not configured."}
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Prepare channel data
        channel_data = {
            "name": name,
            "category": category,
            "description": description,
            "stream_url": stream_url,
            "logo_url": logo_url
        }
        
        # Add channel to Supabase
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/channels",
            headers=headers,
            data=json.dumps(channel_data)
        )
        
        response.raise_for_status()
        
        # Fetch the created channel
        get_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/channels?name=eq.{name}&select=*",
            headers=headers
        )
        
        if get_response.status_code == 200:
            created_channel = get_response.json()
            if created_channel:
                logging.info(f"Successfully added channel: {name}")
                return {"success": True, "channel": created_channel[0]}
        
        return {"success": True, "message": "Channel added successfully"}
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error adding channel to Supabase: {e}"
        if e.response:
            error_msg += f" Response: {e.response.status_code} - {e.response.text}"
        logging.error(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Error adding channel to Supabase: {e}"
        logging.error(error_msg)
        return {"success": False, "error": error_msg}

def update_sport_channel(channel_id, data):
    """
    Update an existing sport TV channel in Supabase
    
    Args:
        channel_id (str): The ID of the channel to update
        data (dict): Dictionary containing fields to update
                    (name, category, description, stream_url, logo_url)
    
    Returns:
        dict: Success status and message
    """
    if not _supabase_configured():
        return {"success": False, "error": "Supabase is not configured."}
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        # Update channel in Supabase
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/channels?id=eq.{channel_id}",
            headers=headers,
            data=json.dumps(data)
        )
        
        response.raise_for_status()
        logging.info(f"Successfully updated channel ID: {channel_id}")
        return {"success": True, "message": "Channel updated successfully"}
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error updating channel in Supabase: {e}"
        if e.response:
            error_msg += f" Response: {e.response.status_code} - {e.response.text}"
        logging.error(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Error updating channel in Supabase: {e}"
        logging.error(error_msg)
        return {"success": False, "error": error_msg}

def delete_sport_channel(channel_id):
    """
    Delete a sport TV channel from Supabase
    
    Args:
        channel_id (str): The ID of the channel to delete
    
    Returns:
        dict: Success status and message
    """
    if not _supabase_configured():
        return {"success": False, "error": "Supabase is not configured."}
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Delete channel from Supabase
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/channels?id=eq.{channel_id}",
            headers=headers
        )
        
        response.raise_for_status()
        logging.info(f"Successfully deleted channel ID: {channel_id}")
        return {"success": True, "message": "Channel deleted successfully"}
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error deleting channel from Supabase: {e}"
        if e.response:
            error_msg += f" Response: {e.response.status_code} - {e.response.text}"
        logging.error(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Error deleting channel from Supabase: {e}"
        logging.error(error_msg)
        return {"success": False, "error": error_msg} 