"""Real app icons and friendly names for the app picker (Windows shell APIs via ctypes)."""
import ctypes
from ctypes import wintypes
from pathlib import Path

from PIL import Image

shell32 = ctypes.WinDLL("shell32")
user32 = ctypes.WinDLL("user32")
gdi32 = ctypes.WinDLL("gdi32")
version = ctypes.WinDLL("version")


class ICONINFO(ctypes.Structure):
    _fields_ = [("fIcon", wintypes.BOOL), ("xHotspot", wintypes.DWORD), ("yHotspot", wintypes.DWORD),
                ("hbmMask", wintypes.HBITMAP), ("hbmColor", wintypes.HBITMAP)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long), ("biYPelsPerMeter", ctypes.c_long),
                ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]


VP = ctypes.c_void_p
user32.GetDC.restype = VP
user32.GetDC.argtypes = [VP]
user32.ReleaseDC.argtypes = [VP, VP]
user32.GetIconInfo.argtypes = [VP, ctypes.POINTER(ICONINFO)]
user32.DestroyIcon.argtypes = [VP]
gdi32.GetDIBits.argtypes = [VP, VP, wintypes.UINT, wintypes.UINT, VP, VP, wintypes.UINT]
gdi32.DeleteObject.argtypes = [VP]
gdi32.GetObjectW.argtypes = [VP, ctypes.c_int, VP]


def _bits(hbm, w, h):
    hdr = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    dc = user32.GetDC(None)
    gdi32.GetDIBits(dc, hbm, 0, h, buf, ctypes.byref(hdr), 0)
    user32.ReleaseDC(None, dc)
    return buf.raw


def exe_icon(path, size=20):
    """PIL RGBA image of the exe's small icon, or None."""
    large, small = wintypes.HICON(), wintypes.HICON()
    if shell32.ExtractIconExW(str(path), 0, ctypes.byref(large), ctypes.byref(small), 1) < 1:
        return None
    hicon = small.value or large.value
    try:
        info = ICONINFO()
        if not user32.GetIconInfo(hicon, ctypes.byref(info)):
            return None
        bm = (ctypes.c_long * 8)()  # BITMAP (32 bytes on x64): type,width,height,...
        gdi32.GetObjectW(info.hbmColor, 32, bm)
        w, h = bm[1], bm[2]
        px = bytearray(_bits(info.hbmColor, w, h))
        if not any(px[3::4]):  # icon without alpha: use mask
            mask = _bits(info.hbmMask, w, h)
            for i in range(w * h):
                px[i * 4 + 3] = 0 if mask[i * 4] else 255
        gdi32.DeleteObject(info.hbmColor)
        gdi32.DeleteObject(info.hbmMask)
        img = Image.frombuffer("RGBA", (w, h), bytes(px), "raw", "BGRA", 0, 1)
        return img.resize((size, size), Image.LANCZOS)
    finally:
        user32.DestroyIcon(large)
        user32.DestroyIcon(small)


def friendly_name(path, fallback):
    """FileDescription from the exe's version info (e.g. 'Microsoft Edge'), else a tidied exe name."""
    try:
        size = version.GetFileVersionInfoSizeW(str(path), None)
        if size:
            buf = ctypes.create_string_buffer(size)
            version.GetFileVersionInfoW(str(path), 0, size, buf)
            tr, n = ctypes.c_void_p(), wintypes.UINT()
            if version.VerQueryValueW(buf, "\\VarFileInfo\\Translation", ctypes.byref(tr), ctypes.byref(n)) and n.value:
                lang, cp = ctypes.cast(tr, ctypes.POINTER(wintypes.WORD * 2)).contents
                for key in ("FileDescription", "ProductName"):
                    val, vn = ctypes.c_void_p(), wintypes.UINT()
                    if version.VerQueryValueW(buf, f"\\StringFileInfo\\{lang:04x}{cp:04x}\\{key}",
                                              ctypes.byref(val), ctypes.byref(vn)) and vn.value:
                        s = ctypes.wstring_at(val.value).strip()
                        if s:
                            return s
    except Exception:  # noqa: BLE001
        pass
    return Path(fallback).stem.replace("_", " ").replace("-", " ").title()
