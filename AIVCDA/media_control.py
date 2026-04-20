import keyboard
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER

def get_volume_interface():
    """Helper to access the system audio endpoint."""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception as e:
        print(f"Audio Interface Error: {e}")
        return None

def set_volume(level):
    """Sets system volume (0-100)."""
    try:
        volume = get_volume_interface()
        if volume:
            # Clamping level
            level = max(0, min(100, level))
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return True
    except Exception as e:
        print(f"Volume Set Error: {e}")
    return False

def toggle_mute():
    """Toggles system mute."""
    try:
        volume = get_volume_interface()
        if volume:
            is_muted = volume.GetMute()
            volume.SetMute(not is_muted, None)
            return True
    except Exception as e:
        print(f"Mute Error: {e}")
    return False

def media_key(action):
    """Sends hardware media keys: next track, previous track, play/pause media."""
    try:
        keyboard.send(action)
        return True
    except Exception as e:
        print(f"Media Key Error: {e}")
        return False
