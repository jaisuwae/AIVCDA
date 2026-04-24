# Project AIVCDA Metadata

VERSION = "3.0.0"
AUTHOR = "Jaisuwae"
LICENSE = "MIT"
GITHUB = "https://github.com/jaisuwae/AIVCDA"

LIBRARIES = [
    {"name": "Ollama / LM Studio", "desc": "Local LLM runtime for private inference and model hosting."},
    {"name": "Vosk", "desc": "Offline speech recognition for wake words and fallback command capture."},
    {"name": "CustomTkinter", "desc": "Modern dark GUI framework for the app interface."},
    {"name": "edge-tts", "desc": "High-quality cloud text-to-speech via Microsoft Edge voices."},
    {"name": "pyttsx3", "desc": "Local offline speech engine used when cloud TTS is unavailable."},
    {"name": "SpeechRecognition", "desc": "Speech-to-text integration for Google and local audio input."},
    {"name": "sounddevice", "desc": "Microphone capture and playback for voice command handling."},
    {"name": "requests", "desc": "Local HTTP communication with Ollama and remote resources."},
    {"name": "psutil", "desc": "System monitoring to support low-RAM eco mode and resource-aware behavior."}
]

CHANGELOG = [
    {"v": "3.0.0", "date": "2026-04-23", "note": "Local AI rebuild: Removed Gemini/OpenAI, added Llama local LLM, refined all modules."},
    {"v": "2.1.0", "date": "2026-04-20", "note": "Added Neural Hub, Documentation Tab, Multi-AI Support, and recursive loop fixes."},
    {"v": "2.0.0", "date": "2026-04-19", "note": "Project AIVCDA Launch. Carbon GUI, Learning Memory logic, and Stability overhaul."}
]

TERMS = """Project AIVCDA is provided as-is and under the MIT license.
By using this software, you agree that the author is not liable for any damage, loss, or harm to you, your files, resources, computer, or devices.
This product is used at your own risk; all responsibility for usage rests with you.
Privacy: Voice commands are processed locally when possible. Google STT and Edge-TTS require internet when enabled."""
