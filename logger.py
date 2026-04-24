import os
import datetime
import re
from config import load_config
from audio_utils import speak
import shared_state

LOG_FILENAME = "assistant.log"
ALLOWED_LOG_PATTERNS = [
    r"preferred music streaming platform",
    r"music streaming platform",
    r"preferred music",
    r"favorite music",
    r"favourite music",
    r"music platform",
    r"streaming platform",
    r"like",
    r"likes",
    r"favorite",
    r"favourite",
    r"user name",
    r"assistant name",
    r"username",
    r"name",
]


def get_log_path():
    config = load_config()
    log_file = config.get("LOG_FILE", LOG_FILENAME)
    if os.path.isabs(log_file):
        return log_file
    return os.path.join(os.path.dirname(__file__), log_file)


def is_loggable_message(message):
    if not message or not isinstance(message, str):
        return False
    text = message.lower()
    if "name" in text and any(k in text for k in ["user", "assistant", "username"]):
        return True
    if any(re.search(pattern, text) for pattern in ALLOWED_LOG_PATTERNS):
        return True
    return False


def write_log_entry(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} [{level}] {message}\n"
    try:
        path = get_log_path()
        with open(path, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        print(f"Logger write failed: {e}")


def request_log(message, level="INFO"):
    if not is_loggable_message(message):
        return False
    config = load_config()
    if config.get("ASK_BEFORE_LOGGING", True):
        if shared_state.pending_action:
            return False
        shared_state.pending_action = "log_confirmation"
        shared_state.pending_data["pending_log"] = {"message": message, "level": level}
        speak("Should I log that, sir?")
        return False
    write_log_entry(message, level)
    return True


def approve_pending_log(allow):
    pending = shared_state.pending_data.pop("pending_log", None)
    shared_state.pending_action = None
    if not pending:
        return False
    if allow:
        write_log_entry(pending["message"], pending.get("level", "INFO"))
        return True
    return False


def log(message, level="INFO"):
    return request_log(message, level)


def log_exception(exc, context=""):
    write_log_entry(f"{context} {exc}", level="ERROR")
