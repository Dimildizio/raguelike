import base64
import io
import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from set_kokoro_path import generate, build_model, kokoro_path
import scipy.io.wavfile as wav


VOICE_MAP = {
            'a': 'af_bella',  # default female
            'b': 'bm_lewis',  # default male
            'c': 'am_michael',
            'd': 'bf_emma',
            'e': 'af',
            'f': 'af_sarah',
            'g': 'am_adam',
            'h': 'bf_isabella',
            'i': 'bm_george',
            'j': 'af_nicole',
            'k': 'af_sky'
        }

class TTSRequest(BaseModel):
    text: str
    voice_type: str = "a"


class Voice:
    def __init__(self, name):
        self.name = name
        self.voice = self.get_voice(name)

    @staticmethod
    def get_voice(name):
        return torch.load(kokoro_path + f'/voices/{name}.pt', weights_only=True).to('cpu')


class KokoroTTSHandler:
    def __init__(self):
        self.model = build_model(kokoro_path + '/fp16/kokoro-v0_19-half.pth', 'cpu')
        self.sample_rate = 24000
        self.voices = {key: Voice(value) for key, value in VOICE_MAP.items()}


    def generate_audio(self, text: str, voice_type: str) -> bytes:
        try:
            txt = ' '.join([x.strip() for x in text.replace(r'\n', '').split()])
            print(txt)
            audio, _ = generate(self.model, txt, self.voices[voice_type].voice, lang=self.voices[voice_type].name[0])
            byte_io = io.BytesIO()
            wav.write(byte_io, self.sample_rate, audio.astype(np.float32))
            return byte_io.getvalue()
        except Exception as e:
            print(voice_type, e)
            raise HTTPException(status_code=500, detail=str(e))

tts_handler = KokoroTTSHandler()
app = FastAPI()


@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    try:
        audio_bytes = tts_handler.generate_audio(request.text, request.voice_type)
        audio_b64 = base64.b64encode(audio_bytes).decode()
        return {"audio": audio_b64, "sample_rate": tts_handler.sample_rate}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
