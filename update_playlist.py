#!/usr/bin/env python3
import os
import requests
from bs4 import BeautifulSoup
import logging
import json
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_stream_url(youtube_url: str) -> str:
    """Get direct stream URL from YouTube."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        session = requests.Session()
        response = session.get(youtube_url, headers=headers)
        
        if response.status_code == 200:
            video_id_match = re.search(r'videoId":"([^"]+)"', response.text)
            if video_id_match:
                video_id = video_id_match.group(1)
                logger.info(f'Found video ID: {video_id}')
                
                # Construct manifest URL
                manifest_url = (
                    f"https://manifest.googlevideo.com/api/manifest/hls_variant"
                    f"/id/{video_id}"
                    f"/source/yt_live_broadcast"
                    f"/requiressl/yes"
                    f"/playlist_type/DVR"
                    f"/file/index.m3u8"
                )
                return manifest_url
                
        return None
    except Exception as e:
        logger.error(f'Error getting stream URL: {e}')
        return None

def update_playlist():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        channel_info_path = os.path.join(current_dir, 'channel_info.txt')
        playlist_path = os.path.join(current_dir, 'playlist.m3u')
        log_path = os.path.join(current_dir, 'update_log.txt')

        # Read channels
        with open(channel_info_path, 'r', encoding='utf-8') as file:
            channels = [line.strip().split('|') for line in file if line.strip()]

        # Create playlist
        playlist_content = '#EXTM3U\n'
        success_count = 0
        failed_channels = []

        for channel in channels:
            if len(channel) != 4:
                continue
                
            name, group, logo, url = [part.strip() for part in channel]
            logger.info(f'Processing: {name}')
            
            stream_url = get_stream_url(url)
            
            if stream_url:
                playlist_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n'
                playlist_content += f'{stream_url}\n'
                success_count += 1
            else:
                failed_channels.append(name)

        # Write playlist file
        with open(playlist_path, 'w', encoding='utf-8') as file:
            file.write(playlist_content)

        # Write log
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        log_entry = f"""
Update Time: {timestamp}
Channels Processed: {len(channels)}
Successful Updates: {success_count}
Failed Channels: {', '.join(failed_channels) if failed_channels else 'None'}
"""
        with open(log_path, 'a', encoding='utf-8') as file:
            file.write(log_entry + '\n' + '-'*50 + '\n')

        # Create direct link file
        with open('README.md', 'w', encoding='utf-8') as file:
            file.write(f"""# IPTV Playlist

Last updated: {timestamp}

## Direct Links

- [Download Playlist](playlist.m3u)
- [View Update Log](update_log.txt)

## Statistics
- Total Channels: {len(channels)}
- Working Channels: {success_count}
- Failed Channels: {len(failed_channels)}

## Usage
Add this URL to your IPTV player:
```
https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/playlist.m3u
```
""")

        return {
            "status": "success",
            "timestamp": timestamp,
            "channels_processed": len(channels),
            "successful_updates": success_count,
            "failed_channels": failed_channels
        }

    except Exception as e:
        logger.error(f'Error: {str(e)}')
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    result = update_playlist()
    print(json.dumps(result, indent=2))
