import time
import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import os
import tempfile
import asyncio
import edge_tts
import ctypes
import json
import pyttsx3
import urllib.request
import collections
from vosk import Model, KaldiRecognizer
from config import load_config

# 1. PERSONA SETUP (Female Fallback)
engine = pyttsx3.init()
voices = engine.getProperty('voices')
for voice in voices:
    if "zira" in voice.name.lower() or "female" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

def is_connected():
    try:
        urllib.request.urlopen('http://google.com', timeout=1)
        return True
    except:
        return False

async def _generate_voice(text, filepath):
    config = load_config()
    voice = config.get("EDGE_VOICE", "en-US-AvaNeural")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filepath)

def play_audio(filepath):
    alias = "voice_alias"
    mciSendString = ctypes.windll.winmm.mciSendStringW
    mciSendString(f"close {alias}", None, 0, None)
    mciSendString(f"open \"{filepath}\" alias {alias}", None, 0, None)
    mciSendString(f"play {alias} wait", None, 0, None)
    mciSendString(f"close {alias}", None, 0, None)

def speak(text):
    config = load_config()
    use_cloud = config.get("USE_CLOUD_TTS", True)
    salutation = config.get("USER_SALUTATION", "sir")
    
    # Append salutation if it's not already at the very end
    if salutation and not text.strip().lower().endswith(salutation.lower()):
        text = text.strip() + f", {salutation}."
    
    print(f"Silvia: {text}") # Keep internal print for debug
    if is_connected() and use_cloud:
        try:
            temp_mp3 = os.path.join(tempfile.gettempdir(), "silvia_voice.mp3")
            asyncio.run(_generate_voice(text, temp_mp3))
            play_audio(temp_mp3)
            return
        except Exception as e:
            print(f"Cloud TTS Error: {e}")
            
    # Fallback/Offline
    engine.say(text); engine.runAndWait()

# 2. NEURAL GUARD SETUP
def get_vosk_recognizers():
    config = load_config()
    name = config.get("ASSISTANT_NAME", "Silvia").lower()
    aliases = [x.lower() for x in config.get("ASSISTANT_ALIASES", [])]
    
    triggers = [name] + aliases + ["hello", "and", "end", "[unk]"]
    grammar = json.dumps(list(set(triggers)))
    
    try:
        model = Model(model_name="vosk-model-small-en-us-0.15")
        rec_guard = KaldiRecognizer(model, 16000, grammar)
        rec_full = KaldiRecognizer(model, 16000)
        return rec_guard, rec_full
    except Exception as e:
        print(f"Vosk Init Error: {e}")
        return None, None

rec_guard, rec_full = get_vosk_recognizers()

_audio_buffer = collections.deque(maxlen=60)

def wait_for_wake_word():
    config = load_config()
    if not config.get("USE_LOCAL_VOSK", True):
        time.sleep(1)
        return True

    name = config.get("ASSISTANT_NAME", "Silvia").lower()
    aliases = [x.lower() for x in config.get("ASSISTANT_ALIASES", [])]
    triggers = [name] + aliases

    global _audio_buffer
    sample_rate = 16000
    try:
        with sd.RawInputStream(samplerate=sample_rate, blocksize=1600, dtype='int16', channels=1) as stream:
            while True:
                data, _ = stream.read(1600)
                _audio_buffer.append(bytes(data))
                
                if rec_guard and rec_guard.AcceptWaveform(bytes(data)):
                    result = json.loads(rec_guard.Result())
                    text = result.get('text', '')
                    if any(x in text for x in triggers):
                        return True
    except Exception as e:
        print(f"Stream Error: {e}")
        return True

def record_command(duration=5):
    global _audio_buffer
    sample_rate = 16000
    my_recording = b"".join(list(_audio_buffer))
    _audio_buffer.clear()
    
    try:
        with sd.RawInputStream(samplerate=sample_rate, blocksize=1600, dtype='int16', channels=1) as stream:
            for _ in range(int(duration * 10)):
                data, _ = stream.read(1600)
                my_recording += bytes(data)
    except: pass
            
    temp_wav = os.path.join(tempfile.gettempdir(), "cmd.wav")
    with sf.SoundFile(temp_wav, mode='w', samplerate=sample_rate, channels=1, subtype='PCM_16') as f:
        f.write(np.frombuffer(my_recording, dtype=np.int16))
    return temp_wav

def listen_google(wav_path):
    config = load_config()
    if not config.get("USE_GOOGLE_STT", True) or not is_connected():
        return listen_vosk_offline(wav_path)

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio).lower()
    except:
        return ""

def listen_vosk_offline(wav_path):
    if not rec_full: return ""
    try:
        with sf.SoundFile(wav_path) as f:
            data = f.read(dtype='int16')
            rec_full.AcceptWaveform(data.tobytes())
            result = json.loads(rec_full.Result())
            return result.get('text', '').lower()
    except: return ""
