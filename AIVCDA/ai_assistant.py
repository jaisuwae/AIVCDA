import google.generativeai as genai
import json
import re
import difflib
import requests
from config import load_config

def get_model(name='gemini-1.5-flash'):
    """Configures and returns the Gemini model with a fallback mechanism."""
    config = load_config()
    api_key = config.get("GEMINI_API_KEY")
    if not api_key: return None
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(name)
    except: return None

def split_tasks(user_input):
    """Splits a multi-command string into atomic tasks using AI or Regex."""
    text = user_input.strip()
    if not text: return []
    
    # 1. AI Splitting (Recommended for complexity)
    model = get_model()
    if model and len(text.split()) > 3:
        try:
            prompt = f"Split this into a clean JSON list of individual tasks: '{text}'. JSON only:"
            resp = model.generate_content(prompt)
            return json.loads(resp.text.strip().replace("```json", "").replace("```", ""))
        except: pass
        
    # 2. Local Regex Fallback
    delimiters = r'\band\b|\bthen\b|,'
    parts = [p.strip() for p in re.split(delimiters, text, flags=re.IGNORECASE) if p.strip()]
    return parts if len(parts) > 1 else [text]

def parse_intent(text):
    """Local Regex NLU for core offline functionality."""
    raw = text.lower().strip()
    
    # Simple mapping
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

    if any(x in raw for x in ["open", "launch", "start"]):
        t = re.sub(r'open|launch|start', '', raw).strip()
        return {"action": "open", "target": t}
        
    if any(x in raw for x in ["play", "stream", "watch"]):
        q = re.sub(r'play|stream|watch', '', raw).strip()
        return {"action": "play", "query": q}

    return None

def ask_ai_intent(text):
    """Cloud-based intent parsing using Gemini."""
    model = get_model()
    if not model: return parse_intent(text)
    try:
        instr = "JSON only. Actions: open, play, search, calculate, volume, mute, time, date, stats, screenshot. Input: "
        resp = model.generate_content(instr + text)
        return json.loads(resp.text.strip().replace("```json", "").replace("```", ""))
    except: return parse_intent(text)

def chat_response(prompt):
    """Generic conversational response."""
    model = get_model('gemini-pro')
    if not model: return "I'm offline but ready for system commands."
    try:
        resp = model.generate_content(prompt)
        return resp.text.replace("*", "")
    except: return "I encountered a neural link error."
