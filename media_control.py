from pycaw.pycaw import AudioUtilities
import keyboard

def get_volume_interface():
    """Helper to access the system audio endpoint via pycaw."""
    try:
        speakers = AudioUtilities.GetSpeakers()
        return speakers.EndpointVolume
    except Exception as e:
        print(f"Audio Interface Error: {e}")
        return None

def set_volume(level):
    """Sets system volume (0-100)."""
    try:
        volume = get_volume_interface()
        if volume:
            level = max(0, min(100, level))
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            print(f"Volume set to {level}%")
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
            print(f"Mute toggled: {'Muted' if not is_muted else 'Unmuted'}")
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
