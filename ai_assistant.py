import json
import re
import requests
import psutil
import os
import shutil
from urllib.parse import urlparse
from config import load_config
from logger import log

MODEL_ALIAS_MAP = {
    "eco": "LLAMA_MODEL_ECO",
    "standard": "LLAMA_MODEL_STANDARD",
    "phi": "LLAMA_MODEL_PHI",
}

DEFAULT_MODELS = {
    "eco": "qwen2.5:1.5b",
    "standard": "llama3.2:3b",
    "phi": "phi3.5",
}


def split_tasks(user_input):
    """Splits a multi-command string into atomic tasks using Regex."""
    text = user_input.strip()
    if not text: return []
    
    # Local Regex Splitting (Reliable and fast)
    delimiters = r'\band\b|\bthen\b|,'
    parts = [p.strip() for p in re.split(delimiters, text, flags=re.IGNORECASE) if p.strip()]
    return parts if len(parts) > 1 else [text]

def parse_intent(text):
    """Local Regex NLU for core offline functionality."""
    raw = text.lower().strip()
    
    # Simple mapping for core functions
    patterns = {
        "time": ["time", "clock"],
        "date": ["date", "today", "day"],
        "stats": ["stats", "battery", "cpu", "usage"],
        "screenshot": ["screenshot", "capture", "shot"],
        "mute": ["mute", "silence", "stop sound"],
        "volume": ["volume", "sound level"]
    }
    
    for intent, keys in patterns.items():
        if any(k in raw for k in keys):
            if intent == "volume":
                nums = re.findall(r'\d+', raw)
                return {"action": "volume", "level": int(nums[0]) if nums else 50}
            return {"action": intent}

    # Search intents: "search X", "find X", "lookup X", "google X", or "X on google"
    if " on google" in raw:
        query = raw.replace(" on google", "").strip()
        # Strip search keywords if present
        for keyword in ["search", "find", "lookup", "google"]:
            if query.startswith(keyword + " "):
                query = query[len(keyword):].strip()
                break
        if query:
            return {"action": "search", "query": query}
    
    search_match = re.search(r'\b(?:search|find|lookup|google)\b\s+(.*?)$', raw)
    if search_match:
        query = search_match.group(1).strip()
        if query:
            return {"action": "search", "query": query}

    open_match = re.search(r'\b(?:open|launch|start)\b\s+(.*)', raw)
    if open_match:
        t = open_match.group(1).strip()
        return {"action": "open", "target": t}

    play_match = re.search(r'\b(?:play|stream|watch)\b\s+(.*)', raw)
    if play_match:
        q = play_match.group(1).strip()
        return {"action": "play", "query": q}

    return None


def is_low_ram(threshold=0.25):
    try:
        mem = psutil.virtual_memory()
        return mem.available / mem.total < threshold
    except Exception:
        return False


def choose_llm_model(prompt, config):
    """Choose a model based on prompt cues, current defaults, and low RAM."""
    raw = prompt.lower()
    eco_model = config.get("LLAMA_MODEL_ECO", DEFAULT_MODELS["eco"])
    standard_model = config.get("LLAMA_MODEL_STANDARD", DEFAULT_MODELS["standard"])
    phi_model = config.get("LLAMA_MODEL_PHI", DEFAULT_MODELS["phi"])
    custom_model = config.get("LLAMA_CUSTOM_MODEL", "").strip()
    default_brain = config.get("LLAMA_DEFAULT_BRAIN", "Eco").lower()

    if "eco mode" in raw or "use eco" in raw or "qwen" in raw:
        return eco_model, "Eco"
    if "phi" in raw or "3.5" in raw:
        return phi_model, "Phi 3.5"
    if "standard mode" in raw or "use standard" in raw or ("llama" in raw and "qwen" not in raw):
        return standard_model, "Standard"
    if default_brain.startswith("eco") or is_low_ram():
        return eco_model, "Eco"
    if default_brain.startswith("phi"):
        return phi_model, "Phi 3.5"
    if default_brain.startswith("custom") and custom_model:
        return custom_model, "Custom"
    return standard_model, "Standard"


def get_personality_instruction(config):
    """Generate system prompt with personality and available commands."""
    personality = config.get("ASSISTANT_PERSONALITY", "Answer briefly, politely, and clearly.")
    if not isinstance(personality, str):
        personality = str(personality)
    personality = personality.strip()
    
    # Add command awareness to the system prompt
    command_instruction = """
You have the ability to execute the following system commands:

DEVICE CONTROL:
- Turn Bluetooth on/off: "I'll turn on Bluetooth" / "I'll disable Bluetooth"
- Turn WiFi on/off: "I'll enable WiFi" / "I'll turn off WiFi"
- Adjust brightness: "I'll increase brightness" / "I'll dim the screen"
- Mute/Unmute audio: "I'll mute your audio" / "I'll unmute"
- Sleep/Lock screen: "I'll put the system to sleep"
- Restart system: "I'll restart the computer in 30 seconds"
- Shutdown: "I'll shut down in 30 seconds"

APPLICATIONS:
- Open Notepad: "I'll open Notepad"
- Open Calculator: "I'll open Calculator" 
- Open Task Manager: "I'll open Task Manager"

INFORMATION:
- When asked time/date/stats, provide the information
- When asked to search, provide the search results

IMPORTANT INSTRUCTIONS:
1. When a user asks you to do something (turn off, enable, open, etc.), respond with a CLEAR ACTION STATEMENT that includes what you'll do.
2. Format your responses so the action is obvious. Examples:
   - "I'll turn off Bluetooth" (not "Bluetooth will be turned off")
   - "I'll open Notepad for you" (not "Notepad can be opened")
   - "I'll dim the screen" (not "The screen brightness is adjustable")
3. Always use "I'll" or "I will" followed by the action
4. Be concise and direct about what action you're taking
5. After confirming the action, you can add helpful context if needed

Remember: Your responses trigger automatic actions. Be clear about what you're doing!
"""
    
    return f"{personality}\n{command_instruction}"


