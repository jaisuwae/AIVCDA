from pycaw.pycaw import AudioUtilities
def test_dir():
    devices = AudioUtilities.GetSpeakers()
    print(f"Attributes: {dir(devices)}")

if __name__ == "__main__":
    test_dir()
