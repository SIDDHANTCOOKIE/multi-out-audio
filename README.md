# Multi-Out Audio

**Play one app through several audio devices at the same time on Windows**, for example Spotify on your
Bluetooth headphones *and* your speakers, with a delay slider per device to keep them in sync.

Windows normally lets an app use only one output. This tool captures a single app's audio and
re-plays it on every device you tick. No virtual audio driver is needed.

## Use

1. Start playing audio in the app.
2. Run `MultiOutAudio.exe`, choose the app, tick the devices, press **Start**.
3. Bluetooth is slower than wired. If you hear an echo, raise the delay on the *faster* (wired) device until they line up.

The app keeps playing on its normal Windows device too. Either leave that device unticked, or tick it as one of the outputs
and silence the original by routing the app to an unused device in Settings > Sound > Volume mixer.

## Themes

Pick one from the **Theme** menu (it is remembered): **Sakura**, **Midnight Idol**, **Matcha Neko**, **Cyber Bot**, **Ocean Breeze**, and **Custom**.
All mascots are original vector drawings made for this project. For **Custom**, put any PNG or GIF at
%APPDATA%\bt-app-audio-multi\mascot.png (use art you have the rights to, e.g. CC0/public domain).

## How it works

- **Capture:** the Windows process-loopback API (`ActivateAudioInterfaceAsync` on `VAD\Process_Loopback`),
  available on Windows 10 2004+ and Windows 11, grabs only the chosen app's audio.
- **Playback:** one WASAPI output stream per ticked device, each with its own delay buffer.

## Build

Python 3.9+ on Windows.

```powershell
pip install -r requirements.txt
python run_gui.py        # GUI
python -m multiout --list
python -m multiout --app spotify.exe --device Speakers --device "Headphones:120"
.\build.ps1              # dist\MultiOutAudio.exe
```

## Limitations

- Windows 10 2004+ / Windows 11 only.
- Devices run on separate clocks, so very long sessions can drift slightly; the buffer is bounded to correct this.
- Delay is set by ear. There is no automatic Bluetooth latency measurement.
- Captures the app's process tree, so a browser's tabs are all included.

## License

[MIT](LICENSE)
