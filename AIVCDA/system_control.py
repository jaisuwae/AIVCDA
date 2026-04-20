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
    
    # 1. Custom Command Lookup
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
        path = os.path.join(os.path.expanduser("~"), "Desktop", f"AVCDA_{now.strftime('%H%M%S')}.png")
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
