#!/usr/bin/env python3
"""STAGE B - guarded slow ~20 deg move of joints 5 and 6 over the Waveshare
ESP32 SERIAL_FORWARDING USB bridge.

Safety design (why this won't slam the arm):
  * FRAMING GATE: first write commands the servo to its CURRENT position.
    Correct framing/endianness -> zero motion. Wrong -> caught within 0.4 s
    (only a few deg at the low speed used) and the script HALTS + aborts.
  * PROBE: a ~5 deg slow nudge, verified by reading position back, confirms
    direction and counts-per-degree before the real move.
  * MOVE: exactly +20 deg (or -20 if +20 is near a limit), slow.
  * RETURN: back to the exact start position.
  * One joint at a time; torque stays ON; never touches CalibrationOfs/max/min.
  * Any anomaly -> write goal=present (stop) and abort.

Usage:
  scs_move.py --family SC|ST [--joints 5 6] [--deg 20] [--go]
Without --go it does a DRY diagnostic (read-only) and prints the plan.
"""
import sys, time, argparse, serial

PORT, USB_BAUD = "/dev/ttyUSB0", 115200
R_MODE, R_POS = 33, 56

FAM = {
    # counts_full, deg_full, End(1=BE/SC,0=LE/ST), slow_speed, acc, lo, hi
    "SC": dict(counts=1024, deg=210.0, End=1, speed=150, acc=None, lo=40,  hi=983),
    "ST": dict(counts=4096, deg=360.0, End=0, speed=300, acc=20,  lo=150, hi=3945),
}


def ck(b): return (~sum(b)) & 0xFF


def open_no_reset():
    s = serial.Serial()
    s.port, s.baudrate, s.timeout = PORT, USB_BAUD, 0.35
    s.dtr = False; s.rts = False
    s.open()
    return s


def txn(s, body, expect=0):
    s.reset_input_buffer()
    s.write(bytes([0xFF, 0xFF] + body + [ck(body)]))
    t0 = time.time(); buf = b""
    while time.time() - t0 < 0.35 and len(buf) < 10 + expect:
        c = s.read(64)
        if c: buf += c
        elif buf: break
    i = buf.find(b"\xff\xff")
    if i < 0 or len(buf) < i + 4: return None
    ln = buf[i+3]; frame = buf[i:i+4+ln]
    if len(frame) < 4 + ln: return None
    return list(frame[5:5+ln-2])


def ping(s, sid): return txn(s, [sid, 0x02, 0x01]) is not None
def read_reg(s, sid, addr, n): return txn(s, [sid, 0x04, 0x02, addr, n], expect=n)


def enc(val, End):
    val &= 0xFFFF
    hi, lo = (val >> 8) & 0xFF, val & 0xFF
    return [hi, lo] if End else [lo, hi]   # SC big-endian, ST little-endian


def read_pos(s, sid, End):
    b = read_reg(s, sid, R_POS, 2)
    if not b or len(b) != 2: return None
    return (b[0] << 8 | b[1]) if End else (b[0] | b[1] << 8)


def write_goal(s, sid, pos, fam):
    """Position-mode goal write, slow speed, for SC or ST family."""
    End, spd = fam["End"], fam["speed"]
    if fam is FAM["ST"]:
        data = [fam["acc"]] + enc(pos, End) + enc(0, End) + enc(spd, End)
        body = [sid, 3 + 7, 0x03, 41] + data          # reg 41, 7 bytes
    else:
        data = enc(pos, End) + enc(0, End) + enc(spd, End)
        body = [sid, 3 + 6, 0x03, 42] + data          # reg 42, 6 bytes
    s.reset_input_buffer()
    s.write(bytes([0xFF, 0xFF] + body + [ck(body)]))
    time.sleep(0.02)


def halt(s, sid, fam):
    p = read_pos(s, sid, fam["End"])
    if p is not None:
        write_goal(s, sid, p, fam)
    print(f"    !! HALT servo {sid} at {p}")


