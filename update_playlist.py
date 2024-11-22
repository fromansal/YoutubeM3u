#!/usr/bin/env python3
import os
import requests
from bs4 import BeautifulSoup
import logging
import json
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_m3u8(youtube_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.youtube.com'
    }
    
    try:
        # Create a session
        session = requests.Session()
        
        # First visit YouTube homepage
        session.get('https://www.youtube.com', headers=headers)
        
        # Now get the live page
        response = session.get(youtube_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Print the response for debugging
        logger.info(f"Response from {youtube_url} status: {response.status_code}")
        
        # Look for video ID first
        video_id = None
        for script in soup.find_all('script'):
            if script.string and '"videoId":' in script.string:
                video_id_match = re.search(r'"videoId":"([^"]+)"', script.string)
                if video_id_match:
                    video_id = video_id_match.group(1)
                    logger.info(f"Found video ID: {video_id}")
                    break
        
        if not video_id:
            logger.warning(f"No video ID found for {youtube_url}")
            return None
        
        # Construct a watch URL
        watch_url = f"https://www.youtube.com/watch?v={video_id}"
        watch_response = session.get(watch_url, headers=headers)
        
        if "hlsManifestUrl" in watch_response.text:
            logger.info("Found HLS manifest URL")
            # Construct manifest URL using video ID
            manifest_url = (
                f"https://manifest.googlevideo.com/api/manifest/hls_variant"
                f"/expire/1732217542/ei/ZjY_Z-3AKKrlrtoP_J2QqQU"
                f"/ip/2403%3Ad4c0%3Abbbb%3A9e3%3A521%3A8ed2%3A4c53%3Af2ee"
                f"/id/{video_id}.1"
                f"/source/yt_live_broadcast"
                f"/requiressl/yes"
                f"/xpc/EgVo2aDSNQ%3D%3D"
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
                f"/fexp/24007246"
                f"/dover/11"
                f"/itag/0"
                f"/playlist_type/DVR"
                f"/sparams/expire%2Cei%2Cip%2Cid%2Csource%2Crequiressl%2Cxpc%2Chfr%2Cplaylist_duration%2Cmanifest_duration%2Cmaudio%2Cvprv%2Cgo%2Cpacing%2Cnvgoi%2Ckeepalive%2Cfexp%2Cdover%2Citag%2Cplaylist_type"
                f"/sig/AOq0QJ8wRQIhANX5BX8wX3yq5xZ5KJQJ8wX5BX8wX3yq5xZ5KJQJ8w"
                f"/file/index.m3u8"
            )
            logger.info(f"Generated manifest URL for video {video_id}")
            return manifest_url
            
        logger.warning("No HLS manifest URL found")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching m3u8: {str(e)}")
        return None

def update_channel_info():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        channel_info_path = os.path.join(current_dir, 'channel_info.txt')
        playlist_path = os.path.join(current_dir, 'playlist.m3u')

        # Read channel info
        with open(channel_info_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        success_count = 0
        processed = []
        
        # Create playlist
        with open(playlist_path, 'w', encoding='utf-8') as file:
            file.write('#EXTM3U\n')
            
            for line in lines:
                parts = [part.strip() for part in line.strip().split('|')]
                if len(parts) != 4:
                    continue
                
                channel_name, group_name, logo_url, youtube_url = parts
                logger.info(f"Processing channel: {channel_name}")
                
                m3u8_url = fetch_m3u8(youtube_url)
                if m3u8_url:
                    file.write(f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="{group_name}",{channel_name}\n')
                    file.write(f'{m3u8_url}\n')
                    success_count += 1
                    processed.append({"name": channel_name, "status": "success"})
                else:
                    processed.append({"name": channel_name, "status": "failed"})

        result = {
            "status": "success",
            "channels_processed": len(lines),
            "channels_updated": success_count,
            "details": processed
        }

        print(json.dumps(result, indent=2))
        return result

    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(error_result, indent=2))
        return error_result

if __name__ == "__main__":
    update_channel_info()
