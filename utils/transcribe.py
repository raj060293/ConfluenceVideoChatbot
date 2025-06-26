import os
import subprocess
import asyncio
from deepgram import Deepgram
import hashlib
import json

DEEPGRAM_API_KEY = "551e5521166984fcbd8207d439416865d4f2f457"

def get_video_hash(video_path):
    return hashlib.md5(video_path.encode()).hexdigest()

def extract_audio_with_ffmpeg(video_path, audio_path="temp_audio.wav"):
    try:
        command = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise Exception(f"FFmpeg failed to extract audio: {e}")

def transcribe_video_from_url(video_path):
    video_id = get_video_hash(video_path)
    transcript_path = f".cache/transcript_{video_id}.txt"

    # Reuse cached transcript
    if os.path.exists(transcript_path):
        with open(transcript_path, "r") as f:
            return f.read()

    # Else, extract and transcribe
    audio_path = "temp_audio.wav"
    try:
        extract_audio_with_ffmpeg(video_path, audio_path)
        transcript = asyncio.run(transcribe_with_deepgram(audio_path))
        os.makedirs(".cache", exist_ok=True)
        with open(transcript_path, "w") as f:
            f.write(transcript)
        return transcript
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

async def transcribe_with_deepgram(audio_path):
    dg_client = Deepgram(DEEPGRAM_API_KEY)
    with open(audio_path, 'rb') as audio_file:
        source = {'buffer': audio_file, 'mimetype': 'audio/wav'}
        response = await dg_client.transcription.prerecorded(source, {'punctuate': True, 'language': 'en'})

        results = response.get("results")
        if not results:
            raise Exception("No transcription results found")

        return results["channels"][0]["alternatives"][0]["transcript"]
