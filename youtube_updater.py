import os
import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver():
    """Setup Chrome driver with appropriate options"""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920x1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def fetch_m3u8(youtube_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }
    logging.info(f'Fetching m3u8 link for URL: {youtube_url.strip()}')
    try:
        response = requests.get(youtube_url.strip(), headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup.find_all('script'):
            if 'hlsManifestUrl' in script.text:
                start = script.text.find('hlsManifestUrl') + len('hlsManifestUrl":"')
                end = script.text.find('",', start)
                m3u8_url = script.text[start:end].replace('\\u0026', '&')
                logging.info(f'Found m3u8 link: {m3u8_url}')
                return m3u8_url
    except requests.RequestException as e:
        logging.error(f'Error fetching m3u8 link: {e}')
    logging.warning(f'No m3u8 link found for URL: {youtube_url.strip()}')
    return None

def update_playlist():
    """Update the M3U playlist"""
    try:
        driver = setup_driver()
        
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
            stream_url = get_stream_url(driver, channel['url'])
            
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
            
        driver.quit()
        
        return {
            "status": "success",
            "updated": success_count,
            "failed": len(failed_channels),
            "failed_channels": failed_channels,
            "playlist_content": playlist_content
        }
        
    except Exception as e:
        logger.error(f"Error updating playlist: {str(e)}")
        if 'driver' in locals():
            driver.quit()
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    result = update_playlist()
    print(json.dumps(result, indent=2))
