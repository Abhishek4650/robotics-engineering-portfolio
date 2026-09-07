#!/usr/bin/env python3
"""Continuous slow oscillation of joints 5 & 6 for N seconds over the
Waveshare ESP32 SERIAL_FORWARDING USB bridge (STS3215 / ST family).

Each joint sweeps +/- amp_deg around its CURRENT position as a slow sine
(joint 6 offset 90 deg in phase so they weave), then both return to start.

Safety: framing gate first (write current pos -> no motion), every target
clamped to a safe count window, torque stays on, and start positions are
restored on normal end, Ctrl-C, or any error.

Usage:
  scs_oscillate.py [--secs 30] [--amp-deg 15] [--freq 0.3] [--joints 5 6] --go
"""
import sys, os, time, math, argparse, serial

PORT, USB_BAUD = "/dev/ttyUSB0", 115200
LOG_DIR = "/home/user/robotic_motion/logs"
_logf = None


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {msg}"
    print(line, flush=True)
    if _logf:
        _logf.write(line + "\n"); _logf.flush()
R_POS = 56
END = 0                       # ST family = little-endian
COUNTS, DEG = 4096, 360.0
CPD = COUNTS / DEG            # counts per degree
LO, HI = 150, 3945           # safe count window
STREAM_SPEED, STREAM_ACC = 1500, 30   # servo follows the sine smoothly


def ck(b): return (~sum(b)) & 0xFF


def open_no_reset():
    s = serial.Serial()
    s.port, s.baudrate, s.timeout = PORT, USB_BAUD, 0.3
    s.dtr = False; s.rts = False
    s.open()
    return s


def txn(s, body, expect=0, want_id=None):
    s.reset_input_buffer()
    s.write(bytes([0xFF, 0xFF] + body + [ck(body)]))
    t0 = time.time(); buf = b""
    while time.time() - t0 < 0.3 and len(buf) < 12 + expect:
        c = s.read(64)
        if c: buf += c
        elif buf: break
    # scan all frames; return the one whose ID matches want_id (skips stray
    # write-acks from the other servo that can land here during streaming)
    off = 0
    while True:
        i = buf.find(b"\xff\xff", off)
        if i < 0 or len(buf) < i + 4: return None
        ln = buf[i+3]; frame = buf[i:i+4+ln]
        if len(frame) < 4 + ln: return None
        if want_id is None or frame[2] == want_id:
            return list(frame[5:5+ln-2])
        off = i + 2


def ping(s, sid): return txn(s, [sid, 0x02, 0x01], want_id=sid) is not None


def read_pos(s, sid):
    b = txn(s, [sid, 0x04, 0x02, R_POS, 2], expect=2, want_id=sid)
    if not b or len(b) != 2: return None
    return b[0] | b[1] << 8


def enc(v):
    v &= 0xFFFF
    return [v & 0xFF, (v >> 8) & 0xFF]     # little-endian (ST)


def write_goal(s, sid, pos, speed=STREAM_SPEED):
    pos = max(LO, min(HI, int(pos)))
    data = [STREAM_ACC] + enc(pos) + enc(0) + enc(speed)   # reg 41: ACC,pos,time,speed
    body = [sid, 3 + 7, 0x03, 41] + data
    s.reset_input_buffer()
    s.write(bytes([0xFF, 0xFF] + body + [ck(body)]))


def wait_for_bridge(s):
    if ping(s, 5) or ping(s, 6):
        return True
    print("PORT OPEN (board rebooted -> forwarding OFF).", flush=True)
    print(">>> On the phone: RELOAD http://192.168.4.1 and tap "
          "'Start Serial Forwarding'. <<<", flush=True)
    t0 = time.time(); n = 0
    while time.time() - t0 < 240:
        if ping(s, 5) or ping(s, 6):
            print("Bridge LIVE.", flush=True); return True
        n += 1
        if n % 4 == 0:
            print(f"  ... waiting ({int(time.time()-t0)}s)", flush=True)
        time.sleep(1.5)
    return False


def main():
    global _logf
    ap = argparse.ArgumentParser()
    ap.add_argument("--secs", type=float, default=30.0)
    ap.add_argument("--amp-deg", type=float, default=15.0)
    ap.add_argument("--freq", type=float, default=0.3)     # Hz
    ap.add_argument("--joints", type=int, nargs="+", default=[5, 6])
    ap.add_argument("--go", action="store_true")
    a = ap.parse_args()
    amp = a.amp_deg * CPD
    joints = a.joints

    os.makedirs(LOG_DIR, exist_ok=True)
    logpath = os.path.join(LOG_DIR, "oscillate_" +
                           time.strftime("%Y%m%d_%H%M%S") + ".log")
    _logf = open(logpath, "w")
    log(f"=== oscillate joints {joints}  secs={a.secs}  amp={a.amp_deg}deg "
        f"freq={a.freq}Hz  go={a.go} ===")
    log(f"log file: {logpath}")

    s = open_no_reset(); time.sleep(0.2)
    if not wait_for_bridge(s):
        log("No servo response; is forwarding on?"); s.close(); return

    # read start positions
    start = {}
    for sid in joints:
        p = read_pos(s, sid)
        if p is None:
            log(f"servo {sid}: no position read, aborting"); s.close(); return
        start[sid] = p
        log(f"servo {sid}: start {p} counts ({p/CPD:.1f} deg)")

    # framing gate: command each to its current pos, expect no jump
    for sid in joints:
        write_goal(s, sid, start[sid])
    time.sleep(0.4)
    for sid in joints:
        pg = read_pos(s, sid)
        if pg is None or abs(pg - start[sid]) > max(8, int(0.5*CPD)):
            log(f"servo {sid}: framing check FAILED ({start[sid]}->{pg}); abort")
            s.close(); return
    log(f"framing OK; oscillating {a.secs:.0f}s, +/-{a.amp_deg:.0f} deg "
        f"@ {a.freq} Hz ...")

    if not a.go:
        log("(dry run - not sending motion)"); s.close(); return

    phase = {sid: i * math.pi/2 for i, sid in enumerate(joints)}  # weave
    t0 = time.time(); next_log = 0.0
    try:
        while True:
            t = time.time() - t0
            if t >= a.secs:
                break
            tgts = {}
            for sid in joints:
                tgt = start[sid] + amp*math.sin(2*math.pi*a.freq*t + phase[sid])
                tgts[sid] = int(max(LO, min(HI, tgt)))
                write_goal(s, sid, tgt)
            if t >= next_log:          # ~1 Hz: log target vs actual
                time.sleep(0.02); s.reset_input_buffer()  # let write-acks clear
                acts = {sid: read_pos(s, sid) for sid in joints}
                desc = "  ".join(f"J{sid} tgt={tgts[sid]} act={acts[sid]}"
                                 f"({(acts[sid] or 0)/CPD:.1f}d)" for sid in joints)
                log(f"t={t:4.1f}s  {desc}")
                next_log = t + 1.0
            time.sleep(0.05)           # ~20 Hz update
    except KeyboardInterrupt:
        log("interrupted - returning to start")
    finally:
        for sid in joints:            # ease back to start
            write_goal(s, sid, start[sid], speed=600)
        time.sleep(2.0)
        for sid in joints:
            p = read_pos(s, sid)
            log(f"servo {sid}: returned {p} counts ({p/CPD:.1f} deg), "
                f"start {start[sid]}")
        s.close()
    log("Done.  log saved: " + logpath)
    _logf.close()


if __name__ == "__main__":
    main()
