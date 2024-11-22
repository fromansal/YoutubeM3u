import yt_dlp
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_stream_url(url):
    """Get HLS stream URL using yt-dlp"""
    try:
        logger.info(f"Getting stream URL for: {url}")
        
        ydl_opts = {
            'format': 'best',
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            # Look for HLS format
            for f in formats:
                if f.get('protocol') == 'm3u8' and 'manifest.googlevideo.com' in f.get('url', ''):
                    logger.info(f"Found HLS URL")
                    return f['url']
            
            logger.warning(f"No HLS URL found for {url}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting stream URL: {str(e)}")
        return None

def update_playlist():
    """Update the M3U playlist"""
    try:
        channels = [
            {
                "name": "24 News Malayalam",
                "group": "Malayalam",
                "logo": "https://www.twentyfournews.com/wp-content/themes/nextline_v3/images/logo-new.png",
                "url": "https://www.youtube.com/c/24OnLive/live"
            },
            {
                "name": "Asianet News",
                "group": "Malayalam",
                "logo": "https://upload.wikimedia.org/wikipedia/commons/c/c4/Asianet_News_Logo.png",
                "url": "https://www.youtube.com/user/asianetnews/live"
            },
            {
                "name": "Reporter",
                "group": "Malayalam",
                "logo": "https://yt3.ggpht.com/ytc/AAUvwngYsY0-vY4E8BQ1SvfkhzJKhSQGazUVCU6Li8saGw=s900-c-k-c0x00ffffff-no-rj",
                "url": "https://www.youtube.com/@reporterlive/live"
            }
        ]
        
        playlist_content = '#EXTM3U\n'
        success_count = 0
        failed_channels = []
        
        for channel in channels:
            logger.info(f"\nProcessing channel: {channel['name']}")
            stream_url = get_stream_url(channel['url'])
            
            if stream_url:
                playlist_content += f'#EXTINF:-1 tvg-logo="{channel["logo"]}" group-title="{channel["group"]}",{channel["name"]}\n'
                playlist_content += f'{stream_url}\n'
                success_count += 1
                logger.info(f"Successfully added {channel['name']}")
            else:
                failed_channels.append(channel['name'])
                logger.warning(f"Failed to get stream for {channel['name']}")
        
        # Write playlist file
        with open('playlist.m3u', 'w', encoding='utf-8') as f:
            f.write(playlist_content)
            
        logger.info(f"\nPlaylist updated:")
        logger.info(f"Success: {success_count}")
        logger.info(f"Failed: {len(failed_channels)}")
        
        if failed_channels:
            logger.info(f"Failed channels: {', '.join(failed_channels)}")
            
        return {
            "status": "success",
            "updated": success_count,
            "failed": len(failed_channels),
            "failed_channels": failed_channels
        }
        
    except Exception as e:
        logger.error(f"Error updating playlist: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    result = update_playlist()
    print(json.dumps(result, indent=2))
