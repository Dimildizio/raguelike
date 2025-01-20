import requests
import base64
import io
import pygame as pg


class TTSHandler:
    def __init__(self):
        self.api_url = "http://localhost:1920/tts"

    def generate_and_play_tts(self, text, voice_type="a"):
        """
        Sends text to TTS API, converts response to pygame Sound, and plays it
        """
        try:
            print('PAYLOAD:', self.api_url, {"text": text, "voice_type": voice_type})
            response = requests.post(self.api_url, json={"text": text, "voice_type": voice_type})
            response.raise_for_status()

            audio_data = base64.b64decode(response.json()["audio"])
            audio_buffer = io.BytesIO(audio_data)
            return audio_buffer
        except requests.RequestException as e:
            print(f"Error request making TTS request: {e}")
        except Exception as e:
            print(f"Error processing TTS audio: {e}")

    def test_sound(self, audio_buffer):
        pg.init()
        pg.mixer.init()
        narration_channel = pg.mixer.Channel(1)
        sound = pg.mixer.Sound(audio_buffer)
        narration_channel.play(sound)
        self.wait_for_narration(narration_channel, sound.get_length())
        print("Playback done")
        pg.quit()

    @staticmethod
    def wait_for_narration(narration, length):
        """Wait for current narration to complete"""
        while narration.get_busy():
            pg.time.wait(int(length)+1)


if __name__ == "__main__":
    tts = TTSHandler()
    aboof = tts.generate_and_play_tts("Hello, adventurer, how may i be of help?")
    tts.test_sound(aboof)