def wait_for_bridge(s):
    print("PORT OPEN (the board just rebooted, so forwarding is OFF).", flush=True)
    print(">>> On the phone: RELOAD http://192.168.4.1 , then tap "
          "'Start Serial Forwarding' and confirm. <<<", flush=True)
    t0 = time.time(); n = 0
    while time.time() - t0 < 240:
        if ping(s, 5) or ping(s, 6):
            print("Bridge LIVE.", flush=True); return True
        n += 1
        if n % 4 == 0:
            print(f"  ... waiting for forwarding ({int(time.time()-t0)}s)",
                  flush=True)
        time.sleep(1.5)
    return False


def do_joint(s, sid, fam, deg, go):
    End = fam["End"]
    cpd = fam["counts"] / fam["deg"]                  # counts per degree
    d20 = round(deg * cpd)
    p0 = read_pos(s, sid, End)
    if p0 is None:
        print(f"  servo {sid}: cannot read position, skip"); return
    a0 = p0 / cpd
    # move TOWARD the centre of travel (safest away from end-stops)
    mid = fam["counts"] // 2
    sign = -1 if p0 > mid else 1
    tgt_full = p0 + sign * d20
    if tgt_full > fam["hi"] or tgt_full < fam["lo"]:
        print(f"  servo {sid}: target {tgt_full} near a limit (pos {p0}), skip"); return
    print(f"  servo {sid}: start {p0} counts ({a0:.1f} deg); plan {'+' if sign>0 else '-'}{deg} deg "
          f"= {sign*d20} counts, slow speed {fam['speed']}")
    if not go:
        print("    (dry run - not sending)"); return

    # 1) FRAMING GATE: command current position; expect ~no motion.
    write_goal(s, sid, p0, fam); time.sleep(0.4)
    pg = read_pos(s, sid, End)
    if pg is None or abs(pg - p0) > max(8, int(0.5 * cpd)):
        print(f"    framing check FAILED (pos {p0}->{pg}); aborting this joint")
        halt(s, sid, fam); return
    print(f"    framing OK (pos {p0}->{pg})")

    # 2) PROBE ~5 deg
    probe = sign * round(5 * cpd)
    write_goal(s, sid, p0 + probe, fam); time.sleep(1.0)
    p1 = read_pos(s, sid, End)
    moved = (p1 - p0) if p1 is not None else 0
    if p1 is None or moved * sign <= 0 or abs(moved) > abs(probe) * 2.2:
        print(f"    probe anomaly (moved {moved}, expected ~{probe}); aborting joint")
        halt(s, sid, fam); return
    print(f"    probe OK (moved {moved} counts ~ {moved/cpd:.1f} deg)")

    # 3) FULL 20 deg
    tgt = p0 + sign * d20
    write_goal(s, sid, tgt, fam); time.sleep(2.5)
    p2 = read_pos(s, sid, End)
    print(f"    moved to {p2} counts ({p2/cpd:.1f} deg), target was {tgt}")

    # 4) RETURN
    write_goal(s, sid, p0, fam); time.sleep(2.5)
    p3 = read_pos(s, sid, End)
    print(f"    returned to {p3} counts ({p3/cpd:.1f} deg), start was {p0}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=["SC", "ST"], required=True)
    ap.add_argument("--joints", type=int, nargs="+", default=[5, 6])
    ap.add_argument("--deg", type=float, default=20.0)
    ap.add_argument("--go", action="store_true")
    args = ap.parse_args()
    fam = FAM[args.family]

    s = open_no_reset(); time.sleep(0.2)
    if not (ping(s, 5) or ping(s, 6)):
        if not wait_for_bridge(s):
            print("No servo response; is forwarding on?"); s.close(); return
    print(f"\nFamily={args.family}  joints={args.joints}  deg={args.deg}  "
          f"{'LIVE MOVE' if args.go else 'DRY RUN'}\n")
    try:
        for sid in args.joints:
            if not ping(s, sid):
                print(f"  servo {sid}: no ping, skip"); continue
            do_joint(s, sid, fam, args.deg, args.go)
    except Exception as e:
        print("ERROR:", e)
        for sid in args.joints:
            try: halt(s, sid, fam)
            except Exception: pass
    finally:
        s.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
