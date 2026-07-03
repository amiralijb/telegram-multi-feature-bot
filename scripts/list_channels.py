#!/usr/bin/env python
import os
import sys
import json

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.supabase_utils import get_channels_from_supabase

def display_all_channels():
    """Fetch and display all channels from Supabase"""
    print("📺 Fetching all TV channels from Supabase...\n")
    
    # Get all channels
    channels = get_channels_from_supabase()
    
    if not channels:
        print("❌ No channels found in the database.")
        return
    
    print(f"✅ Found {len(channels)} channels!\n")
    
    # Group channels (assuming no category in DB, we'll group by first letter of name)
    channels_by_group = {}
    
    # Add each channel to its group
    for channel in channels:
        name = channel.get("name_fa", "")
        if not name:
            name = channel.get("name_en", "Unnamed")
        
        # Get first letter as group key
        group_key = name[0].upper() if name else "#"
        if group_key not in channels_by_group:
            channels_by_group[group_key] = []
        
        channels_by_group[group_key].append(channel)
    
    # Sort groups alphabetically
    sorted_groups = sorted(channels_by_group.keys())
    
    # Display channels organized by group
    for group in sorted_groups:
        group_channels = channels_by_group[group]
        print(f"\n📋 کانال‌های شروع شده با '{group}' ({len(group_channels)}):")
        print("-" * 70)
        
        for channel in group_channels:
            print(f"🔹 ID: {channel.get('id')}")
            print(f"   نام فارسی: {channel.get('name_fa', 'N/A')}")
            print(f"   نام انگلیسی: {channel.get('name_en', 'N/A')}")
            print(f"   نام ترکی: {channel.get('name_tr', 'N/A')}")
            
            # Print stream URL with truncation if too long
            stream_url = channel.get('stream_url', 'N/A')
            if len(stream_url) > 70:
                stream_url = stream_url[:67] + "..."
            print(f"   آدرس پخش: {stream_url}")
            
            # Print creation date
            print(f"   ایجاد شده در: {channel.get('created_at', 'N/A')}")
            print("-" * 70)

def display_channels_as_json():
    """Fetch and display all channels as JSON"""
    print("📺 Fetching all TV channels from Supabase...\n")
    
    # Get all channels
    channels = get_channels_from_supabase()
    
    if not channels:
        print("❌ No channels found in the database.")
        return
    
    print(f"✅ Found {len(channels)} channels!\n")
    
    # Pretty print the JSON data
    print(json.dumps(channels, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="List all Sport TV channels from Supabase")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--by-name", action="store_true", help="Group channels by name (default: by first letter)")
    
    args = parser.parse_args()
    
    if args.json:
        display_channels_as_json()
    else:
        display_all_channels() 