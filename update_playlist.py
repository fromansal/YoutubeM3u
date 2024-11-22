import os
import requests
from bs4 import BeautifulSoup
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_m3u8(youtube_url):
    """Fetch m3u8 link from YouTube URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }
    
    try:
        session = requests.Session()
        
        # Get channel page
        logger.info(f"Fetching channel URL: {youtube_url}")
        response = session.get(youtube_url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find video ID
        for script in soup.find_all('script'):
            if script.string and '"videoId"' in script.string:
                start = script.string.find('"videoId":"') + len('"videoId":"')
                end = script.string.find('"', start)
                video_id = script.string[start:end]
                logger.info(f"Found video ID: {video_id}")
                
                # Get watch page
                watch_url = f'https://www.youtube.com/watch?v={video_id}'
                watch_response = session.get(watch_url, headers=headers)
                
                # Find hlsManifestUrl
                for script in BeautifulSoup(watch_response.content, 'html.parser').find_all('script'):
                    if script.string and 'hlsManifestUrl' in script.string:
                        start = script.string.find('hlsManifestUrl":"') + len('hlsManifestUrl":"')
                        end = script.string.find('"', start)
                        hls_url = script.string[start:end].replace('\\u0026', '&')
                        logger.info(f"Found manifest URL")
                        return hls_url
    except Exception as e:
        logger.error(f"Error fetching m3u8: {e}")
    return None

def update_channel_info():
    """Update the playlist with channel information."""
    try:
        # Setup paths
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
                
                m3u8_url = fetch_m3u8(url)
                if m3u8_url:
                    file.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n')
                    file.write(f'{m3u8_url}\n')
                    success_count += 1
                else:
                    failed_channels.append(name)
        
        # Create result
        result = {
            "status": "success",
            "channels_processed": len(lines),
            "channels_updated": success_count,
            "failed_channels": failed_channels
        }
        
        print(json.dumps(result, indent=2))
        return result
        
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(error_result))
        return error_result

if __name__ == "__main__":
    update_channel_info()
