from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER

def test_volume():
    try:
        devices = AudioUtilities.GetSpeakers()
        print(f"Device type: {type(devices)}")
        # If it's the pycaw wrapper, it might have an '.id' or similar, 
        # but usually we want the IMMDevice.
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        print("Success with Activate!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_volume()
