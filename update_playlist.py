import os
import time
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_m3u8(youtube_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
    }
    logging.info(f'Fetching m3u8 link for URL: {youtube_url.strip()}')
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(youtube_url.strip(), headers=headers, timeout=30)
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
            logging.error(f'Error fetching m3u8 link: {e}, attempt {attempt + 1}/{retries}')
            if attempt < retries - 1:
                time.sleep(10)  # Wait before retrying
    logging.warning(f'No m3u8 link found for URL: {youtube_url.strip()} after {retries} attempts')
    return None

def update_channel_info():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    channel_info_path = os.path.join(current_dir, 'channel_info.txt')

    with open(channel_info_path, 'r') as file:
        lines = file.readlines()

    playlist_path = os.path.join(current_dir, 'playlist.m3u')
    with open(playlist_path, 'w') as file:
        file.write('#EXTM3U\n')
        for line in lines:
            parts = [part.strip() for part in line.strip().split('|')]
            if len(parts) < 4:
                continue
            channel_name, group_name, logo_url, youtube_url = parts
            m3u8_url = fetch_m3u8(youtube_url)
            if m3u8_url:
                file.write(f'#EXTINF:-1 tvg-logo="{logo_url}" group-title="{group_name}",{channel_name}\n')
                file.write(f'{m3u8_url}\n')

if __name__ == "__main__":
    while True:
        logging.info('Starting update cycle...')
        update_channel_info()
        logging.info('Update cycle complete. Sleeping for 3 hours.')
        time.sleep(10800)  # Sleep for 3 hours (10800 seconds)
