#!/usr/bin/env python3
"""
Is the ESP32 chip alive? -- the definitive test, independent of firmware.

Listening for a boot banner assumes the chip is running SOMETHING and that it
prints at a baud rate we guessed. This does not. It drives the board into the
ROM download mode and speaks the ROM bootloader's own protocol at it.

That ROM is in mask silicon. It answers SYNC on a blank chip, on an erased
chip, on a chip whose firmware crashes at boot, and on a chip whose app never
prints. If SYNC gets a reply, the ESP32 is powered, clocked and executing. If
it does not, no firmware fix can help -- the fault is power, wiring, or the
board's USB-to-ESP32 path.

Nothing is written. SYNC is a handshake; no flash operation follows.
"""
import struct
import sys
import time

import serial

PORT = "/dev/ttyUSB0"
SYNC_DATA = b"\x07\x07\x12\x20" + b"\x55" * 32


def slip(payload):
    out = bytearray([0xC0])
    for b in payload:
        if b == 0xDB:
            out += b"\xdb\xdd"
        elif b == 0xC0:
            out += b"\xdb\xdc"
        else:
            out.append(b)
    out.append(0xC0)
    return bytes(out)


def sync_frame():
    # direction 0x00 (request), command 0x08 (SYNC), size, checksum, data
    pkt = (b"\x00\x08" + struct.pack("<H", len(SYNC_DATA))
           + struct.pack("<I", 0) + SYNC_DATA)
    return slip(pkt)


def classic_reset(s, download=True):
    """esptool's ClassicReset. DTR drives IO0, RTS drives EN, both inverted by
    the board's two-transistor circuit.  IO0 low at the moment EN is released
    is what selects the ROM download mode."""
    s.dtr = False          # IO0 HIGH
    s.rts = True           # EN  LOW  -> hold in reset
    time.sleep(0.1)
    s.dtr = bool(download)  # IO0 LOW -> download mode on release
    s.rts = False          # EN  HIGH -> run
    time.sleep(0.05)
    s.dtr = False          # release IO0


def try_sync(baud, attempts=8):
    s = serial.Serial()
    s.port, s.baudrate, s.timeout = PORT, baud, 0.12
    try:
        s.open()
    except Exception as e:
        print(f"    {baud:>7}: cannot open -- {e}")
        return None
    classic_reset(s, download=True)
    time.sleep(0.08)
    s.reset_input_buffer()
    frame = sync_frame()
    for k in range(attempts):
        s.write(frame)
        s.flush()
        t0 = time.time()
        buf = b""
        while time.time() - t0 < 0.12:
            c = s.read(256)
            if not c:
                break
            buf += c
        if buf:
            s.close()
            return buf
        time.sleep(0.05)
    s.close()
    return b""


def main():
    print("ESP32 liveness test -- ROM bootloader SYNC (writes nothing)\n")
    print(f"  port {PORT}")
    print("  driving the board into ROM download mode and sending SYNC ...\n")

    hit = None
    for baud in (115200, 74880, 230400, 921600, 57600):
        r = try_sync(baud)
        if r is None:
            continue
        if r:
            print(f"    {baud:>7}: {len(r)} bytes back  {r[:40].hex()}")
            hit = (baud, r)
            break
        print(f"    {baud:>7}: no reply")

    print()
    print("=" * 62)
    if hit:
        baud, r = hit
        ok = b"\xc0" in r
        print("RESULT: the ESP32 ANSWERED.")
        print(f"        ROM bootloader replied at {baud} baud"
              f"{' (valid SLIP frame)' if ok else ''}.")
        print("        The chip is powered, clocked and executing. Any")
        print("        remaining fault is firmware or wiring, not the board.")
        return 0
    print("RESULT: no reply from the ROM bootloader at any baud rate.")
    print()
    print("  The ROM answers SYNC on a blank chip, so this is not a")
    print("  firmware problem. In order of likelihood:")
    print("    1. the board's USB-serial chip is not wired to the ESP32's")
    print("       UART0 -- some carrier boards need a jumper or switch")
    print("    2. no power to the ESP32 itself (USB feeds the CP210x alone")
    print("       on boards that take a separate DC input)")
    print("    3. auto-reset not wired: hold BOOT, tap EN, release BOOT,")
    print("       then re-run this script")
    print("    4. a charge-only USB cable -- data lines absent")
    print("    5. the ESP32 module is dead")
    return 2


if __name__ == "__main__":
    sys.exit(main())
