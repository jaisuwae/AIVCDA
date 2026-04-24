import time
import threading
import os
import shared_state
from config import load_config, save_config
from audio_utils import speak, speak_stream, wait_for_wake_word, record_command, listen, is_connected
import system_control as sys_ctrl
import ai_assistant as ai
import media_control as media
from logger import log, approve_pending_log
def handle_command(command):
    """Entry point for all user commands. Handles splitting and state."""
    if not command: return
    log(f"Received command: {command}")
    
    # Check for deactivation phrases (including aliases)
    config = load_config()
    name = config.get("ASSISTANT_NAME", "Silvia").lower()
    aliases = [a.lower() for a in config.get("ASSISTANT_ALIASES", [])]
    all_names = [name] + aliases
    
    # Check each deactivation action against all name variations
    deactivation_actions = ["end", "close", "exit", "stop"]
    cmd_lower = command.lower()
    for action in deactivation_actions:
        for nm in all_names:
            if f"{action} {nm}" in cmd_lower:
                speak("Closing Silvia. Goodbye.")
                log("Deactivation command received.")
                import sys
                sys.exit(0)
    
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
        log(f"Executing task: {task}")
        
        # 1. Local Intent Parsing (Regex)
        intent = ai.parse_intent(task) 
            
        if intent:
            if run_intent(intent): 
                if shared_state.pending_action: return # Pause for confirmation
                continue
        
        # 2. Local AI Fallback (Llama)
        print(f"Consulting Local Llama for: {task}")
        response = ai.ask_local_llama(task, on_chunk=speak_stream)
        log(f"Assistant response: {response}")
        
        # 3. Try to extract and execute commands from LLM response
        extracted_command = sys_ctrl.extract_command_from_response(response)
        if extracted_command:
            success, feedback = sys_ctrl.execute_system_command(extracted_command)
            if success:
                speak(feedback)
                log(f"Executed system command: {extracted_command}")
                continue
        
        # 4. If no command extracted, just speak the response
        speak(response)
    
    return True

def run_intent(intent):
    """Maps parsed intents to system actions."""
    action = intent.get("action")
    target = intent.get("target", intent.get("query", "")).strip()
    
    if action == "search":
        if target:
            speak(f"Searching for {target}")
            sys_ctrl.web_query(target, "google")
        else:
            speak("What would you like me to search for?")
    elif action == "open":
        success = sys_ctrl.open_app(target)
        if success:
            speak(f"Opening {target}")
        else:
            speak(f"I couldn't open {target}. Please add it in the app registry if needed.")
    elif action == "play":
        if target:
            speak(f"Playing {target}")
            sys_ctrl.web_query(target, "youtube")
        else:
            speak("What would you like me to play?")
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
    if shared_state.pending_action == "log_confirmation":
        allowed = command.strip().lower() in ["yes", "y", "sure", "ok", "yeah", "affirmative"]
        if approve_pending_log(allowed):
            speak("Okay, I logged that.")
        else:
            speak("I will not log that.")
        return execute_queue()

    shared_state.pending_action = None
    speak("Confirmed. Proceeding.")
    return execute_queue()

def main():
    print("AIVCDA Local Engine Starting...")
    config = load_config()
    while True:
        try:
            if wait_for_wake_word():
                speak("Listening.")
                wav_path = record_command(duration=5)
                cmd = listen(wav_path)
                
                if cmd:
                    # Strip assistant name and all aliases
                    name = config.get("ASSISTANT_NAME", "Silvia").lower()
                    aliases = [a.lower() for a in config.get("ASSISTANT_ALIASES", [])]
                    cmd_lower = cmd.lower()
                    for nm in [name] + aliases:
                        cmd_lower = cmd_lower.replace(nm, " ").strip()
                    if cmd_lower:
                        handle_command(cmd_lower)
        except Exception as e:
            log(f"Main Loop Error: {e}", level="ERROR")
            print(f"Main Loop Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to close...")
