import os
import subprocess
import webbrowser
import psutil
import urllib.request
import urllib.parse
import re
import ast
import operator
from datetime import datetime
from PIL import ImageGrab
from config import load_config

def is_process_running(exe_name):
    """Checks if a process is already active."""
    exe_name = exe_name.lower()
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and exe_name in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

def open_app(app_name):
    """Unified application and deep-search launcher."""
    config = load_config()
    app_name = app_name.lower().strip()
    
    # 1. Registered custom apps from GUI
    custom_apps = config.get("CUSTOM_APPS", {})
    for key, path in custom_apps.items():
        if key in app_name:
            if "://" in path:
                webbrowser.open(path)
            else:
                os.startfile(path)
            return True

    # 2. Custom Command Lookup
    custom = config.get("CUSTOM_COMMANDS", {})
    if app_name in custom:
        path = custom[app_name]
        if "://" in path: webbrowser.open(path)
        else: os.startfile(path)
        return True

    # 2. Hardcoded Common Apps
    app_map = {
        "whatsapp": "whatsapp://",
        "chrome": "start chrome",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "spotify": "spotify",
        "code": "code"
    }
    
    for key, cmd in app_map.items():
        if key in app_name:
            if key == "chrome": subprocess.Popen(cmd, shell=True)
            elif "://" in cmd or key == "spotify": os.startfile(cmd)
            else: subprocess.Popen(cmd, shell=True)
            return True

    # 3. Global Windows Search Fallback
    search_paths = [
        os.path.join(os.environ.get("ProgramData", ""), "Microsoft/Windows/Start Menu/Programs"),
        os.path.join(os.environ.get("AppData", ""), "Microsoft/Windows/Start Menu/Programs")
    ]
    
    for path in search_paths:
        if os.path.exists(path):
            for root, _, files in os.walk(path):
                for f in files:
                    if app_name in f.lower():
                        try:
                            os.startfile(os.path.join(root, f))
                            return True
                        except: continue
    return False

def calculate(expression):
    """Safely evaluates mathematical expressions."""
    ops = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Pow: operator.pow, ast.BitXor: operator.xor,
        ast.USub: operator.neg
    }
    
    def _eval(node):
        if isinstance(node, ast.Constant): return node.value
        elif isinstance(node, ast.BinOp): return ops[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp): return ops[type(node.op)](_eval(node.operand))
        raise TypeError(node)

    try:
        # Pre-process: strip words and convert operators
        expr = expression.lower()
        for word in ["what is", "calculate", "how much is"]: expr = expr.replace(word, "")
        expr = expr.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/").replace("^", "**")
        expr = re.sub(r'[^0-9\+\-\*\/\.\(\)\s\^]', '', expr).strip()
        
        if not expr: return None
        return str(_eval(ast.parse(expr, mode='eval').body))
    except: return None

def query_system(action):
    """Handles time, stats, and screenshot actions."""
    now = datetime.now()
    if action == "time": return now.strftime("%I:%M %p")
    if action == "date": return now.strftime("%A, %B %d")
    if action == "stats":
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        return f"CPU is at {cpu}%, RAM is at {ram}%."
    if action == "screenshot":
        path = os.path.join(os.path.expanduser("~"), "Desktop", f"AIVCDA_{now.strftime('%H%M%S')}.png")
        ImageGrab.grab().save(path)
        return path
    return None

def web_query(query, site="google"):
    """Generic web search and video player."""
    encoded = urllib.parse.quote(query)
    if site == "youtube":
        try:
            html = urllib.request.urlopen(f"https://www.youtube.com/results?search_query={encoded}").read().decode()
            video_ids = re.findall(r"watch\?v=(\S{11})", html)
            if video_ids:
                webbrowser.open(f"https://www.youtube.com/watch?v={video_ids[0]}&autoplay=1")
                return True
        except: pass
        webbrowser.open(f"https://www.youtube.com/results?search_query={encoded}")
    else:
        webbrowser.open(f"https://www.google.com/search?q={encoded}")
    return True

