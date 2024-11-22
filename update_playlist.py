#!/usr/bin/env python3
import os
import requests
from bs4 import BeautifulSoup
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_file_exists(filepath, default_content=''):
    """Ensure a file exists, create it if it doesn't"""
    if not os.path.exists(filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(default_content)

def update_playlist():
    try:
        # Setup paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        channel_info_path = os.path.join(current_dir, 'channel_info.txt')
        playlist_path = os.path.join(current_dir, 'playlist.m3u')
        log_path = os.path.join(current_dir, 'update_log.txt')
        readme_path = os.path.join(current_dir, 'README.md')

        # Ensure files exist
        ensure_file_exists(playlist_path, '#EXTM3U\n')
        ensure_file_exists(log_path)
        ensure_file_exists(readme_path, '# IPTV Playlist\n')

        # Start update process
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        logger.info(f'Starting update at {timestamp}')

        # Read and process channels
        with open(channel_info_path, 'r', encoding='utf-8') as f:
            channels = [line.strip().split('|') for line in f if line.strip()]

        # Update playlist
        playlist_content = '#EXTM3U\n'
        success_count = 0
        failed_channels = []

        for channel in channels:
            if len(channel) != 4:
                continue
            name, group, logo, url = [part.strip() for part in channel]
            
            try:
                stream_url = get_stream_url(url)
                if stream_url:
                    playlist_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n'
                    playlist_content += f'{stream_url}\n'
                    success_count += 1
                else:
                    failed_channels.append(name)
            except Exception as e:
                logger.error(f'Error processing {name}: {e}')
                failed_channels.append(name)

        # Write updated playlist
        with open(playlist_path, 'w', encoding='utf-8') as f:
            f.write(playlist_content)

        # Update log
        log_entry = f"""
Update Time: {timestamp}
Channels Processed: {len(channels)}
Successful Updates: {success_count}
Failed Channels: {', '.join(failed_channels) if failed_channels else 'None'}
{'='*50}
"""
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

        # Update README
        readme_content = f"""# IPTV Playlist

Last Updated: {timestamp}

## Statistics
- Total Channels: {len(channels)}
- Working Channels: {success_count}
- Failed Channels: {len(failed_channels)}

## Usage
Add this URL to your IPTV player:
```
https://raw.githubusercontent.com/fromansal/YoutubeM3u/main/playlist.m3u
```

## Update Log
Last update status:
```
Successful: {success_count}/{len(channels)}
Failed Channels: {', '.join(failed_channels) if failed_channels else 'None'}
```
"""
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        logger.info('Update completed successfully')
        return {
            "status": "success",
            "timestamp": timestamp,
            "total_channels": len(channels),
            "successful": success_count,
            "failed": len(failed_channels)
        }

    except Exception as e:
        logger.error(f'Update failed: {e}')
        return {
            "status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    result = update_playlist()
    print(json.dumps(result, indent=2))
