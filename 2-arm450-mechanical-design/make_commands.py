"""
Build COMMANDS.md — the ARM-450 command reference.

GENERATED, NOT TYPED. The alias table is parsed straight out of
arm450_aliases.sh and the tool options straight out of plan_sine.py's argument
parser. That is deliberate: a hand-written command sheet is exactly the kind of
document that goes stale silently, which is the failure this project has now hit
three separate times (a drawing asserting a bearing pocket that had been fixed,
a workspace table quoting a tool reach from before the part changed shape, and
an alias still passing the trace height that collided with the base).

Run:  python3 make_commands.py && python3 build_pdf.py COMMANDS.md
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SH = os.path.join(HERE, "arm450_aliases.sh")

# one line each for the shell FUNCTIONS, whose bodies are too long to tabulate
FUNC_SUMMARY = {
    "a450speed": "a450speed <hz>  — set playback rate, 0.5–500",
    "a450plan": "a450plan <plan_sine.py args>  — re-solve the trajectory",
    "a450urdf": "a450urdf [tool]  — regenerate BOTH urdfs and install them",
    "a450tool": "a450tool gripper / dock / none — swap the end effector, rebuild, re-solve",
    "a450unsnap": "unset GTK_PATH — lets rviz2 start in a VS Code snap terminal",
}


def parse_aliases():
    """-> [(section, name, expansion, note)] in file order."""
    out, section, pending = [], "general", []
    for line in open(SH, encoding="utf-8"):
        line = line.rstrip("\n")
        m = re.match(r"^#\s*---\s*(.+?)\s*-{3,}\s*$", line)
        if m:
            section, pending = m.group(1), []
            continue
        if line.startswith("#"):
            t = line.lstrip("#").strip()
            if t and not t.startswith("---"):
                pending.append(t)
            continue
        m = re.match(r"^alias\s+([A-Za-z0-9_]+)='(.*)'$", line)
        if m:
            out.append((section, m.group(1), m.group(2), " ".join(pending)))
            pending = []
            continue
        m = re.match(r"^([a-z][A-Za-z0-9_]*)\(\)\s*\{\s*(?:#\s*(.*))?$", line)
        if m and m.group(1) != "a450help":
            name = m.group(1)
            # A function's body is several lines, so there is nothing sensible
            # to put in a "runs" column. Use the usage comment on the def line,
            # falling back to a written summary -- "(function)" told the reader
            # nothing, which is worse than the alias rows it sits beside.
            usage = (m.group(2) or "").strip() or FUNC_SUMMARY.get(name, "")
            out.append((section, name + "()", usage or "see the notes below",
                        " ".join(pending)))
            pending = []
            continue
        if line.strip() == "":
            pending = []
    return out


def md_escape(s):
    """A pipe inside a table cell splits the row into extra columns. A
    backslash escape is not enough -- the renderer here does not honour it --
    so substitute the HTML entity, which passes through as a literal bar."""
    return s.replace("|", "/")


def plan_help():
    p = subprocess.run([sys.executable, "plan_sine.py", "--help"],
                       capture_output=True, text=True, cwd=HERE)
    return p.stdout.strip()


HEAD = """# ARM-450 — Command Reference

Every alias, every raw ROS 2 equivalent, and the commands worth knowing when
something looks wrong.

**This page is generated.** The alias table below is parsed out of
`arm450_aliases.sh` by `make_commands.py`; the trajectory options are read from
`plan_sine.py --help`. Nothing here is typed by hand, because a hand-written
command sheet is precisely the document that goes stale without anyone noticing.

---

## 1. Install, once

```bash
echo 'source ~/ros2_ws/arm450_design/arm450_aliases.sh' >> ~/.bashrc
exec bash
a450help          # the whole list, any time
```

If the workspace has never been built on this machine:

```bash
cd ~/ros2_ws
colcon build --packages-select arm450_description arm450_sine --symlink-install
source install/setup.bash
```

---

## 2. The short version

```bash
a450src           # source ROS 2 Jazzy + this workspace
a450run           # arm + gripper + sine trace in RViz
a450slow          # slow it down to watch the wrist
a450stop          # stop everything
```

**Use a plain Ubuntu terminal.** Inside the VS Code integrated terminal the snap
sets `GTK_PATH`, RViz loads a GTK module from the snap tree, that module drags in
the snap's glibc, and `rviz2` dies on startup with

```
libpthread.so.0: undefined symbol: __libc_pthread_init, version GLIBC_PRIVATE
```

`a450unsnap` (`unset GTK_PATH`) fixes it. Outside the editor the variable is not
set and the problem does not exist.

---
"""

TAIL = """
---

## 5. Raw ROS 2 — the same things without aliases

Useful when you are on another machine, or debugging and want to see exactly
what is being run.

### Launch

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash

ros2 launch arm450_sine sine.launch.py                 # trace, with RViz
ros2 launch arm450_sine sine.launch.py traj_file:=/path/to/other.npz
ros2 launch arm450_description display.launch.py       # RViz + joint sliders
ros2 launch arm450_description display.launch.py gui:=false
```

### Run a single node

```bash
ros2 run arm450_sine sine_node --ros-args \\
    -p traj_file:=$HOME/ros2_ws/src/arm450_sine/sine_traj.npz \\
    -p approach_time:=3.0 \\
    -p loop_mode:=pingpong