def find_ollama_executable(directory=None):
    """Try to locate the Ollama executable on disk."""
    if directory:
        candidate = os.path.join(directory, "ollama.exe" if os.name == "nt" else "ollama")
        if os.path.isfile(candidate):
            return candidate

    which_path = shutil.which("ollama")
    if which_path and os.path.isfile(which_path):
        return which_path

    candidates = []
    if os.name == "nt":
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("PROGRAMFILES", "")
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "")
        candidates.extend([
            os.path.join(local_appdata, "Programs", "Ollama", "ollama.exe"),
            os.path.join(program_files, "Ollama", "ollama.exe"),
            os.path.join(program_files_x86, "Ollama", "ollama.exe"),
        ])
    else:
        candidates.extend([
            "/usr/local/bin/ollama",
            "/usr/bin/ollama",
            "/bin/ollama",
        ])

    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def is_ollama_running(url=None, timeout=2):
    """Checks whether the local Ollama service is accessible."""
    config = load_config()
    url = url or config.get("LLAMA_URL", "http://localhost:11434/api/generate")
    if not url:
        return False
    try:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        requests.get(base_url, timeout=timeout)
        return True
    except Exception:
        return False


def ask_local_llama(prompt, on_chunk=None):
    """
    Communicates with a local Llama instance (Ollama/LM Studio style).
    Targets the 'LLAMA_URL' defined in config.
    """
    config = load_config()
    url = config.get("LLAMA_URL", "http://localhost:11434/api/generate") # Default Ollama port
    timeout = int(config.get("LLAMA_TIMEOUT", 120))
    model, model_mode = choose_llm_model(prompt, config)
    
    if not url:
        return "Local Llama endpoint not configured."
    if not isinstance(model, str):
        model = str(model)

    parsed = urlparse(url)
    endpoint = parsed.path.lower()
    use_chat_payload = endpoint.endswith("/chat") or "/chat" in endpoint

    def _normalize_line(line):
        if isinstance(line, bytes):
            line = line.decode("utf-8", errors="replace")
        if not isinstance(line, str):
            return None
        line = line.strip()
        if not line or line == "[DONE]":
            return None
        if line.startswith("data:"):
            line = line[5:].strip()
        return line or None

    def _extract_text_from_stream_line(line):
        line = _normalize_line(line)
        if not line:
            return None
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return None

        if isinstance(payload, dict):
            if isinstance(payload.get("response"), str):
                return payload["response"]
            if isinstance(payload.get("content"), str):
                return payload["content"]
            if isinstance(payload.get("text"), str):
                return payload["text"]

            choices = payload.get("choices")
            if isinstance(choices, list) and choices:
                choice = choices[0]
                if isinstance(choice, dict):
                    delta = choice.get("delta")
                    if isinstance(delta, dict) and isinstance(delta.get("content"), str):
                        return delta.get("content")
                    if isinstance(choice.get("text"), str):
                        return choice.get("text")
        return None

    def _stream_response(response):
        full_response = ""
        for line in response.iter_lines(decode_unicode=False):
            chunk = _extract_text_from_stream_line(line)
            if not chunk:
                continue
            full_response += chunk
            if on_chunk:
                try:
                    on_chunk(chunk)
                except Exception as e:
                    print(f"Chunk callback error: {e}")
        return full_response

    def _send_request(target_url, payload):
        return requests.post(target_url, json=payload, stream=True, timeout=timeout)

    payload = {"model": model, "stream": True}
    if use_chat_payload:
        payload["messages"] = [{"role": "user", "content": prompt}]
    else:
        payload["prompt"] = prompt

    print(f"Using LLM model: {model} ({model_mode})")

    personality = get_personality_instruction(config)
    if use_chat_payload:
        payload["messages"] = [
            {"role": "system", "content": personality},
            {"role": "user", "content": prompt}
        ]
    else:
        payload["prompt"] = f"{personality}\n\n{prompt}"

    log(f"LLM prompt model={model}; mode={model_mode}; personality={personality}")
    try:
        response = _send_request(url, payload)
        if response.status_code == 200:
            full_response = _stream_response(response)
            if full_response:
                log(f"LLM response: {full_response}")
                return full_response
            return "No response from local LLM."

        if not use_chat_payload:
            fallback_url = f"{parsed.scheme}://{parsed.netloc}/api/chat"
            fallback_payload = {"model": model, "stream": True, "messages": [{"role": "user", "content": prompt}]}
            response = _send_request(fallback_url, fallback_payload)
            if response.status_code == 200:
                full_response = _stream_response(response)
                if full_response:
                    return full_response
                return "No response from local LLM."

        print(f"Local LLM error: HTTP {response.status_code}")
        return "My local brain isn't responding right now."
    except requests.ConnectionError:
        print("Local LLM not running.")
        return "My local AI brain is offline. Please start Ollama or LM Studio."
    except requests.Timeout:
        print(f"Local LLM timed out after {timeout} seconds.")
        return "My local AI brain took too long to respond."
    except Exception as e:
        print(f"Local LLM error: {e}")
        return "I couldn't reach my local AI brain."