def execute_system_command(command):
    """Execute system control commands extracted from LLM responses."""
    command = command.lower().strip()
    
    # Bluetooth commands
    if any(k in command for k in ["bluetooth", "turn off bluetooth", "disable bluetooth"]):
        if "turn off" in command or "disable" in command or "off" in command:
            subprocess.run("powershell -Command \"(Get-Service bluetooth) | Stop-Service -Force -NoWait\"", shell=True)
            return True, "Turning off Bluetooth."
        elif "turn on" in command or "enable" in command or "on" in command:
            subprocess.run("powershell -Command \"(Get-Service bluetooth) | Start-Service -NoWait\"", shell=True)
            return True, "Turning on Bluetooth."
    
    # WiFi commands
    if any(k in command for k in ["wifi", "wi-fi", "turn off wifi", "disable wifi", "turn on wifi"]):
        if "turn off" in command or "disable" in command or "off" in command:
            subprocess.run("powershell -Command \"Disable-NetAdapter -Name WiFi -Confirm:$false\"", shell=True)
            return True, "Turning off WiFi."
        elif "turn on" in command or "enable" in command or "on" in command:
            subprocess.run("powershell -Command \"Enable-NetAdapter -Name WiFi -Confirm:$false\"", shell=True)
            return True, "Turning on WiFi."
    
    # Sleep/Lock screen
    if any(k in command for k in ["sleep", "lock", "suspend"]):
        subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
        return True, "Putting the system to sleep."
    
    # Restart/Shutdown
    if "restart" in command or "reboot" in command:
        subprocess.run("shutdown /r /t 30 /c 'Restarting at Silvia request'", shell=True)
        return True, "Restarting the system in 30 seconds."
    
    if "shutdown" in command or "turn off" in command and "computer" in command:
        subprocess.run("shutdown /s /t 30 /c 'Shutting down at Silvia request'", shell=True)
        return True, "Shutting down the system in 30 seconds."
    
    # Screen brightness (using Windows settings)
    if "brightness" in command or "dim" in command:
        if "increase" in command or "up" in command or "brighter" in command:
            subprocess.run("powershell -Command \"(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,100)\"", shell=True)
            return True, "Increasing screen brightness."
        elif "decrease" in command or "down" in command or "dimmer" in command:
            subprocess.run("powershell -Command \"(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,30)\"", shell=True)
            return True, "Decreasing screen brightness."
    
    # Volume control
    if "volume" in command:
        if "mute" in command or "silent" in command:
            subprocess.run("powershell -Command \"[Windows.Media.SystemMediaTransportControls]::CreateForShellContext().Mute()\"", shell=True)
            return True, "Muting audio."
        elif "unmute" in command or "unmuted" in command:
            subprocess.run("powershell -Command \"[Windows.Media.SystemMediaTransportControls]::CreateForShellContext().Unmute()\"", shell=True)
            return True, "Unmuting audio."
    
    # Applications
    if "notepad" in command or "open notepad" in command:
        subprocess.Popen("notepad.exe")
        return True, "Opening Notepad."
    
    if "calculator" in command or "open calculator" in command or "calc" in command:
        subprocess.Popen("calc.exe")
        return True, "Opening Calculator."
    
    if "task manager" in command or "open task manager" in command:
        subprocess.Popen("taskmgr.exe")
        return True, "Opening Task Manager."
    
    return False, None

def extract_command_from_response(response):
    """Extract actionable commands from LLM response."""
    response_lower = response.lower()
    
    # Common patterns the LLM might use to indicate an action
    command_patterns = [
        r"(?:turn off|disable|shut down|disable)\s+(\w+)",
        r"(?:turn on|enable|start)\s+(\w+)",
        r"(?:open|launch|start)\s+(\w+)",
        r"(?:set|change)\s+(\w+)\s+(?:to|at)\s+(\w+|\d+)",
    ]
    
    # Check if response contains action keywords
    action_keywords = ["bluetooth", "wifi", "wi-fi", "sleep", "lock", "brightness", "volume", 
                      "mute", "unmute", "restart", "reboot", "shutdown", "notepad", "calculator", 
                      "task manager"]
    
    for keyword in action_keywords:
        if keyword in response_lower:
            return response  # Return the full response for command execution
    
    return None
