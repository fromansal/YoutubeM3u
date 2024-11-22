import os
import requests
from bs4 import BeautifulSoup
import logging
import json
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_hls_stream(manifest_url):
    """Get the actual HLS stream URL from the manifest"""
    try:
        # Get the manifest content
        response = requests.get(manifest_url)
        if response.status_code == 200:
            # Get the highest quality stream URL
            streams = [line for line in response.text.split('\n') if line.startswith('https://')]
            if streams:
                return streams[0]  # Return the first (highest quality) stream URL
    except Exception as e:
        logger.error(f"Error getting HLS stream: {e}")
    return None

def fetch_m3u8(youtube_url):
    """Fetch m3u8 link from YouTube URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        session = requests.Session()
        
        # Get initial page
        logger.info(f"Fetching URL: {youtube_url}")
        response = session.get(youtube_url, headers=headers)
        
        # Get video ID
        video_id = None
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup.find_all('script'):
            if script.string and '"videoId"' in script.string:
                match = re.search(r'"videoId":"([^"]+)"', script.string)
                if match:
                    video_id = match.group(1)
                    break
        
        if not video_id:
            logger.warning("No video ID found")
            return None
            
        logger.info(f"Found video ID: {video_id}")
        
        # Get watch page
        watch_url = f'https://www.youtube.com/watch?v={video_id}'
        watch_response = session.get(watch_url, headers=headers)
        
        # Find manifest URL
        manifest_match = re.search(r'"hlsManifestUrl":"([^"]+)"', watch_response.text)
        if manifest_match:
            manifest_url = manifest_match.group(1).replace('\\u0026', '&')
            logger.info("Found manifest URL")
            
            # Get the actual stream URL
            stream_url = get_hls_stream(manifest_url)
            if stream_url:
                logger.info("Found stream URL")
                return stream_url
                
        logger.warning("No stream URL found")
        return None
        
    except Exception as e:
        logger.error(f"Error in fetch_m3u8: {e}")
        return None

def update_channel_info():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        channel_info_path = os.path.join(current_dir, 'channel_info.txt')
        playlist_path = os.path.join(current_dir, 'playlist.m3u')
        
        # Read channels
        with open(channel_info_path, 'r', encoding='utf-8') as file:
            lines = [line.strip() for line in file if line.strip()]
        
        success_count = 0
        failed_channels = []
        
        # Create playlist
        with open(playlist_path, 'w', encoding='utf-8') as file:
            file.write('#EXTM3U\n')
            
            for line in lines:
                parts = [part.strip() for part in line.split('|')]
                if len(parts) != 4:
                    continue
                
                name, group, logo, url = parts
                logger.info(f"Processing channel: {name}")
                
                stream_url = fetch_m3u8(url)
                if stream_url:
                    file.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n')
                    file.write(f'{stream_url}\n')
                    success_count += 1
                    logger.info(f"Added stream for {name}")
                else:
                    failed_channels.append(name)
                    logger.warning(f"Failed to get stream for {name}")
        
        result = {
            "status": "success",
            "channels_processed": len(lines),
            "channels_updated": success_count,
            "failed_channels": failed_channels
        }
        
        print(json.dumps(result, indent=2))
        return result
        
    except Exception as e:
        logger.error(f"Error updating playlist: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    update_channel_info()