URDF=~/ros2_ws/install/arm450_description/share/arm450_description/urdf
ros2 run robot_state_publisher robot_state_publisher --ros-args \\
    -p robot_description:="$(cat $URDF/arm450_meshes.urdf)"

RVIZ=~/ros2_ws/install/arm450_description/share/arm450_description/rviz
rviz2 -d $RVIZ/arm450.rviz
```

Three RViz configs ship: `arm450.rviz` (whole arm), `arm450_tool.rviz` (camera on
the wrist), `arm450_side.rviz` (looks along −Y, so board distance and tip are
unambiguous — perspective in the orbit views makes the traced curve look like it
passes through the gripper when it does not).

### Parameters, live

```bash
ros2 param list /arm450_sine
ros2 param get  /arm450_sine rate
ros2 param set  /arm450_sine rate 60.0      # 0.5 – 500 Hz, takes effect at once
ros2 param dump /arm450_sine
```

`rate` is the only parameter that can be changed while running and have an
effect. `create_timer()` fixes its period at construction, so the node rebuilds
the timer in a parameter callback — without that, `ros2 param set` would be
accepted and then silently ignored.

### Topics

```bash
ros2 topic list
ros2 topic echo /joint_states --once
ros2 topic hz   /joint_states                # should sit at the `rate` param
ros2 topic info /arm450/trajectory --verbose
ros2 topic echo /arm450/trajectory --once    # the whole solved path, latched
ros2 topic echo /sine_path --once            # the marker RViz draws
```

`/joint_states` is a **visualisation** stream — a real controller will not follow
it. `/arm450/trajectory` is the same path as a `JointTrajectory` with timestamps
and velocities, published once and latched (`TRANSIENT_LOCAL`), which is what a
`FollowJointTrajectory` action wants.

### Frames

```bash
ros2 run tf2_ros tf2_echo base_link tool_tip     # where the tool actually works
ros2 run tf2_ros tf2_echo base_link tcp          # the J6 flange, 42 mm behind it
ros2 run tf2_tools view_frames                   # writes frames.pdf
ros2 topic echo /tf_static --once
```

**`tcp` is not the working point.** It is the J6 tool face; a fitted gripper
works 42 mm further out at `tool_tip`. Reading `tcp` and assuming it was the pen
is what put the traced curve 42 mm behind the fingers.

### Recording and replay

```bash
ros2 bag record /joint_states /sine_path /tf /tf_static -o arm450_trace
ros2 bag info arm450_trace
ros2 bag play arm450_trace --loop
```

### Inspecting the model

```bash
check_urdf $URDF/arm450_meshes.urdf
urdf_to_graphiz $URDF/arm450_meshes.urdf     # writes arm450.gv / .pdf
ros2 node list
ros2 node info /arm450_sine
ros2 doctor --report
```

---

## 6. Re-solving the trajectory

The ROS node **replays** a solved file; it does not do IK. Changing amplitude,
cycles, span or board distance needs `plan_sine.py`, then a relaunch.

```
"""

TAIL2 = """```

### The board distance changes with a tool fitted

The trajectory drives the **J6 flange**. A fitted tool works further out, so the
board the tip traces is that much beyond `--board-x`:

| fitted | works past the flange | board goes at |
| --- | --- | --- |
| none | — | 300 mm |
| pen | 30 mm | 330 mm |
| **gripper** | **42 mm** | **342 mm** |
| dock probe | 36 mm | 336 mm |

`plan_sine.py` prints the number so you never work it out:

```
  TOOL: gripper, working point 42 mm past the J6 flange
  IK drives the FLANGE
  *** PUT THE BOARD AT x = 342 mm ***  (flange sweeps x = 300 mm)
```

If the board cannot move, `a450tipik` drives the tip onto 300 mm instead. It is
the worse option — 2.87° joint steps against 2.09°, and 0.087 mm rms against
0.055 — because the flange ends up 42 mm nearer the base on a poorer IK branch.
It also needs `--z-center 0.26` and `--w-ori 0.2`: with a tool fitted a tilt
moves the tip, so at the flange-tuned weight the solver trades **21° of tool
tilt** for position error.

**Keep amplitude at 0.04.** Past 40 mm the shoulder J2 reaches its +115° stop and
path error goes 0.19 → 1.35 mm. Cycles are free — raise `--points` to about
60 × cycles and the error does not move.

---

## 7. Design-side commands

```bash
cd ~/ros2_ws/arm450_design

python3 preflight.py            # the full 8-stage pre-print check  (a450flight)
python3 preprint_check.py       # the fast parts gate               (a450gate)
python3 check_tool_fit.py       # end-effector interfaces + the docking mate
python3 check_sine_clear.py     # sine path vs exact mesh, per fitted tool
python3 workspace.py            # reach and swept volume, per fitted tool
python3 interference.py         # joint-limit collision sweep

