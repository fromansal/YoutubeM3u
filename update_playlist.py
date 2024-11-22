import os
import requests
from bs4 import BeautifulSoup
import logging
import json
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_stream_url(youtube_url: str) -> str:
    """Get YouTube stream URL with multiple fallback attempts"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Origin': 'https://www.youtube.com',
        'Referer': 'https://www.youtube.com'
    }

    try:
        # Create session for cookies
        session = requests.Session()

        # First try: Direct URL
        logger.info(f'Trying direct URL: {youtube_url}')
        response = session.get(youtube_url, headers=headers)
        
        # Extract video ID
        video_id = None
        
        # Try different video ID patterns
        patterns = [
            r'videoId":"([^"]+)"',
            r'v=([^&]+)',
            r'embed/([^"?/]+)',
            r'youtu.be/([^"?/]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                video_id = match.group(1)
                logger.info(f'Found video ID: {video_id}')
                break
        
        if not video_id:
            logger.warning('No video ID found')
            return None
            
        # Try to get the stream URL
        watch_url = f'https://www.youtube.com/watch?v={video_id}'
        watch_response = session.get(watch_url, headers=headers)
        
        hls_patterns = [
            r'hlsManifestUrl":"([^"]+)',
            r'dashManifestUrl":"([^"]+)',
            r'url":"([^"]+\.m3u8[^"]*)'
        ]
        
        for pattern in hls_patterns:
            match = re.search(pattern, watch_response.text)
            if match:
                stream_url = match.group(1).replace('\\u0026', '&')
                logger.info(f'Found stream URL for {youtube_url}')
                return stream_url

        # Try alternative manifest URL format
        manifest_url = (
            f"https://manifest.googlevideo.com/api/manifest/hls_playlist"
            f"/expire/1732217543/ei/ZzY_Z8vMJdWC9fwPgsGL4Ac"
            f"/id/{video_id}"
            f"/source/yt_live_broadcast"
            f"/requiressl/yes"
            f"/playlist_type/DVR"
            f"/hfr/1"
            f"/playlist_duration/30"
            f"/manifest_duration/30"
            f"/maxh/4320"
            f"/maudio/1"
            f"/vprv/1"
            f"/go/1"
            f"/pacing/0"
            f"/nvgoi/1"
            f"/keepalive/yes"
            f"/file/index.m3u8"
        )
        
        return manifest_url
        
    except Exception as e:
        logger.error(f'Error getting stream URL for {youtube_url}: {str(e)}')
        return None

def update_playlist():
    try:
        # Ensure directory exists
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Define file paths
        channel_info_path = os.path.join(current_dir, 'channel_info.txt')
        playlist_path = os.path.join(current_dir, 'playlist.m3u')
        log_path = os.path.join(current_dir, 'update_log.txt')
        
        # Read channels
        with open(channel_info_path, 'r', encoding='utf-8') as f:
            channels = [line.strip().split('|') for line in f if line.strip()]
        
        # Process channels
        playlist_content = '#EXTM3U\n'
        success_count = 0
        failed_channels = []
        
        for channel in channels:
            if len(channel) != 4:
                continue
                
            name, group, logo, url = [part.strip() for part in channel]
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
        
        # Write playlist
        with open(playlist_path, 'w', encoding='utf-8') as f:
            f.write(playlist_content)
        
        # Update log
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        log_entry = f"""Update Time: {timestamp}
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

## Status
- Total Channels: {len(channels)}
- Working Channels: {success_count}
- Failed Channels: {len(failed_channels)}

## Usage
Add this URL to your IPTV player:
```
https://raw.githubusercontent.com/fromansal/YoutubeM3u/main/playlist.m3u
```

## Channels
Working channels:
{', '.join([ch[0].strip() for ch, *_ in zip(channels, range(success_count))])}

Failed channels:
{', '.join(failed_channels) if failed_channels else 'None'}
"""
        
        with open(os.path.join(current_dir, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        logger.info('Update completed')
        return {
            "status": "success",
            "updated": success_count,
            "total": len(channels),
            "failed": len(failed_channels)
        }
        
    except Exception as e:
        logger.error(f'Error updating playlist: {str(e)}')
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    result = update_playlist()
    print(json.dumps(result, indent=2))
