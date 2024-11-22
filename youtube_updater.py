import yt_dlp
import json
import logging
from datetime import datetime
import tempfile
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_cookie_file():
    """Create a cookie file with required YouTube cookies"""
    cookie_data = """# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	1735689600	CONSENT	YES+cb
.youtube.com	TRUE	/	FALSE	1735689600	VISITOR_INFO1_LIVE	random_value
.youtube.com	TRUE	/	FALSE	1735689600	LOGIN_INFO	random_value"""
    
    temp_cookie_file = os.path.join(tempfile.gettempdir(), 'youtube_cookies.txt')
    with open(temp_cookie_file, 'w') as f:
        f.write(cookie_data)
    return temp_cookie_file

def get_stream_url(url):
    """Get HLS stream URL using yt-dlp with cookies"""
    try:
        logger.info(f"Getting stream URL for: {url}")
        
        # Create cookie file
        cookie_file = create_cookie_file()
        
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'cookiefile': cookie_file,
            'extract_flat': True,
            'youtube_include_dash_manifest': False,
            'preferredformat': 'm3u8',
            'noplaylist': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            
            # Look for HLS format
            for f in formats:
                if f.get('protocol') == 'm3u8' or '.m3u8' in f.get('url', ''):
                    logger.info(f"Found HLS URL")
                    return f['url']
                    
            # Try fallback to manifest URL from info
            manifest_url = info.get('manifest_url') or info.get('url')
            if manifest_url and '.m3u8' in manifest_url:
                logger.info(f"Found manifest URL")
                return manifest_url
            
            logger.warning(f"No HLS URL found for {url}")
            return None
            
    except Exception as e:
        logger.error(f"Error getting stream URL: {str(e)}")
        return None
    finally:
        # Clean up cookie file
        if os.path.exists(cookie_file):
            os.remove(cookie_file)

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
            "failed_channels": failed_channels,
            "playlist_content": playlist_content
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
