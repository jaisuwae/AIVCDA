import time
import threading
import os
import shared_state
from config import load_config, save_config
from audio_utils import speak, wait_for_wake_word, record_command, listen_google, is_connected
import system_control as sys_ctrl
import ai_assistant as ai
import media_control as media

def handle_command(command):
    """Entry point for all user commands. Handles splitting and state."""
    if not command: return
    
    # 1. Resolve Confirmations
    if shared_state.pending_action:
        return resolve_confirmation(command)

    # 2. Split and Queue Tasks
    tasks = ai.split_tasks(command)
    shared_state.task_queue.extend(tasks)
    return execute_queue()

def execute_queue():
    """Processes the task queue sequentially."""
    while shared_state.task_queue:
        task = shared_state.task_queue.pop(0)
        print(f"Executing: {task}")
        
        # Determine if we use AI or Local NLU
        intent = ai.parse_intent(task) 
        if not intent and is_connected():
            intent = ai.ask_ai_intent(task)
            
        if intent:
            if run_intent(intent): 
                if shared_state.pending_action: return # Pause for confirmation
                continue
        
        # Conversational fallback
        if is_connected():
            speak(ai.chat_response(task))
        else:
            speak("I'm sorry, I couldn't process that offline.")
    return True

def run_intent(intent):
    """Maps parsed intents to system actions."""
    action = intent.get("action")
    target = intent.get("target", intent.get("query", ""))
    
    if action == "open":
        speak(f"Opening {target}")
        sys_ctrl.open_app(target)
    elif action == "play":
        speak(f"Playing {target}")
        sys_ctrl.web_query(target, "youtube")
    elif action == "calculate":
        res = sys_ctrl.calculate(intent.get("expr", target))
        speak(f"The result is {res}" if res else "I couldn't calculate that.")
    elif action == "volume":
        media.set_volume(intent.get("level", 50))
    elif action == "mute":
        media.toggle_mute()
    elif action in ["time", "date", "stats"]:
        speak(sys_ctrl.query_system(action))
    elif action == "screenshot":
        speak("Screenshot saved.")
        sys_ctrl.query_system("screenshot")
    return True

def resolve_confirmation(command):
    """Handles follow-up logic (Yes/No)."""
    # Simplified for rebuild
    shared_state.pending_action = None
    speak("Confirmed. Proceeding.")
    return execute_queue()

def main():
    print("AVCDA Engine Stabilized.")
    config = load_config()
    while True:
        try:
            if wait_for_wake_word():
                speak("Listening.")
                audio = record_command(duration=5)
                cmd = listen_google(audio)
                if cmd:
                    # Strip assistant name
                    name = config.get("ASSISTANT_NAME", "Silvia").lower()
                    cmd = cmd.lower().replace(name, "").strip()
                    handle_command(cmd)
        except Exception as e:
            print(f"Main Loop Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
