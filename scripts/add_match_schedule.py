#!/usr/bin/env python
import os
import sys
import logging
import requests
import json

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_tv_schedule_table():
    """Create the tv_schedule table in Supabase if it doesn't exist"""
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Check if table exists by making a query
        check_response = requests.get(
            f"{SUPABASE_URL}/rest/v1/tv_schedule?limit=1",
            headers=headers
        )
        
        # If table exists, return success
        if check_response.status_code == 200:
            logging.info("tv_schedule table already exists")
            return {"success": True, "message": "Table already exists"}
        
        # Create SQL query to create the table
        sql_query = """
        CREATE TABLE IF NOT EXISTS tv_schedule (
            id SERIAL PRIMARY KEY,
            channel_id TEXT NOT NULL,
            time TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Execute SQL query
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/execute_sql",
            headers=headers,
            json={"query": sql_query}
        )
        
        if response.status_code in (200, 201):
            logging.info("Successfully created tv_schedule table")
            return {"success": True, "message": "Table created successfully"}
        else:
            logging.error(f"Error creating table: {response.status_code} - {response.text}")
            return {"success": False, "error": f"Error creating table: {response.status_code} - {response.text}"}
            
    except Exception as e:
        error_msg = f"Error creating tv_schedule table: {e}"
        logging.error(error_msg)
        return {"success": False, "error": error_msg}

def add_match_to_supabase(channel_id, time, title):
    """
    Add a match to the tv_schedule table in Supabase
    
    Args:
        channel_id (str): The channel ID
        time (str): Match time (format: "HH:MM")
        title (str): Match title
    
    Returns:
        dict: Success status and message
    """
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Prepare match data
        match_data = {
            "channel_id": channel_id,
            "time": time,
            "title": title
        }
        
        # Add match to Supabase
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/tv_schedule",
            headers=headers,
            data=json.dumps(match_data)
        )
        
        response.raise_for_status()
        
        logging.info(f"Successfully added match: {title} at {time} on {channel_id}")
        return {"success": True, "message": "Match added successfully"}
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error adding match to Supabase: {e}"
        if e.response:
            error_msg += f" Response: {e.response.status_code} - {e.response.text}"
        logging.error(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Error adding match to Supabase: {e}"
        logging.error(error_msg)
        return {"success": False, "error": error_msg}

def add_sample_matches():
    """Add sample matches from the screenshot to Supabase"""
    # First, create table if it doesn't exist
    table_result = create_tv_schedule_table()
    if not table_result["success"]:
        logging.error(f"Failed to create table: {table_result.get('error')}")
        return False
    
    matches = [
        {"channel_id": "channel3", "time": "13:30", "title": "Manisa FK - Keçiörengücü"},
        {"channel_id": "channel5", "time": "14:30", "title": "Everton - Arsenal"},
        {"channel_id": "channel4", "time": "13:30", "title": "Ç.Rizespor - Sivasspor"},
        {"channel_id": "channel_1742022421291_558", "time": "20:00", "title": "Kasımpaşa - Beşiktaş"},
        {"channel_id": "channel_1742081729008_514", "time": "19:00", "title": "Bahçeşehir Klj - Petkimspor"},
        {"channel_id": "channel_1742083613760_349", "time": "22:00", "title": "Barcelona - B.Dortmund"},
        {"channel_id": "channel1", "time": "20:00", "title": "Boluspor - Sakaryaspor"},
    ]
    
    # First, clear existing matches
    try:
        clear_existing_matches()
    except Exception as e:
        logging.warning(f"Error clearing matches: {e}")
    
    # Add each match to Supabase
    success_count = 0
    for match in matches:
        logging.info(f"Adding match: {match['title']} at {match['time']}")
        result = add_match_to_supabase(
            channel_id=match["channel_id"],
            time=match["time"],
            title=match["title"]
        )
        
        if result["success"]:
            success_count += 1
        else:
            logging.error(f"Failed to add match {match['title']}: {result.get('error')}")
    
    logging.info(f"Added {success_count} out of {len(matches)} matches successfully")
    return success_count == len(matches)

def clear_existing_matches():
    """Clear all existing matches from the table"""
    try:
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json"
        }
        
        # Delete all matches
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/tv_schedule",
            headers=headers
        )
        
        response.raise_for_status()
        logging.info("Successfully cleared all existing matches")
        
    except Exception as e:
        logging.error(f"Error clearing matches: {e}")
        raise

def add_custom_match():
    """Add a custom match with user input"""
    # First, create table if it doesn't exist
    table_result = create_tv_schedule_table()
    if not table_result["success"]:
        print(f"\nFailed to create table: {table_result.get('error')}")
        return False
    
    print("Add a new match to Supabase")
    print("-" * 40)
    
    channel_id = input("Channel ID: ")
    time = input("Time (HH:MM): ")
    title = input("Match title: ")
    
    print("\nAdding match to Supabase...")
    result = add_match_to_supabase(
        channel_id=channel_id,
        time=time,
        title=title
    )
    
    if result["success"]:
        print(f"\nSuccess! Match '{title}' added to Supabase.")
        return True
    else:
        print(f"\nError adding match: {result.get('error')}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Add match schedule to Supabase")
    parser.add_argument("--sample", action="store_true", help="Add sample matches from screenshot")
    parser.add_argument("--custom", action="store_true", help="Add a custom match with interactive prompts")
    parser.add_argument("--clear", action="store_true", help="Clear all existing matches")
    parser.add_argument("--create-table", action="store_true", help="Create the tv_schedule table")
    
    args = parser.parse_args()
    
    if args.create_table:
        result = create_tv_schedule_table()
        if result["success"]:
            print("✅ Table created or already exists!")
        else:
            print(f"❌ Error creating table: {result.get('error')}")
    elif args.clear:
        try:
            clear_existing_matches()
            print("✅ All matches cleared successfully")
        except Exception as e:
            print(f"❌ Error clearing matches: {e}")
    elif args.sample:
        success = add_sample_matches()
        if success:
            print("✅ All sample matches added successfully")
        else:
            print("❌ There were errors adding some or all matches")
    elif args.custom:
        add_custom_match()
    else:
        parser.print_help() 