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
    """Get direct HLS variant stream URL from YouTube."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    try:
        # Create session
        session = requests.Session()
        
        # First get the channel page
        logger.info(f'Fetching channel URL: {youtube_url}')
        response = session.get(youtube_url, headers=headers, timeout=15)
        logger.info(f'Channel page status code: {response.status_code}')
        
        if response.status_code != 200:
            logger.error(f'Failed to get channel page: {response.status_code}')
            return None

        # Look for video ID
        video_id = None
        video_patterns = [
            r'"videoId":"([^"]+)"',
            r'v=([^&]+)',
            r'youtu.be/([^"?/]+)'
        ]
        
        for pattern in video_patterns:
            match = re.search(pattern, response.text)
            if match:
                video_id = match.group(1)
                logger.info(f'Found video ID: {video_id}')
                break

        if not video_id:
            logger.error('No video ID found')
            # Save response for debugging
            with open('channel_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            return None

        # Get the watch page
        watch_url = f'https://www.youtube.com/watch?v={video_id}'
        logger.info(f'Fetching watch URL: {watch_url}')
        watch_response = session.get(watch_url, headers=headers, timeout=15)
        logger.info(f'Watch page status code: {watch_response.status_code}')

        if watch_response.status_code != 200:
            logger.error(f'Failed to get watch page: {watch_response.status_code}')
            return None

        # Save watch page response for debugging
        with open('watch_response.html', 'w', encoding='utf-8') as f:
            f.write(watch_response.text)

        # Look for hlsManifestUrl
        manifest_match = re.search(r'"hlsManifestUrl":"([^"]+)"', watch_response.text)
        if manifest_match:
            manifest_url = manifest_match.group(1).replace('\\u0026', '&')
            logger.info(f'Found manifest URL: {manifest_url}')
            
            # Get the manifest content
            manifest_response = session.get(manifest_url, headers=headers, timeout=15)
            logger.info(f'Manifest response status code: {manifest_response.status_code}')
            
            if manifest_response.status_code == 200:
                # Save manifest content for debugging
                with open('manifest_response.txt', 'w', encoding='utf-8') as f:
                    f.write(manifest_response.text)
                
                # Extract the highest quality variant URL
                variants = [line for line in manifest_response.text.splitlines() 
                          if line.startswith('https://') and '.m3u8' in line]
                
                if variants:
                    logger.info(f'Found {len(variants)} variant URLs')
                    return variants[0]
                else:
                    logger.error('No variant URLs found in manifest')
            else:
                logger.error(f'Failed to get manifest: {manifest_response.status_code}')
        else:
            logger.error('No manifest URL found in watch page')

        return None

    except Exception as e:
        logger.error(f'Error in get_stream_url: {str(e)}')
        return None

def update_playlist():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        channel_info_path = os.path.join(current_dir, 'channel_info.txt')
        playlist_path = os.path.join(current_dir, 'playlist.m3u')
        log_path = os.path.join(current_dir, 'update_log.txt')

        # Ensure we can read the channel info
        if not os.path.exists(channel_info_path):
            logger.error(f'Channel info file not found: {channel_info_path}')
            return {"status": "error", "message": "Channel info file not found"}

        # Read channel info
        logger.info(f'Reading channel info from: {channel_info_path}')
        with open(channel_info_path, 'r', encoding='utf-8') as file:
            content = file.read()
            logger.info(f'Channel info content:\n{content}')
            channels = [line.strip().split('|') for line in content.splitlines() if line.strip()]

        logger.info(f'Found {len(channels)} channels')
        
        # Process channels
        success_count = 0
        failed_channels = []
        playlist_content = '#EXTM3U\n'

        for channel_info in channels:
            if len(channel_info) != 4:
                logger.error(f'Invalid channel info format: {channel_info}')
                continue

            name, group, logo, url = [part.strip() for part in channel_info]
            logger.info(f'\nProcessing channel: {name}')
            logger.info(f'URL: {url}')

            stream_url = get_stream_url(url)
            if stream_url:
                logger.info(f'Got stream URL for {name}: {stream_url}')
                playlist_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n'
                playlist_content += f'{stream_url}\n'
                success_count += 1
            else:
                logger.error(f'Failed to get stream URL for {name}')
                failed_channels.append(name)

        # Write playlist file
        logger.info(f'Writing playlist to: {playlist_path}')
        logger.info(f'Playlist content:\n{playlist_content}')
        
        with open(playlist_path, 'w', encoding='utf-8') as file:
            file.write(playlist_content)

        # Update log
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

        result = {
            "status": "success",
            "channels_processed": len(channels),
            "channels_updated": success_count,
            "failed_channels": failed_channels,
            "playlist_content": playlist_content
        }
        
        logger.info(f'Final result: {json.dumps(result, indent=2)}')
        return result

    except Exception as e:
        logger.error(f'Error in update_playlist: {str(e)}')
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    result = update_playlist()
    print(json.dumps(result, indent=2))
