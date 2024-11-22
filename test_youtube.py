import requests
import json
import re
from bs4 import BeautifulSoup

def test_channel(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    print(f"\nTesting URL: {url}")
    
    try:
        session = requests.Session()
        response = session.get(url, headers=headers)
        print(f"Response status: {response.status_code}")
        
        if '"videoId"' in response.text:
            print("Found videoId in response")
            video_id_match = re.search(r'"videoId":"([^"]+)"', response.text)
            if video_id_match:
                video_id = video_id_match.group(1)
                print(f"Video ID: {video_id}")
                
                watch_url = f'https://www.youtube.com/watch?v={video_id}'
                print(f"Getting watch URL: {watch_url}")
                
                watch_response = session.get(watch_url, headers=headers)
                print(f"Watch response status: {watch_response.status_code}")
                
                if '"hlsManifestUrl"' in watch_response.text:
                    print("Found hlsManifestUrl")
                    manifest_match = re.search(r'"hlsManifestUrl":"([^"]+)"', watch_response.text)
                    if manifest_match:
                        manifest_url = manifest_match.group(1).replace('\\u0026', '&')
                        print(f"Manifest URL: {manifest_url}")
                        return manifest_url
                else:
                    print("No hlsManifestUrl found in watch response")
            else:
                print("Could not extract video ID")
        else:
            print("No videoId found in response")
            
        return None
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    channels = [
        "https://www.youtube.com/c/24OnLive/live",
        "https://www.youtube.com/user/asianetnews/live",
        "https://www.youtube.com/@reporterlive/live"
    ]
    
    playlist_content = '#EXTM3U\n'
    channel_info = [
        ("24 News Malayalam", "Malayalam", "https://www.twentyfournews.com/wp-content/themes/nextline_v3/images/logo-new.png"),
        ("Asianet News", "Malayalam", "https://upload.wikimedia.org/wikipedia/commons/c/c4/Asianet_News_Logo.png"),
        ("Reporter", "Malayalam", "https://yt3.ggpht.com/ytc/AAUvwngYsY0-vY4E8BQ1SvfkhzJKhSQGazUVCU6Li8saGw=s900-c-k-c0x00ffffff-no-rj")
    ]
    
    for (name, group, logo), url in zip(channel_info, channels):
        print(f"\nProcessing {name}")
        m3u8_url = test_channel(url)
        if m3u8_url:
            playlist_content += f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n'
            playlist_content += f'{m3u8_url}\n'
    
    with open('playlist.m3u', 'w', encoding='utf-8') as f:
        f.write(playlist_content)
    
    print("\nPlaylist content:")
    print(playlist_content)
    
if __name__ == "__main__":
    main()
