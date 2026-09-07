#!/usr/bin/env python3
"""STAGE A - READ ONLY diagnostic over the Waveshare ESP32 'SERIAL_FORWARDING'
USB bridge. Pings servos and dumps registers. Sends NO motion command
(only PING 0x01 and READ 0x02). Determines servo family (SC vs ST) and
current angles so the follow-up move script uses correct units/endianness.

Run:  /home/user/robotic_arm/venv/bin/python /home/user/arm_demo/scs_diag.py
Enable 'Start Serial Forwarding' on the phone web UI (192.168.4.1) when asked.
"""
import sys, time, serial

PORT = "/dev/ttyUSB0"
USB_BAUD = 115200          # bridge speed; ESP32 relays to the 1 Mbps servo bus
IDS = [5, 6, 2, 3, 4, 1]   # joints of interest first; 1 expected dead

# --- register addresses (same numbers for SC and ST families) ---
R_MODEL = 3      # 2 bytes  (ST: model, SC: version)
R_ID    = 5      # 1 byte
R_MODE  = 33     # 1 byte   (ST only; SC ignores)
R_POS   = 56     # 2 bytes  present position


def open_no_reset():
    """Open the port without pulsing DTR/RTS, so the ESP32 is NOT reset
    (a reset would drop it out of SERIAL_FORWARDING)."""
    s = serial.Serial()
    s.port = PORT
    s.baudrate = USB_BAUD
    s.timeout = 0.35
    s.dtr = False
    s.rts = False
    s.open()
    return s


def ck(body):
    return (~sum(body)) & 0xFF


def ping(s, sid):
    body = [sid, 0x02, 0x01]
    s.reset_input_buffer()
    s.write(bytes([0xFF, 0xFF] + body + [ck(body)]))
    r = read_pkt(s)
    return r is not None


def read_reg(s, sid, addr, n):
    body = [sid, 0x04, 0x02, addr, n]
    s.reset_input_buffer()
    s.write(bytes([0xFF, 0xFF] + body + [ck(body)]))
    return read_pkt(s, expect_params=n)


def read_pkt(s, expect_params=0, timeout=0.35):
    """Parse FF FF ID LEN ERR [params...] CHK. Returns list of param bytes
    (possibly empty) on success, or None."""
    t0 = time.time()
    buf = b""
    need = 6 + expect_params
    while time.time() - t0 < timeout and len(buf) < need + 4:
        c = s.read(need + 4 - len(buf) or 1)
        if c:
            buf += c
        elif buf:
            break
    i = buf.find(b"\xff\xff")
    if i < 0 or len(buf) < i + 4:
        return None
    sid, ln = buf[i+2], buf[i+3]
    frame = buf[i:i+4+ln]
    if len(frame) < 4 + ln:
        return None
    err = frame[4]
    params = list(frame[5:5+ln-2])
    return params


def main():
    print(f"Opening {PORT} without resetting the ESP32 ...")
    s = open_no_reset()
    time.sleep(0.2)

    print("Waiting for SERIAL_FORWARDING  ->  on your phone, open "
          "http://192.168.4.1 and tap 'Start Serial Forwarding' (confirm).")
    print("(polling servo 5 ...)")
    live = False
    t0 = time.time()
    n = 0
    while time.time() - t0 < 600:
        if ping(s, 5) or ping(s, 6):
            live = True
            break
        n += 1
        if n % 5 == 0:
            print(f"  ... still waiting ({int(time.time()-t0)}s) - "
                  f"forwarding not on yet", flush=True)
        time.sleep(3)
    if not live:
        print("No servo answered within 600 s. Is forwarding enabled? "
              "Is USB still /dev/ttyUSB0?")
        s.close(); sys.exit(1)

    print("\nBridge is LIVE. Reading registers (no motion) ...\n")
    results = {}
    for sid in IDS:
        if not ping(s, sid):
            print(f"  ID {sid}: no ping (not present)")
            continue
        model = read_reg(s, sid, R_MODEL, 2) or []
        idb   = read_reg(s, sid, R_ID, 1) or []
        mode  = read_reg(s, sid, R_MODE, 1) or []
        pos   = read_reg(s, sid, R_POS, 2) or []
        pos_le = (pos[0] | pos[1] << 8) if len(pos) == 2 else None   # ST
        pos_be = (pos[0] << 8 | pos[1]) if len(pos) == 2 else None   # SC
        results[sid] = dict(model=model, idb=idb, mode=mode,
                            pos=pos, le=pos_le, be=pos_be)
        print(f"  ID {sid}: model_bytes={model} id_readback={idb} "
              f"mode={mode}\n         pos_bytes={pos}  "
              f"pos(if ST/LE)={pos_le}  pos(if SC/BE)={pos_be}")

    # --- decide family from servos 5/6 ---
    print("\n--- interpretation ---")
    for sid in (5, 6):
        if sid not in results:
            continue
        r = results[sid]
        le, be = r["le"], r["be"]
        guess = []
        if le is not None and 0 <= le <= 4095:
            guess.append(f"ST: {le} counts = {le*360/4096:.1f} deg")
        if be is not None and 0 <= be <= 1023:
            guess.append(f"SC: {be} counts = {be*210/1024:.1f} deg")
        print(f"  servo {sid}: " + "  |  ".join(guess or ["unclear"]))
    print("\nSTAGE A done (nothing moved). Share this output before the move.")
    s.close()


if __name__ == "__main__":
    main()
