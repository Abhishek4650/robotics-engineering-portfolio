#!/usr/bin/env python3
"""ARM-450 bus check -- READ ONLY.

Answers one question: is there a live servo on the bus, and if not, how far
down the chain does the signal actually get?

Runs three stages and never commands motion (PING 0x01 and READ 0x02 only):

  1  USB       -- does the CP210x bridge enumerate and open
  2  ESP32     -- pulse the auto-reset line and listen for the boot banner.
                  A powered ESP32 ALWAYS prints a ROM banner on reset, even
                  with completely erased flash. Silence here means the chip
                  is not running -- almost always missing DC power, because
                  USB powers the bridge chip only.
  3  servos    -- ping every ID at every plausible baud rate

Run:  /home/user/robotic_arm/venv/bin/python /home/user/arm_demo/bus_check.py
"""
import sys, time, serial

PORT  = "/dev/ttyUSB0"
BAUDS = [1000000, 115200, 500000, 250000, 128000, 76800, 57600, 38400]
IDS   = list(range(0, 21))

# --- ST/SMS (Feetech) register map -------------------------------------
R_MODEL, R_POS, R_LOAD, R_VOLT, R_TEMP, R_TORQUE = 3, 56, 60, 62, 63, 40


def ck(b):
    return (~sum(b)) & 0xFF


def port(baud, timeout=0.06):
    s = serial.Serial()
    s.port, s.baudrate, s.timeout = PORT, baud, timeout
    s.dtr = s.rts = False          # do not reset the ESP32 on open
    s.open()
    time.sleep(0.05)
    return s


def txrx(s, body, nparam=0):
    s.reset_input_buffer()
    s.write(bytes([0xFF, 0xFF] + body + [ck(body)]))
    s.flush()
    need, buf, t0 = 6 + nparam, b"", time.time()
    while time.time() - t0 < 0.06 and len(buf) < need:
        c = s.read(need - len(buf))
        if not c:
            break
        buf += c
    i = buf.find(b"\xff\xff")
    if i < 0 or len(buf) < i + 5:
        return None
    ln = buf[i + 3]
    fr = buf[i:i + 4 + ln]
    return None if len(fr) < 4 + ln else dict(id=fr[2], err=fr[4],
                                              params=list(fr[5:5 + ln - 2]))


def ping(s, sid):
    return txrx(s, [sid, 0x02, 0x01]) is not None


def rd(s, sid, addr, n):
    r = txrx(s, [sid, 0x04, 0x02, addr, n], n)
    return r["params"] if r and len(r["params"]) == n else None


def stage1():
    print("1  USB bridge")
    try:
        s = port(115200)
        s.close()
        print(f"   OK    {PORT} opens\n")
        return True
    except Exception as e:
        print(f"   FAIL  {e}\n")
        return False


def stage2():
    """Reset the ESP32 and listen. Returns True if it said anything."""
    print("2  ESP32 alive?")
    for baud in (115200, 74880):
        s = port(baud, timeout=0.2)
        s.dtr = False           # IO0 high -> normal boot, not flash mode
        s.rts = True            # EN  low  -> hold reset
        time.sleep(0.15)
        s.reset_input_buffer()
        s.rts = False           # EN  high -> run
        buf, t0 = b"", time.time()
        while time.time() - t0 < 2.5:
            buf += s.read(4096)
        s.close()
        if buf:
            print(f"   OK    boot banner at {baud} ({len(buf)} bytes):")
            print("        " + buf.decode("utf-8", "replace")[:400]
                  .replace("\n", "\n        "))
            print()
            return True
    print("   FAIL  silent at 115200 and 74880 after a reset pulse.")
    print("         A powered ESP32 prints a ROM banner even with erased")
    print("         flash -- so this is a POWER or WIRING fault, not firmware.\n")
    return False


def stage3():
    print("3  servo bus")
    found = False
    for baud in BAUDS:
        s = port(baud)
        hits = sorted({sid for sid in IDS if ping(s, sid)})
        if hits:
            found = True
            print(f"   baud {baud}: IDs {hits}")
            for sid in hits:
                w = lambda p: (p[0] | p[1] << 8) if p else None
                m, p = rd(s, sid, R_MODEL, 2), rd(s, sid, R_POS, 2)
                v, t = rd(s, sid, R_VOLT, 1), rd(s, sid, R_TEMP, 1)
                ld, tq = rd(s, sid, R_LOAD, 2), rd(s, sid, R_TORQUE, 1)
                pos = w(p)
                print(f"     ID {sid:>2}  model {w(m)}  pos {pos} "
                      f"({pos * 360 / 4096:.1f} deg)" if pos is not None
                      else f"     ID {sid:>2}  model {w(m)}")
                print(f"            {v[0]/10 if v else '?'} V   "
                      f"{t[0] if t else '?'} C   load {w(ld)}   "
                      f"torque_enable {tq[0] if tq else '?'}")
        else:
            print(f"   baud {baud}: silent")
        s.close()
    if not found:
        print("\n   No servo answered at any baud rate.")
    return found


if __name__ == "__main__":
    print(f"ARM-450 bus check  --  read only, nothing will move\n")
    if not stage1():
        sys.exit(1)
    esp = stage2()
    srv = stage3()
    print("\n" + "=" * 58)
    if srv:
        print("RESULT: servos are alive and answering.")
    elif esp:
        print("RESULT: ESP32 runs, servo bus is silent.")
        print("        -> servo power, bus wiring, or forwarding not enabled.")
    else:
        print("RESULT: USB bridge only. ESP32 is not running.")
        print("        -> check the board's DC input first; USB powers the")
        print("           CP210x alone, so the port appears either way.")
    sys.exit(0 if srv else 2)