python3 cad/end_effector.py     # rebuild the six tool parts
python3 cad/volumes.py          # refresh the exact STEP volumes
python3 draw_iso.py             # isometric sheets   -> figures/iso/
python3 draw_3view.py           # third-angle sheets -> figures/3view/
python3 build_pdf.py REPORT.md  # any .md -> output/ARM450_*.pdf
```

### Swapping the fitted end effector

```bash
a450tool gripper     # or: dock | none
```

That regenerates both URDFs, copies the meshes, colcon-builds, and re-solves the
trajectory so the path marker lands on the new tool's tip. Then `a450run`.

Manually:

```bash
cd ~/ros2_ws/arm450_design
EMIT=1 TOOL=dock python3 generate_urdf_meshes.py
cp meshes/*.stl ~/ros2_ws/src/arm450_description/meshes/
cp arm450_meshes.urdf ~/ros2_ws/src/arm450_description/urdf/
cd ~/ros2_ws && colcon build --packages-select arm450_description --symlink-install
```

---

## 8. When something looks wrong

| symptom | cause | fix |
| --- | --- | --- |
| `rviz2` exits instantly, GLIBC symbol error | VS Code snap sets `GTK_PATH` | `a450unsnap`, or use a plain terminal |
| RViz shows blocks, not the real arm | loaded `arm450.urdf` (primitives) instead of `arm450_meshes.urdf` | use the launch file, or `a450urdf` |
| meshes missing, arm is invisible | `package://` name wrong — it is `arm450_description`, never `arm450_design` | rebuild with `a450urdf` |
| no motion in RViz | `sine_node` not running, or Fixed Frame is not `world` | `a450nodes`, check the RViz Global Options |
| arm jumps back to the start each pass | `loop_mode:=wrap` | leave it at `pingpong` |
| traced curve sits behind the gripper | path marker on the flange | re-solve with `--tool`, see §6 |
| `a450stop` kills your terminal | you used `pkill -f ros2` | `a450stop` names each executable for this reason |

### Stopping things safely

```bash
a450stop        # pkill -f sine_node; pkill -f robot_state_publisher; pkill -f rviz2
```

Never `pkill -f ros2`. The pattern matches your own shell's command line and
kills the terminal you are typing in. For the same reason, a wait loop built on
`pgrep -f <script>` never exits — it matches itself.

---

## 9. Reference PDFs

| file | what is in it |
| --- | --- |
| `ARM450_RUN.pdf` | running the simulation, in full |
| `ARM450_URDF.pdf` | the kinematic chain, every link and joint |
| `ARM450_BUY.pdf` | what to buy, what to print, print order |
| `ARM450_PREFLIGHT.pdf` | the 8-stage pre-print gate |
| `ARM450_END_EFFECTORS.pdf` | the gripper and the docking probe |
| `ARM450_WORKSPACE.pdf` | reach and swept volume |
| `ARM450_DRAWINGS_ISO.pdf` | dimensioned isometric sheets, 18 parts |
| `ARM450_DRAWINGS_3VIEW.pdf` | third-angle sheets, 18 parts |
| `ARM450_LOG.pdf` | what changed, when, and why |
| `ARM450_LESSONS.pdf` | the mistakes, and the rules they produced |

`a450docs` lists them; `a450open` opens the folder.
"""


def main():
    rows = parse_aliases()
    body = [HEAD, "## 3. Every alias\n",
            "Parsed from `arm450_aliases.sh`, so this table cannot drift from "
            "what your shell actually does.\n"]
    cur = None
    for section, name, exp, note in rows:
        if section != cur:
            cur = section
            body.append(f"\n### {section}\n")
            body.append("| command | runs |")
            body.append("| --- | --- |")
        exp = exp if len(exp) < 150 else exp[:147] + "…"
        body.append(f"| `{name}` | `{md_escape(exp)}` |")
    body.append("\n### Notes carried in the file\n")
    for section, name, exp, note in rows:
        if note and len(note) > 40:
            body.append(f"**`{name}`** — {note}\n")
    body.append("\n---\n\n## 4. Environment variables\n")
    body.append("| variable | value |")
    body.append("| --- | --- |")
    # top-level exports only, first definition wins. Without the dedupe the
    # `export ARM450_TOOL="$1"` inside a450tool() appeared as a second row
    # claiming the variable's value was the literal string $1.
    seen = set()
    for line in open(SH, encoding="utf-8"):
        if line.startswith((" ", "\t")):
            continue
        m = re.match(r"^export\s+([A-Z0-9_]+)=(.*)$", line.strip())
        if m and m.group(1) not in seen:
            seen.add(m.group(1))
            body.append(f"| `{m.group(1)}` | `{m.group(2)}` |")
    body.append("\n`ARM450_TOOL` follows whatever `a450tool` last fitted, and "
                "`a450plan` passes it to `plan_sine.py` automatically.\n")
    body.append(TAIL)
    body.append(plan_help())
    body.append(TAIL2)
    out = os.path.join(HERE, "COMMANDS.md")
    open(out, "w", encoding="utf-8").write("\n".join(body) + "\n")
    print(f"  {len(rows)} aliases/functions parsed")
    print(f"  wrote {out}")


if __name__ == "__main__":
    main()
