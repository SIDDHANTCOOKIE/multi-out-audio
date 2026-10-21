"""Fan one process's audio out to several output devices, each with its own delay."""
import threading

import sounddevice as sd

from .capture import ProcessCapture, RATE, CHANNELS, FRAME_BYTES


def output_devices():
    """[(index, name)] of WASAPI output devices."""
    api = next(i for i, h in enumerate(sd.query_hostapis()) if h["name"] == "Windows WASAPI")
    return [(i, d["name"]) for i, d in enumerate(sd.query_devices())
            if d["hostapi"] == api and d["max_output_channels"] > 0]


class Sink:
    """One output device with a byte queue and adjustable delay."""

    def __init__(self, index, delay_ms=0):
        self.buf = bytearray()
        self.lock = threading.Lock()
        self.delay_ms = 0
        self.stream = sd.RawOutputStream(samplerate=RATE, channels=CHANNELS, dtype="int16", device=index,
                                         callback=self._cb, latency="low",
                                         extra_settings=sd.WasapiSettings(auto_convert=True))
        self.set_delay(delay_ms)
        self.stream.start()

    def _cb(self, outdata, frames, time, status):
        need = frames * FRAME_BYTES
        with self.lock:
            chunk = bytes(self.buf[:need])
            del self.buf[:need]
        outdata[:] = chunk + bytes(need - len(chunk))

    def set_delay(self, ms):
        diff = int((ms - self.delay_ms) * RATE / 1000) * FRAME_BYTES
        with self.lock:
            if diff > 0:
                self.buf[:0] = bytes(diff)
            elif diff < 0:
                del self.buf[:min(-diff, len(self.buf))]
        self.delay_ms = ms

    def push(self, data):
        with self.lock:
            self.buf += data
            cap = int((self.delay_ms + 300) * RATE / 1000) * FRAME_BYTES  # bound drift
            if len(self.buf) > cap:
                del self.buf[:len(self.buf) - cap]

    def close(self):
        self.stream.stop()
        self.stream.close()


class Mirror:
    def __init__(self, pid):
        self.pid = pid
        self.sinks = {}
        self.running = False

    def set_sinks(self, wanted):
        """wanted: {device_index: delay_ms}. Opens/closes/retunes sinks to match."""
        for idx in list(self.sinks):
            if idx not in wanted:
                self.sinks.pop(idx).close()
        for idx, ms in wanted.items():
            if idx in self.sinks:
                self.sinks[idx].set_delay(ms)
            else:
                self.sinks[idx] = Sink(idx, ms)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        cap = ProcessCapture(self.pid)
        try:
            while self.running:
                data = cap.read()
                if data:
                    for s in list(self.sinks.values()):
                        s.push(data)
        finally:
            cap.close()

    def stop(self):
        self.running = False
        self.thread.join(2)
        for s in self.sinks.values():
            s.close()
        self.sinks.clear()
