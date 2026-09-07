#!/usr/bin/env python3
"""Generate Robotic_Motion_Guide.pdf - a step-by-step operating guide for the
Waveshare ESP32 + STS3215 arm (joint moves, continuous motion, and the path
to running the R_sine sinusoidal motion on the real hardware)."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, ListFlowable, ListItem, HRFlowable)

OUT = "/home/user/robotic_motion/Robotic_Motion_Guide.pdf"
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, spaceBefore=14,
                    spaceAfter=6, textColor=colors.HexColor("#12335a"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, spaceBefore=8,
                    spaceAfter=4, textColor=colors.HexColor("#1f4e79"))
BODY = ParagraphStyle("BODY", parent=ss["BodyText"], fontSize=10, leading=14,
                      spaceAfter=4)
NOTE = ParagraphStyle("NOTE", parent=BODY, textColor=colors.HexColor("#7a3b00"))
TITLE = ParagraphStyle("TITLE", parent=ss["Title"], fontSize=22,
                       textColor=colors.HexColor("#12335a"))
SUB = ParagraphStyle("SUB", parent=BODY, fontSize=11,
                     textColor=colors.HexColor("#555555"))
CODE = ParagraphStyle("CODE", parent=ss["Code"], fontSize=8.5, leading=11,
                      textColor=colors.HexColor("#101010"))

story = []


def P(t, s=BODY): story.append(Paragraph(t, s))
def gap(h=4): story.append(Spacer(1, h))


def code(lines):
    if isinstance(lines, str):
        lines = [lines]
    txt = "<br/>".join(l.replace("&", "&amp;").replace("<", "&lt;")
                       .replace(">", "&gt;") for l in lines)
    tbl = Table([[Paragraph(txt, CODE)]], colWidths=[165*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f2f4f7")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd6dd")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    story.append(tbl)
    gap(6)


def steps(items):
    story.append(ListFlowable(
        [ListItem(Paragraph(t, BODY), leftIndent=6) for t in items],
        bulletType="1", start="1", leftIndent=14))
    gap(4)


def bullets(items):
    story.append(ListFlowable(
        [ListItem(Paragraph(t, BODY), leftIndent=6) for t in items],
        bulletType="bullet", leftIndent=14))
    gap(4)


PY = "/home/user/robotic_arm/venv/bin/python"
DIR = "/home/user/robotic_motion"

# ---------- Title ----------
P("Robotic Motion &mdash; Operating Guide", TITLE)
P("Waveshare &ldquo;Servo Driver with ESP32&rdquo; + Feetech STS3215 6-DOF arm", SUB)
P("Scripts &amp; logs: <b>/home/user/robotic_motion/</b> &nbsp;&bull;&nbsp; "
  "Generated 2026-07-25", SUB)
story.append(HRFlowable(width="100%", color=colors.HexColor("#cfd6dd"),
                        spaceBefore=6, spaceAfter=8))

# ---------- 1. What this is ----------
P("1. What the arm is and how it is controlled", H1)
bullets([
    "<b>Board:</b> Waveshare &ldquo;Servo Driver with ESP32&rdquo;, a Silicon "
    "Labs CP2102 USB-UART bridge on <b>/dev/ttyUSB0</b>.",
    "<b>Servos:</b> Feetech <b>STS3215</b> bus servos, IDs 1&ndash;6 "
    "(ST family: absolute position 0&ndash;4095 = 360&deg;, ~11.38 counts/deg). "
    "Joint 5 = wrist bend, Joint 6 = end-flange twist.",
    "<b>Power:</b> the servos need their own DC motor supply ON. Without it the "
    "board boots but every servo is dead (this was the original problem).",
    "<b>Control path:</b> in normal mode the USB port is <b>debug-only</b> &mdash; "
    "the firmware ignores USB commands. To command servos you enable "
    "<b>SERIAL_FORWARDING</b>, which turns the USB port into a transparent bridge "
    "to the 1&nbsp;Mbps servo bus. Then the PC speaks the Feetech protocol directly.",
    "<b>Enabling forwarding</b> is done from the board&rsquo;s own WiFi web page "
    "(access point <b>ESP32_DEV</b>, password <b>12345678</b>, "
    "<b>http://192.168.4.1</b>).",
])

P("THE GOLDEN RULE (important quirk)", H2)
P("Every time a program opens /dev/ttyUSB0, the ESP32 <b>reboots</b> (its reset "
  "pin is wired to the USB control lines) and SERIAL_FORWARDING switches "
  "<b>OFF</b>. So the order is always: <b>start the script first</b>, and only "
  "<b>after</b> it prints &ldquo;PORT OPEN &hellip; waiting&rdquo; do you "
  "(re)enable forwarding on the phone. Each script run needs one enable.", NOTE)

# ---------- 2. Prerequisites ----------
P("2. Every-session checklist", H1)
bullets([
    "Motor DC power supply <b>ON</b>; USB cable from the board to the PC.",
    "The board&rsquo;s small OLED is lit.",
    "Run all scripts with this Python (it has pyserial): <b>%s</b>" % PY,
    "You are in the <b>dialout</b> group (already done) so /dev/ttyUSB0 is usable.",
])

# ---------- 3. Enable forwarding ----------
P("3. Enable SERIAL_FORWARDING (phone) &mdash; do this when a script says "
  "&ldquo;waiting&rdquo;", H1)
steps([
    "On the phone WiFi settings, connect to <b>ESP32_DEV</b>, password "
    "<b>12345678</b>. Ignore the &ldquo;no internet&rdquo; warning and stay on it "
    "(turn mobile data off so the browser uses the board).",
    "Open a browser to <b>http://192.168.4.1</b> (http, not https). If it was "
    "already open, <b>reload</b> the page.",
    "Tap <b>&ldquo;Start Serial Forwarding&rdquo;</b> and tap <b>OK</b> on the "
    "confirm dialog.",
    "Confirm it worked: the OLED shows <b>SERIAL FORWARDING</b> and the button "
    "relabels to <b>&ldquo;Stop Serial Forwarding&rdquo;</b>.",
])
P("You do <b>not</b> need &ldquo;Start Searching&rdquo; or to pick a servo &mdash; "
  "the scripts address joints by ID directly. <b>Never</b> tap "
  "&ldquo;Set Middle Position&rdquo; &mdash; it rewrites a servo&rsquo;s zero.", NOTE)

# ---------- 4. Move joints a fixed angle ----------
P("4. Move joints by a fixed angle &mdash; scs_move.py", H1)
P("A safe, one-shot move: it read-checks framing (commands the joint to its "
  "current spot = no motion), does a slow 5&deg; probe, then the full angle, then "
  "returns to the start position. One joint at a time, torque stays on.", BODY)
P("Run it (example: joints 5 and 6, 20&deg;):", H2)
code("%s %s/scs_move.py --family ST --joints 5 6 --deg 20 --go" % (PY, DIR))
steps([
    "Run the command above. It opens the port (board reboots) and prints "
    "&ldquo;PORT OPEN &hellip; waiting&rdquo;.",
    "Do Section 3 (enable forwarding). Within a couple of seconds it prints "
    "&ldquo;Bridge LIVE&rdquo; and moves the joints.",
    "Watch the arm; the script prints start / probe / moved / returned angles and "
    "exits.",
])
P("Options:", H2)
bullets([
    "<b>--joints</b> &nbsp;list of servo IDs, e.g. <b>--joints 5</b> or "
    "<b>--joints 4 5 6</b>.",
    "<b>--deg</b> &nbsp;angle in degrees (default 20). It always moves "
    "<b>toward the centre</b> of travel (safest).",
    "<b>Dry run:</b> omit <b>--go</b> to print the plan and move nothing.",
])

# ---------- 5. Keep joints moving ----------
P("5. Keep the joints moving (continuous) &mdash; scs_oscillate.py", H1)
P("Sweeps each joint as a slow sine around its current position for a set time, "
  "then returns to start. Writes a timestamped log to "
  "<b>/home/user/robotic_motion/logs/</b>.", BODY)
P("Run it (example: joints 4, 5, 6 for 30 s):", H2)
code("%s %s/scs_oscillate.py --secs 30 --amp-deg 15 --freq 0.3 "
     "--joints 4 5 6 --go" % (PY, DIR))
steps([
    "Run the command; when it prints &ldquo;PORT OPEN &hellip; waiting&rdquo;, do "
    "Section 3 to enable forwarding.",
    "The joints weave for the chosen duration (each logged ~once/second: target "
    "vs actual counts), then ease back to their start positions.",
])
P("Options:", H2)
bullets([
    "<b>--secs</b> duration seconds (default 30).",
    "<b>--amp-deg</b> swing amplitude &plusmn;degrees (default 15). Keep it "
    "modest; targets are clamped to a safe count window.",
    "<b>--freq</b> oscillation frequency in Hz (default 0.3 = one full "
    "back-and-forth every ~3.3 s).",
    "<b>--joints</b> which servo IDs to move together.",
])

# ---------- 6. Logs ----------
P("6. Logs", H1)
bullets([
    "Location: <b>/home/user/robotic_motion/logs/oscillate_YYYYMMDD_HHMMSS.log</b>.",
    "Contents: run parameters, start positions, framing check, per-second "
    "target-vs-actual counts/degrees, and the final returned positions.",
    "The move script (scs_move.py) prints its results to the terminal; redirect "
    "with <b>&gt; run.log 2&gt;&amp;1</b> if you want it saved too.",
])

# ---------- 7. R_sine on hardware ----------
P("7. Running the R_sine sinusoidal motion on the real arm", H1)
P("<b>What R_sine is:</b> the simulation project (package <b>src/Rsine</b>) that "
  "solves 6-DOF inverse kinematics to trace a sine wave on a configurable plane "
  "and plays it in RViz by publishing /joint_states. On hardware we must convert "
  "those joint angles into STS3215 servo counts and stream them to the bus.", BODY)
P("<b>The one missing piece = a per-joint calibration map.</b> R_sine angles are "
  "in URDF radians; each servo has its own absolute zero and rotation direction. "
  "For every joint we need: &nbsp;count = zero_i + dir_i &times; theta_rad &times; "
  "(4096 / 2&pi;).", BODY)
P("Calibration procedure (do once):", H2)
steps([
    "Enable forwarding (Section 3).",
    "Put the arm in a known reference pose (ideally the URDF &ldquo;all-zeros&rdquo; "
    "home you use in RViz). Read all six servo counts with: "
    "&nbsp;<b>%s %s/scs_diag.py</b> &mdash; those counts are the <b>zero_i</b> for "
    "that pose." % (PY, DIR),
    "Find each joint&rsquo;s direction: nudge one joint a known +angle with "
    "scs_move.py and see whether its count went up (dir=+1) or down (dir=&minus;1). "
    "The scale is fixed at ~11.38 counts/deg.",
    "Record zero_i and dir_i for joints 1&ndash;6.",
])
P("Then stream the trajectory:", H2)
steps([
    "Generate R_sine&rsquo;s joint trajectory (its IK already precomputes the "
    "waypoint angles q for the whole sine path).",
    "Map each waypoint&rsquo;s six angles to counts with the calibration, clamp to "
    "each joint&rsquo;s safe range, and stream them over the bridge (a "
    "sync-write of all six servos per waypoint) at a steady rate matched to the "
    "servo speed limit.",
    "Start slow: run the first few waypoints, verify the tip traces the sine and "
    "no joint fights a limit, then run the full path.",
])
P("Status: the streaming script (scs_rsine.py) is <b>not built yet</b> &mdash; it "
  "needs the calibration numbers above. Once you capture zero_i / dir_i I can "
  "generate it. Caveats: this small arm has a much smaller reach than the sim, so "
  "scale the sine amplitude/width down; watch joint 1 (its bus cable has been "
  "intermittent); keep speeds low on the first runs.", NOTE)

# ---------- 8. Troubleshooting ----------
P("8. Troubleshooting", H1)
bullets([
    "<b>Script stuck on &ldquo;waiting&rdquo;:</b> forwarding isn&rsquo;t on. "
    "Reload 192.168.4.1 and tap Start Serial Forwarding. Reconnect the phone to "
    "ESP32_DEV if it dropped during the reboot.",
    "<b>A joint shows Type &minus;1 / not detected (esp. joint 1):</b> check the "
    "motor DC power and reseat that servo&rsquo;s bus cable.",
    "<b>&ldquo;could not open port / busy&rdquo;:</b> another script still holds "
    "/dev/ttyUSB0 &mdash; stop it first.",
    "<b>act=None in an oscillation log:</b> harmless read hiccup on the bus; the "
    "joint still moves (writes are separate from reads).",
    "<b>Board unreachable after many runs:</b> power-cycle the board; ESP32_DEV "
    "reappears in a few seconds.",
])

# ---------- 9. Safety ----------
P("9. Safety", H1)
bullets([
    "Keep hands and cables clear of the arm before any --go run.",
    "First run of anything new: small amplitude, low speed, one joint.",
    "Never tap &ldquo;Set Middle Position&rdquo; on the web UI (rewrites the "
    "servo zero / calibration).",
    "To stop: press Ctrl-C (scripts ease back to start), or cut the motor power "
    "supply for an immediate limp stop.",
])

# ---------- Quick reference ----------
P("Quick command reference", H1)
code([
    "# read-only check (type, IDs, positions):",
    "%s %s/scs_diag.py" % (PY, DIR),
    "",
    "# move joints a fixed angle (returns to start):",
    "%s %s/scs_move.py --family ST --joints 5 6 --deg 20 --go" % (PY, DIR),
    "",
    "# keep joints moving for 30 s:",
    "%s %s/scs_oscillate.py --secs 30 --amp-deg 15 --freq 0.3 --joints 4 5 6 --go"
    % (PY, DIR),
])

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm,
                        topMargin=16*mm, bottomMargin=16*mm,
                        title="Robotic Motion Operating Guide")
doc.build(story)
print("wrote", OUT)
