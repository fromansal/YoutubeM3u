import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_m3u8(youtube_url):
    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service('/usr/bin/chromedriver')  # Ensure the correct path to chromedriver
    driver = webdriver.Chrome(service=service, options=options)
    
    logging.info(f'Fetching m3u8 link for URL: {youtube_url.strip()}')
    driver.get(youtube_url.strip())
    try:
        # Wait for the script containing hlsManifestUrl to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//script[contains(text(), 'hlsManifestUrl')]"))
        )
        page_source = driver.page_source
        if 'hlsManifestUrl' in page_source:
            start = page_source.find('hlsManifestUrl') + len('hlsManifestUrl":"')
            end = page_source.find('",', start)
            m3u8_url = page_source[start:end].replace('\\u0026', '&')
            logging.info(f'Found m3u8 link: {m3u8_url}')
            return m3u8_url
    except Exception as e:
        logging.error(f'Error fetching m3u8 link: {e}')
    finally:
        driver.quit()
    logging.warning(f'No m3u8 link found for URL: {youtube_url.strip()}')
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
