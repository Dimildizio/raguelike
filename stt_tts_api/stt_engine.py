from fastapi import FastAPI
import sounddevice as sd
import numpy as np
import torch
from transformers import WhisperProcessor, WhisperForConditionalGeneration

app = FastAPI()


class AudioProcessor:
    def __init__(self):
        print("Loading Whisper model...")
        self.processor = WhisperProcessor.from_pretrained("openai/whisper-tiny")
        self.model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-tiny")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = self.model.to(self.device)
        self.recording = False
        self.audio_data = []
        print(f"Model loaded! Using device: {self.device}")

    def start_recording(self):
        self.audio_data = []
        self.recording = True

        def callback(indata, frames, time, status):
            if status:
                print(f"Status: {status}")
            if self.recording:
                self.audio_data.extend(indata.copy())

        self.stream = sd.InputStream(
            callback=callback,
            channels=1,
            samplerate=16000,
            blocksize=1024,
            dtype=np.float32
        )
        self.stream.start()

    def stop_recording(self):
        self.recording = False
        self.stream.stop()
        self.stream.close()
        return self.process_audio()

    def process_audio(self):
        if not self.audio_data:
            return "No audio recorded"

        audio = np.concatenate(self.audio_data)

        processor_output = self.processor(
            audio,
            sampling_rate=16000,
            return_tensors="pt",
            return_attention_mask=True
        )

        input_features = processor_output.input_features.to(self.device)
        attention_mask = processor_output.attention_mask.to(self.device)

        forced_decoder_ids = self.processor.get_decoder_prompt_ids(language="en", task="transcribe")
        predicted_ids = self.model.generate(
            input_features,
            attention_mask=attention_mask,
            forced_decoder_ids=forced_decoder_ids,
            max_length=128
        )

        return self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]


audio_processor = AudioProcessor()


@app.post("/start_recording")
async def start_recording():
    try:
        audio_processor.start_recording()
        return {"status": "Recording started"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/stop_recording")
async def stop_recording():
    try:
        transcription = audio_processor.stop_recording()
        return {"text": transcription}
    except Exception as e:
        return {"error": str(e)}