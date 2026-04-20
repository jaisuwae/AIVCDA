import os
import json
import psutil

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config_data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config_data, f, indent=4)

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
