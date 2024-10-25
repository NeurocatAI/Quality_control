# utils/transcription.py
import openai

def transcribe_audio(audio_file):
    with open(audio_file, "rb") as audio:
        transcription = openai.Audio.transcribe(
            model="whisper-1",
            file=audio,
            response_format="text"
        )
    return transcription
