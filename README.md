# AIVCDA (Sidewing)

AIVCDA is a local AI assistant for Windows that uses Ollama/LM Studio and offline speech tools to process commands, execute tasks, and speak responses. It is built for privacy-first local use with a modern GUI, configurable brain selection, personalized assistant behavior, and automatic fallbacks.

## Features

- Local LLM support via Ollama/LM Studio
- Multiple model modes: Eco (`qwen2.5:1.5b`), Standard (`llama3.2:3b`), and Phi `3.5`
- Low-RAM eco mode selection and model routing
- Wake-word detection with Vosk
- Hybrid speech recognition using Google STT + local fallback
- Cloud TTS with Edge plus offline fallback using pyttsx3
- GUI brain selection, Ollama autodiscovery, and activation options
- Personal assistant personality customization
- Configurable logging with permission-based prompts
- MIT open-source license

## Requirements

- Windows 10 / 11
- Ollama or LM Studio installed
- Minimum Ryzen 3 or equivalent processor or higher for eco mode
- Minimum 8GB RAM for eco mode 
- Integrated Graphics or Dedicated GPU with Minimum 4GB VRAM for standard mode and eco mode
- Python 3.11+ (recommended)
- Local Ollama or LM Studio installation
- Internet for Google STT and Edge cloud TTS (optional)

## Python dependencies

The project uses these packages:

- `numpy`
- `ollama`
- `sounddevice`
- `soundfile`
- `SpeechRecognition`
- `vosk`
- `edge-tts`
- `pyttsx3`
- `customtkinter`
- `psutil`
- `WMI`
- `pywin32`
- `requests`
- `Pillow`
- `comtypes`
- `pycaw`
- `keyboard`

See `requirements.txt` for the exact package list.

## Installation

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure `config.json` if needed.

## Configuration

Important configuration options in `config.json`:

- `LLAMA_URL`: Local Ollama endpoint, typically `http://localhost:11434/api/generate`
- `LLAMA_PATH`: Optional path to `ollama.exe`
- `LLAMA_DEFAULT_BRAIN`: Default model mode choice
- `LLAMA_CUSTOM_MODEL`: Optional custom model name
- `ASSISTANT_PERSONALITY`: Custom personality prompt for Silvia
- `LOG_FILE`: Log file path
- `ASK_BEFORE_LOGGING`: Enable permission before writing personal logs

## Usage

- Run the GUI: `python gui.py`
- Use the Neural Hub tab to select your default brain and set Ollama options
- Start the engine from the sidebar
- Speak or type commands as Silvia listens
- If Ollama is not reachable, the app will ask whether to continue anyway
- When internet is unavailable, the assistant reports it and uses offline fallback

## Why use AIVCDA?

AIVCDA is designed for local-first voice automation with privacy in mind. It lets you:

- run commands on your PC with voice
- use offline speech recognition fallback
- choose between eco and standard local models
- customize assistant tone and personality
- keep configuration and logs under your control

## Troubleshooting

- If Ollama cannot be found, use the Neural Hub tab to auto-locate or set the install directory.
- If the assistant says `Internet not detected`, verify your network connection before using cloud-based TTS or STT.
- If local audio fails, ensure your microphone and speakers are working.
- If `LLAMA_URL` is wrong, use the GUI to update the endpoint.

## License

This project is licensed under the MIT License.

## Disclaimer

This software is provided as-is. By using AIVCDA, you agree that the author is not liable for any damage, loss, or harm to you, your files, resources, computer, or devices. Use this product at your own risk.
Data may be shared with Microsoft Edge-tts and Google Speech to Text (STT).

## Credits
Thanks for using,
Jaisuwae.


