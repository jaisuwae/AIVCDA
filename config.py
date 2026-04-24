import os
import json
import psutil
import sys


def get_resource_path(relative_path):
    """Return an absolute path for bundled resources or local files."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def get_writable_path(filename):
    """Return a writable path for config and memory files when bundled."""
    if getattr(sys, "_MEIPASS", False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        return os.path.join(exe_dir, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

CONFIG_RESOURCE_PATH = get_resource_path("config.json")
CONFIG_PATH = get_writable_path("config.json")
MEMORY_RESOURCE_PATH = get_resource_path("memory.json")
MEMORY_PATH = get_writable_path("memory.json")


def load_config():
    path = CONFIG_RESOURCE_PATH if os.path.exists(CONFIG_RESOURCE_PATH) else CONFIG_PATH
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config_data):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)


def load_memory():
    path = MEMORY_RESOURCE_PATH if os.path.exists(MEMORY_RESOURCE_PATH) else MEMORY_PATH
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(memory_data):
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        json.dump(memory_data, f, indent=4)


def apply_resource_limits():
    """Applies CPU priority and affinity based on config to ensure very low resource usage."""
    config = load_config()
    mode = config.get("RESOURCE_MODE", "Low")
    
    p = psutil.Process(os.getpid())
    try:
        # psutil constants for Windows Priority Classes
        BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
        IDLE_PRIORITY_CLASS = 0x00000040
        NORMAL_PRIORITY_CLASS = 0x00000020
        
        if mode == "Low":
            p.nice(BELOW_NORMAL_PRIORITY_CLASS)
            # Limit to 1 CPU core to physically prevent high usage
            cores = p.cpu_affinity()
            if cores and len(cores) > 1:
                p.cpu_affinity([cores[0]]) 
                
        elif mode == "Ultra-Low":
            p.nice(IDLE_PRIORITY_CLASS)
            cores = p.cpu_affinity()
            if cores and len(cores) > 1:
                p.cpu_affinity([cores[0]]) 
        else:
            p.nice(NORMAL_PRIORITY_CLASS)
            p.cpu_affinity(list(range(psutil.cpu_count())))
    except Exception as e:
        print(f"Failed to apply resource limits: {e}")

WAKE_MESSAGE = "What would you like to do today, sir?"
