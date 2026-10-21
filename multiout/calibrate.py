"""Measure each output device's real latency by playing clicks and listening with a microphone.

Bluetooth latency is invisible to Windows, so we measure it acoustically: the click leaves the PC
at a known time and arrives at the mic later. The mic's own delay is the same for every device,
so only differences matter. Hold earbuds/speakers near the mic while this runs.
"""
import threading
import time

import numpy as np
import sounddevice as sd

RATE = 48000
CLICKS = 4
GAP = 0.8  # seconds between clicks
last_debug = []  # (peak, noise) per click window, for troubleshooting


def measure(device_index, input_index=None):
    """Return (latency_seconds_to_mic, confidence 0..1). Raises on device errors."""
    n_total = int((CLICKS * GAP + 1.0) * RATE)
    sig = np.zeros(n_total, dtype=np.int16)
    t = np.arange(int(0.012 * RATE)) / RATE
    burst = (np.sin(2 * np.pi * 2000 * t) * np.hanning(len(t)) * 14000).astype(np.int16)
    starts = [int((0.5 + k * GAP) * RATE) for k in range(CLICKS)]
    for s in starts:
        sig[s:s + len(burst)] = burst
    stereo = np.repeat(sig[:, None], 2, axis=1).tobytes()

    sent_at = [None] * CLICKS
    pos = [0]
    mic = []
    mic_t0 = [None]
    mic_rate = [RATE]
    done = threading.Event()

    def out_cb(outdata, frames, tinfo, status):
        start, end = pos[0], pos[0] + frames
        chunk = stereo[start * 4:end * 4]
        outdata[:] = chunk + bytes(frames * 4 - len(chunk))
        now = time.perf_counter()
        for k, s in enumerate(starts):
            if start <= s < end and sent_at[k] is None:
                sent_at[k] = now + (s - start) / RATE
        pos[0] = end
        if start >= n_total:
            done.set()

    def in_cb(indata, frames, tinfo, status):
        if mic_t0[0] is None:
            mic_t0[0] = time.perf_counter() - frames / mic_rate[0]
        mic.append(indata[:, 0].copy())

    dev_in = sd.query_devices(input_index if input_index is not None else sd.default.device[0])
    mic_rate[0] = int(dev_in["default_samplerate"])
    with sd.InputStream(device=input_index, channels=1, samplerate=mic_rate[0], dtype="float32", callback=in_cb), \
         sd.RawOutputStream(samplerate=RATE, channels=2, dtype="int16", device=device_index, callback=out_cb,
                            extra_settings=sd.WasapiSettings(auto_convert=True)):
        done.wait(CLICKS * GAP + 3)
        time.sleep(0.4)

    if not mic or mic_t0[0] is None:
        return None, 0.0
    x = np.abs(np.concatenate(mic))
    noise = np.median(x) + 1e-6
    results = []
    for k in range(CLICKS):
        if sent_at[k] is None:
            continue
        a = int((sent_at[k] - mic_t0[0]) * mic_rate[0])
        w = x[max(0, a - int(0.05 * mic_rate[0])): a + int(1.2 * mic_rate[0])]
        if len(w) < 100:
            continue
        peak = w.max()
        last_debug.append((float(peak), float(noise)))
        if peak < noise * 12 or peak < 0.01:
            continue
        onset = int(np.argmax(w > peak * 0.4)) + max(0, a - int(0.05 * mic_rate[0]))
        results.append((onset - a) / mic_rate[0])
    if len(results) < 2:
        return None, 0.0
    spread = max(results) - min(results)
    return float(np.median(results)), float(max(0.0, 1 - spread / 0.05))
