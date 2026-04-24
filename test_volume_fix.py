from pycaw.pycaw import AudioUtilities
def test_endpoint():
    devices = AudioUtilities.GetSpeakers()
    ev = devices.EndpointVolume
    print(f"EndpointVolume type: {type(ev)}")
    print(f"EndpointVolume attributes: {dir(ev)}")
    # Try to set volume
    ev.SetMasterVolumeLevelScalar(0.5, None)
    print("Set volume to 50% successful!")

if __name__ == "__main__":
    test_endpoint()
