"""Capture one process's audio with the Windows process-loopback API (Win10 2004+ / Win11)."""
import ctypes
import threading
from ctypes import POINTER, byref, c_void_p, c_uint32, c_uint64, c_ubyte, c_wchar_p, HRESULT, WINFUNCTYPE
from ctypes import wintypes

RATE, CHANNELS, BITS = 48000, 2, 16
FRAME_BYTES = CHANNELS * BITS // 8

ole32 = ctypes.WinDLL("ole32")
mmdev = ctypes.WinDLL("Mmdevapi")
kernel32 = ctypes.WinDLL("kernel32")
kernel32.CreateEventW.restype = c_void_p
kernel32.WaitForSingleObject.argtypes = [c_void_p, wintypes.DWORD]


class GUID(ctypes.Structure):
    _fields_ = [("a", ctypes.c_uint32), ("b", ctypes.c_uint16), ("c", ctypes.c_uint16), ("d", c_ubyte * 8)]

    def __init__(self, s):
        import uuid
        u = uuid.UUID(s)
        super().__init__(u.time_low, u.time_mid, u.time_hi_version,
                         (c_ubyte * 8)(*([u.clock_seq_hi_variant, u.clock_seq_low] + list(u.node.to_bytes(6, "big")))))


IID_IAudioClient = GUID("1CB9AD4C-DBFA-4c32-B178-C2F568A703B2")
IID_IAudioCaptureClient = GUID("c8adbd64-e71e-48a0-a4de-185c395cd317")


class WAVEFORMATEX(ctypes.Structure):
    _fields_ = [("tag", ctypes.c_uint16), ("ch", ctypes.c_uint16), ("rate", ctypes.c_uint32),
                ("avg", ctypes.c_uint32), ("align", ctypes.c_uint16), ("bits", ctypes.c_uint16),
                ("cb", ctypes.c_uint16)]


class ActivationParams(ctypes.Structure):
    _fields_ = [("type", ctypes.c_uint32), ("pid", ctypes.c_uint32), ("mode", ctypes.c_uint32)]


class PropVariantBlob(ctypes.Structure):
    _fields_ = [("vt", ctypes.c_uint16), ("r1", ctypes.c_uint16), ("r2", ctypes.c_uint16), ("r3", ctypes.c_uint16),
                ("cb", ctypes.c_uint32), ("data", c_void_p)]


def _vt(ptr, slot, restype, *argtypes):
    vtbl = ctypes.cast(ctypes.cast(ptr, POINTER(c_void_p))[0], POINTER(c_void_p))
    return WINFUNCTYPE(restype, c_void_p, *argtypes)(vtbl[slot])


class _Handler:
    """Minimal IActivateAudioInterfaceCompletionHandler (also answers as IAgileObject)."""

    def __init__(self):
        self.done = threading.Event()
        self.op = None
        self._qi = WINFUNCTYPE(HRESULT, c_void_p, c_void_p, POINTER(c_void_p))(self._query)
        self._ref = WINFUNCTYPE(ctypes.c_ulong, c_void_p)(lambda s: 1)
        self._done = WINFUNCTYPE(HRESULT, c_void_p, c_void_p)(self._completed)
        self._vtbl = (c_void_p * 4)(*[ctypes.cast(f, c_void_p) for f in (self._qi, self._ref, self._ref, self._done)])
        self._obj = (c_void_p * 1)(ctypes.cast(self._vtbl, c_void_p))
        self.ptr = ctypes.cast(self._obj, c_void_p)

    def _query(self, this, riid, out):
        out[0] = self.ptr.value
        return 0

    def _completed(self, this, op):
        self.op = op
        self.done.set()
        return 0


class ProcessCapture:
    def __init__(self, pid):
        ole32.CoInitializeEx(None, 0)  # MTA
        params = ActivationParams(1, pid, 0)  # PROCESS_LOOPBACK, INCLUDE_TARGET_PROCESS_TREE
        pv = PropVariantBlob(65, 0, 0, 0, ctypes.sizeof(params), ctypes.cast(byref(params), c_void_p))
        handler, op = _Handler(), c_void_p()
        mmdev.ActivateAudioInterfaceAsync.argtypes = [c_wchar_p, POINTER(GUID), c_void_p, c_void_p, POINTER(c_void_p)]
        hr = mmdev.ActivateAudioInterfaceAsync("VAD\\Process_Loopback", byref(IID_IAudioClient),
                                               byref(pv), handler.ptr, byref(op))
        if hr != 0 or not handler.done.wait(5):
            raise OSError(f"ActivateAudioInterfaceAsync failed ({hr & 0xFFFFFFFF:#x})")
        result, unk = ctypes.c_long(), c_void_p()
        _vt(handler.op, 3, HRESULT, POINTER(ctypes.c_long), POINTER(c_void_p))(handler.op, byref(result), byref(unk))
        if result.value != 0 or not unk:
            raise OSError(f"Activation result {result.value & 0xFFFFFFFF:#x}")
        self.client = unk
        fmt = WAVEFORMATEX(1, CHANNELS, RATE, RATE * FRAME_BYTES, FRAME_BYTES, BITS, 0)
        flags = 0x00020000 | 0x00040000 | 0x80000000 | 0x08000000  # loopback|event|autoconvert|SRC
        _vt(self.client, 3, HRESULT, ctypes.c_int, wintypes.DWORD, ctypes.c_int64, ctypes.c_int64,
            POINTER(WAVEFORMATEX), c_void_p)(self.client, 0, flags, 200 * 10000, 0, byref(fmt), None)
        self.event = kernel32.CreateEventW(None, False, False, None)
        _vt(self.client, 13, HRESULT, c_void_p)(self.client, self.event)
        cc = c_void_p()
        _vt(self.client, 14, HRESULT, POINTER(GUID), POINTER(c_void_p))(self.client, byref(IID_IAudioCaptureClient), byref(cc))
        self.cap = cc
        self._get = _vt(cc, 3, HRESULT, POINTER(POINTER(c_ubyte)), POINTER(c_uint32), POINTER(wintypes.DWORD),
                        POINTER(c_uint64), POINTER(c_uint64))
        self._release = _vt(cc, 4, HRESULT, c_uint32)
        self._next = _vt(cc, 5, HRESULT, POINTER(c_uint32))
        _vt(self.client, 10, HRESULT)(self.client)

    def read(self, timeout_ms=100):
        """Return available audio as int16 stereo bytes (possibly empty)."""
        kernel32.WaitForSingleObject(self.event, timeout_ms)
        out = bytearray()
        n = c_uint32()
        while self._next(self.cap, byref(n)) == 0 and n.value:
            data, frames, fl = POINTER(c_ubyte)(), c_uint32(), wintypes.DWORD()
            self._get(self.cap, byref(data), byref(frames), byref(fl), None, None)
            if fl.value & 2:  # AUDCLNT_BUFFERFLAGS_SILENT
                out += bytes(frames.value * FRAME_BYTES)
            else:
                out += ctypes.string_at(data, frames.value * FRAME_BYTES)
            self._release(self.cap, frames.value)
        return bytes(out)

    def close(self):
        _vt(self.client, 11, HRESULT)(self.client)
