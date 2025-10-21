import openai
import tempfile
import os
import io


async def transcribe_audio(file):
    content = await file.read()
    if len(content) > 25 * 1024 * 1024:
        raise ValueError("Audio file too large (max 25MB)")

    audio_file = io.BytesIO(content)
    audio_file.name = file.filename

    transcript = openai.audio.transcriptions.create(model="whisper-1", file=audio_file)
    return transcript.text
