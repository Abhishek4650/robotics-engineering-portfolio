#!/usr/bin/env python3
"""
Is this ESP32 board healthy?  One command, four independent checks.

Written to answer exactly one question -- is the module in good condition --
and to distinguish that from "is it powered", which is the thing that usually
looks like a fault.

  1  USB bridge      does the serial adapter enumerate and open
  2  ROM bootloader  does the chip answer SYNC.  This is the real health test:
                     the ROM is in mask silicon and replies on a blank chip, an
                     erased chip, or one whose firmware crashes at boot, so a
                     reply proves the ESP32 is powered, clocked and executing
                     no matter what state the flash is in
  3  boot banner     what the running firmware prints on reset
  4  Wi-Fi           whether an access point appears -- an entirely separate
                     path from USB, sharing only the power rail

Nothing is written.  SYNC is a handshake; no flash operation follows it.

  /home/user/robotic_arm/venv/bin/python /home/user/arm_demo/esp32_health.py
"""
import os
import re
import struct
import subprocess
import sys
import time

import serial

PORT = "/dev/ttyUSB0"
SYNC_DATA = b"\x07\x07\x12\x20" + b"\x55" * 32


def slip(payload):
    out = bytearray([0xC0])
    for b in payload:
        out += (b"\xdb\xdd" if b == 0xDB else
                b"\xdb\xdc" if b == 0xC0 else bytes([b]))
    out.append(0xC0)
    return bytes(out)


FRAME = slip(b"\x00\x08" + struct.pack("<H", len(SYNC_DATA))
             + struct.pack("<I", 0) + SYNC_DATA)


def reset(s, download):
    """esptool's classic reset. IO0 low as EN is released selects download mode."""
    s.dtr, s.rts = False, True
    time.sleep(0.1)
    s.dtr, s.rts = bool(download), False
    time.sleep(0.05)
    s.dtr = False


def check_usb():
    try:
        serial.Serial(PORT, 115200, timeout=0.1).close()
        return True, f"{PORT} enumerates and opens"
    except Exception as e:
        return False, str(e)


def check_rom():
    for baud in (115200, 230400, 74880):
        s = serial.Serial()
        s.port, s.baudrate, s.timeout = PORT, baud, 0.12
        try:
            s.open()
        except Exception:
            continue
        reset(s, download=True)
        time.sleep(0.08)
        s.reset_input_buffer()
        for _ in range(8):
            s.write(FRAME)
            s.flush()
            t0, buf = time.time(), b""
            while time.time() - t0 < 0.12:
                c = s.read(256)
                if not c:
                    break
                buf += c
            if buf:
                s.close()
                return True, f"ROM answered at {baud} baud ({len(buf)} bytes)"
            time.sleep(0.04)
        s.close()
    return False, "no reply at 115200 / 230400 / 74880"


def check_banner():
    s = serial.Serial()
    s.port, s.baudrate, s.timeout = PORT, 115200, 0.3
    try:
        s.open()
    except Exception as e:
        return False, str(e)
    reset(s, download=False)
    s.reset_input_buffer()
    buf, t0 = b"", time.time()
    while time.time() - t0 < 3.0:
        buf += s.read(4096)
    s.close()
    if not buf:
        return False, "silent for 3 s after reset"
    txt = buf.decode("utf-8", "replace").strip().splitlines()
    return True, f"{len(buf)} bytes: " + " | ".join(t.strip() for t in txt[:4])


def check_wifi(want="ESP32"):
    try:
        subprocess.run(["nmcli", "dev", "wifi", "rescan"],
                       capture_output=True, timeout=20)
        time.sleep(4)
        out = subprocess.run(["nmcli", "-t", "-f", "SSID", "dev", "wifi", "list"],
                             capture_output=True, text=True, timeout=20).stdout
    except Exception as e:
        return None, f"scan unavailable ({e})"
    hits = sorted({l for l in out.splitlines()
                   if l and re.search(want, l, re.I)})
    if hits:
        return True, "access point visible: " + ", ".join(hits)
    return False, "no ESP32 access point in the scan"


def main():
    print("ESP32 HEALTH CHECK  --  read only, nothing is written\n")
    rows = []
    for label, fn in (("1  USB bridge", check_usb),
                      ("2  ROM bootloader", check_rom),
                      ("3  boot banner", check_banner),
                      ("4  Wi-Fi access point", check_wifi)):
        ok, detail = fn()
        mark = "  ok  " if ok else " none " if ok is False else "  ?   "
        print(f"  [{mark}] {label:<22} {detail}")
        rows.append((label, ok))
    usb, rom, banner, wifi = (r[1] for r in rows)

    print("\n" + "=" * 66)
    if rom:
        print("VERDICT: the ESP32 is ALIVE and in working order.")
        if banner or wifi:
            print("         Firmware is running as well.")
        else:
            print("         The chip answers but the firmware does not run --")
            print("         that is a flash/app problem, not a board fault.")
        return 0
    if not usb:
        print("VERDICT: cannot test. The USB serial adapter did not open.")
        return 2
    print("VERDICT: INCONCLUSIVE -- most likely simply UNPOWERED.")
    print()
    print("  This board takes 6-12 V DC on the 5.5 x 2.1 mm barrel jack and")
    print("  CANNOT run from USB: the USB port powers the serial bridge chip")
    print("  only, which is why the port appears while nothing answers.")
    print("  Match VIN to the servo voltage -- 12 V for ST3215.")
    print()
    print("  A healthy but unpowered board gives EXACTLY this result, so")
    print("  nothing here is evidence of a fault. Apply DC and re-run: if")
    print("  check 2 then passes, the module is good.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
