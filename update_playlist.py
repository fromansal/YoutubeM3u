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
    """Get direct HLS variant stream URL from YouTube."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    try:
        session = requests.Session()
        response = session.get(youtube_url, headers=headers)
        if response.status_code != 200:
            return None

        # Extract video ID
        video_id = None
        for pattern in [
            r'videoId":"([^"]+)"',
            r'v=([^&]+)',
            r'youtu.be/([^"?/]+)'
        ]:
            match = re.search(pattern, response.text)
            if match:
                video_id = match.group(1)
                break

        if not video_id:
            return None

        # Get watch page
        watch_url = f'https://www.youtube.com/watch?v={video_id}'
        watch_response = session.get(watch_url, headers=headers)
        
        # Look for hlsManifestUrl
        match = re.search(r'"hlsManifestUrl":"([^"]+)"', watch_response.text)
        if match:
            m3u8_url = match.group(1).replace('\\u0026', '&')
            logger.info(f'Found HLS URL for {video_id}')
            
            # Request the m3u8 URL to get the final variant URL
            m3u8_response = session.get(m3u8_url, headers=headers)
            if m3u8_response.status_code == 200:
                # Extract the first variant URL (usually the highest quality)
                lines = m3u8_response.text.splitlines()
                for line in lines:
                    if line.startswith('https://') and '.m3u8' in line:
                        return line

        return None

    except Exception as e:
        logger.error(f'Error getting stream URL: {str(e)}')
        return None

def update_playlist():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        channel_info_path = os.path.join(current_dir, 'channel_info.txt')
        playlist_path = os.path.join(current_dir, 'playlist.m3u')
        log_path = os.path.join(current_dir, 'update_log.txt')

        logger.info(f'Reading from: {channel_info_path}')
        with open(channel_info_path, 'r', encoding='utf-8') as file:
            channels = [line.strip().split('|') for line in file if line.strip()]

        success_count = 0
        failed_channels = []
        playlist_content = '#EXTM3U\n'

        for channel_info in channels:
            if len(channel_info) != 4:
                continue

            name, group, logo, url = [part.strip() for part in channel_info]
            logger.info(f'Processing channel: {name}')

            stream_url = get_stream_url(url)
            if stream_url:
                playlist_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n'
                playlist_content += f'{stream_url}\n'
                success_count += 1
                logger.info(f'Successfully added {name}')
            else:
                failed_channels.append(name)
                logger.warning(f'Failed to get stream for {name}')

        # Write playlist file
        with open(playlist_path, 'w', encoding='utf-8') as file:
            file.write(playlist_content)

        # Update log file
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        log_entry = f"""
Update Time: {timestamp}
Channels Processed: {len(channels)}
Successful Updates: {success_count}
Failed Channels: {', '.join(failed_channels) if failed_channels else 'None'}
{'='*50}
"""
        with open(log_path, 'a', encoding='utf-8') as file:
            file.write(log_entry)

        # Update README
        readme_content = f"""# IPTV Playlist

Last Updated: {timestamp}

## Status
- Total Channels: {len(channels)}
- Working Channels: {success_count}
- Failed Channels: {len(failed_channels)}

## Usage
Add this URL to your IPTV player:
```
https://raw.githubusercontent.com/fromansal/YoutubeM3u/main/playlist.m3u
```
"""
        with open(os.path.join(current_dir, 'README.md'), 'w', encoding='utf-8') as file:
            file.write(readme_content)

        return {
            "status": "success",
            "channels_processed": len(channels),
            "channels_updated": success_count,
            "details": {
                "successful": len(channels) - len(failed_channels),
                "failed": failed_channels
            }
        }

    except Exception as e:
        logger.error(f'Error updating playlist: {str(e)}')
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    result = update_playlist()
    print(json.dumps(result, indent=2))
