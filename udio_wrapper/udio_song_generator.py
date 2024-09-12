import requests
import logging
import os
import time

class SunoSongGenerator:
    API_BASE_URL = "https://udioapi.pro/api"

    def __init__(self, api_token):
        self.api_token = api_token
        self.logger = logging.getLogger(__name__)

    def generate_song(self, title, prompt, gpt_description_prompt="", make_instrumental=False, model="chirp-v3.5"):
        try:
            self.logger.info(f"Generating song with prompt: {prompt}")
            
            payload = {
                "title": title,
                "prompt": prompt,
                "gpt_description_prompt": gpt_description_prompt,
                "custom_mode": False,
                "make_instrumental": make_instrumental,
                "model": model,
                "disable_callback": True,
                "token": self.api_token
            }
            
            response = requests.post(f"{self.API_BASE_URL}/generate", json=payload)
            response.raise_for_status()
            
            data = response.json()
            self.logger.info(f"Suno API response: {data}")
            
            if 'workId' not in data:
                raise ValueError("Unexpected response format from Suno API")
            
            return data['workId']
        except Exception as e:
            self.logger.error(f"Failed to generate song: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate song: {str(e)}")

    def get_audio_urls(self, work_id, max_attempts=60, delay=5):
        try:
            for _ in range(max_attempts):
                response = requests.get(f"{self.API_BASE_URL}/get_result?workId={work_id}&token={self.api_token}")
                response.raise_for_status()
                result = response.json()
                
                if result.get('code') == 200 and result.get('data', {}).get('callbackType') == 'complete':
                    return [item['audio_url'] for item in result['data']['data'] if 'audio_url' in item]
                
                time.sleep(delay)
            
            raise Exception("Timeout: Audio generation took too long or no audio URLs were provided.")
        except Exception as e:
            self.logger.error(f"Failed to get audio URLs: {str(e)}", exc_info=True)
            raise Exception(f"Failed to get audio URLs: {str(e)}")

    def create_complete_song(self, title, prompt, gpt_description_prompt="", make_instrumental=False, model="chirp-v3.5"):
        try:
            # Generate initial song
            work_id = self.generate_song(title, prompt, gpt_description_prompt, make_instrumental, model)
            
            # Get audio URLs
            audio_urls = self.get_audio_urls(work_id)
            
            # Download and save the audio files
            song_paths = []
            for i, url in enumerate(audio_urls):
                song_filename = f"song_{int(time.time())}_{i}.mp3"
                song_path = os.path.join("songs", song_filename)
                os.makedirs("songs", exist_ok=True)
                
                response = requests.get(url)
                response.raise_for_status()
                
                with open(song_path, 'wb') as f:
                    f.write(response.content)
                self.logger.info(f"Song part {i+1} saved successfully at: {song_path}")
                song_paths.append(song_path)
            
            self.logger.info("Complete song sequence generated successfully")
            return song_paths
        except Exception as e:
            self.logger.error(f"Failed to create complete song: {str(e)}")
            raise Exception(f"Failed to create complete song: {str(e)}")
