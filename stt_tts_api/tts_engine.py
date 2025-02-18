from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import numpy as np
import base64
import io
import scipy.io.wavfile as wav
from kokoro import KModel, KPipeline


class TTSRequest(BaseModel):
    text: str
    voice_type: str = "a"


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


class KokoroTTSHandler:
    def __init__(self):
        # Initialize model on CPU
        self.model = KModel().to('cpu').eval()
        self.sample_rate = 24000

        # Initialize pipelines for different language codes
        self.pipelines = {
            'a': KPipeline(lang_code='a', model=False),  # American English
            'b': KPipeline(lang_code='b', model=False)  # British English
        }

        # Add pronunciation for 'kokoro' word
        self.pipelines['a'].g2p.lexicon.golds['kokoro'] = 'kˈOkəɹO'
        self.pipelines['b'].g2p.lexicon.golds['kokoro'] = 'kˈQkəɹQ'

        # Pre-load voices
        for voice in set(VOICE_MAP.values()):
            self.pipelines[voice[0]].load_voice(voice)

    def generate_audio(self, text: str, voice_type: str) -> bytes:
        try:
            # Get voice name from mapping
            print(voice_type)
            voice = VOICE_MAP.get(voice_type, 'af_heart')

            # Get pipeline for this language
            pipeline = self.pipelines[voice[0]]

            # Generate first audio segment
            for _, ps, _ in pipeline(text, voice, speed=1):
                # Get reference style
                ref_s = pipeline.load_voice(voice)[len(ps) - 1]

                # Generate audio
                audio = self.model(ps, ref_s, speed=1)

                # Convert to bytes
                byte_io = io.BytesIO()
                wav.write(byte_io, self.sample_rate, audio.numpy().astype(np.float32))
                return byte_io.getvalue()

        except Exception as e:
            print(f"Error generating audio: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# Create FastAPI app and handler
app = FastAPI()
tts_handler = KokoroTTSHandler()


@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    try:
        audio_bytes = tts_handler.generate_audio(request.text, request.voice_type)
        audio_b64 = base64.b64encode(audio_bytes).decode()
        return {"audio": audio_b64, "sample_rate": tts_handler.sample_rate}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=1920)