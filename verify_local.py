"""AIVCDA v3.0 Verification Script - Tests all non-hardware modules."""
import sys
print(f"Python: {sys.version}")
print("=" * 50)

# 1. Test all imports
errors = []
modules = {
    "numpy": "import numpy",
    "sounddevice": "import sounddevice",
    "soundfile": "import soundfile",
    "SpeechRecognition": "import speech_recognition",
    "vosk": "import vosk",
    "edge_tts": "import edge_tts",
    "pyttsx3": "import pyttsx3",
    "customtkinter": "import customtkinter",
    "psutil": "import psutil",
    "WMI": "import wmi",
    "requests": "import requests",
    "Pillow": "from PIL import Image",
    "comtypes": "import comtypes",
    "pycaw": "from pycaw.pycaw import AudioUtilities",
    "keyboard": "import keyboard",
}

print("[1/5] Checking module imports...")
for name, stmt in modules.items():
    try:
        exec(stmt)
        print(f"  [OK] {name}")
    except Exception as e:
        errors.append(f"{name}: {e}")
        print(f"  [FAIL] {name} -- {e}")

# 2. Test config
print("\n[2/5] Testing config load/save...")
try:
    from config import load_config, save_config
    cfg = load_config()
    assert "ASSISTANT_NAME" in cfg, "Missing ASSISTANT_NAME"
    assert "LLAMA_URL" in cfg, "Missing LLAMA_URL"
    assert "USE_GOOGLE_STT" in cfg, "Missing USE_GOOGLE_STT"
    assert "USE_CLOUD_TTS" in cfg, "Missing USE_CLOUD_TTS"
    print(f"  [OK] Config loaded -- {len(cfg)} keys")
    print(f"    Assistant: {cfg['ASSISTANT_NAME']}")
    print(f"    Llama URL: {cfg['LLAMA_URL']}")
    print(f"    Google STT: {cfg['USE_GOOGLE_STT']}")
    print(f"    Edge TTS: {cfg['USE_CLOUD_TTS']}")
except Exception as e:
    errors.append(f"config: {e}")
    print(f"  [FAIL] Config error -- {e}")

# 3. Test AI intent parsing
print("\n[3/5] Testing local intent parsing...")
try:
    import ai_assistant as ai
    test_cases = [
        ("open notepad", "open"),
        ("what time is it", "time"),
        ("set volume to 80", "volume"),
        ("take a screenshot", "screenshot"),
        ("play back in black", "play"),
        ("tell me a joke", None),
    ]
    for cmd, expected in test_cases:
        result = ai.parse_intent(cmd)
        action = result.get("action") if result else None
        status = "[OK]" if action == expected else "[FAIL]"
        print(f"  {status} '{cmd}' -> {action} (expected: {expected})")
        if action != expected:
            errors.append(f"parse_intent('{cmd}'): got {action}, expected {expected}")
except Exception as e:
    errors.append(f"ai_assistant: {e}")
    print(f"  [FAIL] AI assistant error -- {e}")

# 4. Test task splitting
print("\n[4/5] Testing task splitting...")
try:
    tasks = ai.split_tasks("open notepad and play music then take a screenshot")
    print(f"  [OK] Split into {len(tasks)} tasks: {tasks}")
    assert len(tasks) == 3, f"Expected 3 tasks, got {len(tasks)}"
except Exception as e:
    errors.append(f"split_tasks: {e}")
    print(f"  [FAIL] Task splitting error -- {e}")

# 5. Test shared_state
print("\n[5/5] Testing shared state...")
try:
    import shared_state
    assert hasattr(shared_state, "task_queue"), "Missing task_queue"
    assert hasattr(shared_state, "pending_action"), "Missing pending_action"
    assert hasattr(shared_state, "is_running"), "Missing is_running"
    assert not hasattr(shared_state, "gemini_enabled"), "Stale gemini_enabled still present!"
    print("  [OK] Shared state clean -- no stale Gemini references")
except Exception as e:
    errors.append(f"shared_state: {e}")
    print(f"  [FAIL] Shared state error -- {e}")

# Summary
print("\n" + "=" * 50)
if errors:
    print(f"RESULT: {len(errors)} issue(s) found:")
    for e in errors:
        print(f"  * {e}")
else:
    print("RESULT: ALL CHECKS PASSED")
print("=" * 50)
