"""python -m multiout --app spotify.exe --device "Speakers" --device "Headphones:120" """
import argparse
import time

import psutil

from .mirror import Mirror, output_devices


def main(argv=None):
    ap = argparse.ArgumentParser(prog="multiout", description="Play one app on several devices at once.")
    ap.add_argument("--list", action="store_true", help="list output devices")
    ap.add_argument("--app", help="process name, e.g. spotify.exe")
    ap.add_argument("--device", action="append", default=[], help="name substring, optional :delay_ms:volume_pct")
    args = ap.parse_args(argv)
    devs = output_devices()
    if args.list or not args.app:
        for i, n in devs:
            print(f"{i}\t{n}")
        return
    pid = next((p.pid for p in psutil.process_iter(["name"])
                if (p.info["name"] or "").lower() == args.app.lower()), None)
    if pid is None:
        raise SystemExit(f"{args.app} is not running")
    wanted = {}
    for spec in args.device:
        name, _, rest = spec.partition(":"); ms, _, vol = rest.partition(":")
        match = next((i for i, n in devs if name.lower() in n.lower()), None)
        if match is None:
            raise SystemExit(f"No device matching '{name}'")
        wanted[match] = (int(ms or 0), float(vol or 100) / 100)
    m = Mirror(pid)
    m.set_sinks(wanted)
    m.start()
    print("Mirroring... Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        m.stop()
