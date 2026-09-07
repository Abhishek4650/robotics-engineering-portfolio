"""Figures for the ARM-450 stress & stiffness report."""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import stress_analysis as S

INK, STEEL, GOOD, BAD, WARN, ACC = "#1b2733", "#6b7f95", "#1e7d3c", "#b03a2e", "#d09a2c", "#2e7d9a"
plt.rcParams["font.size"] = 9.5

# ===========================================================================
# FIG 1 — the compliance budget (the headline result)
# ===========================================================================
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(15, 6.2),
                              gridspec_kw=dict(width_ratios=[1.25, 1], wspace=0.28))
fig.patch.set_facecolor("white")

items = [
    ("JOINT PLAY — loose single\nthrust bearing (observed)", 28.9, BAD),
    ("Servo backlash 1.0°\n(worst case)",      9.65, BAD),
    ("Servo backlash 0.5°\n(typical)",         4.82, BAD),
    ("Servo backlash 0.3°\n(best case)",       2.89, BAD),
    ("Unbolted seam\n(torsion, t=2 PLA)",      2.80, WARN),
    ("Unbolted seam\n(torsion, t=2.4 PLA)",    1.64, WARN),
    ("Elastic droop\nPLA t=2.0",               0.258, ACC),
    ("Elastic droop\nPLA+CF t=2.4",            0.111, GOOD),
]
items.sort(key=lambda r: r[1])
y = np.arange(len(items))
ax.barh(y, [v for _, v, _ in items], color=[c for _, _, c in items],
        height=0.62, edgecolor="white")
for i, (_, v, _) in enumerate(items):
    ax.text(v * 1.06, i, f"{v:.2f} mm", va="center", fontsize=9.4, fontweight="bold")
ax.set_yticks(y)
ax.set_yticklabels([n for n, _, _ in items], fontsize=8.8)
ax.set_xscale("log")
ax.set_xlim(0.05, 120)
ax.set_xlabel("TCP position error  (mm, log scale)")
ax.set_title("A   Where the error actually comes from\n"
             "full extension, 300 g payload",
             loc="left", fontsize=12, fontweight="bold", color=INK)
ax.axvspan(2.5, 120, color=BAD, alpha=0.06)
ax.text(16, 0.15, "dominant band", fontsize=9, color=BAD,
        fontweight="bold", ha="center")
ax.grid(axis="x", alpha=0.25, ls=":")
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

# --- right: what each fix actually buys you ------------------------------
fixes = [
    ("Preloaded bearing PAIR\nspaced ≥40 mm", 28.9 - 0.36, GOOD),
    ("Bolt the seam properly\n(pitch ≤ 25 mm)", 2.80, GOOD),
    ("Halve servo backlash\n1.0° → 0.5°", 9.65 - 4.82, GOOD),
    ("PLA → PLA+CF at t=2.4", 0.221 - 0.111, ACC),
]
fixes.sort(key=lambda r: r[1])
y2 = np.arange(len(fixes))
ax2.barh(y2, [v for _, v, _ in fixes], color=[c for _, _, c in fixes],
         height=0.55, edgecolor="white")
for i, (_, v, _) in enumerate(fixes):
    ax2.text(v + 0.5, i, f"−{v:.2f} mm", va="center", fontsize=9.6, fontweight="bold")
ax2.set_yticks(y2)
ax2.set_yticklabels([n for n, _, _ in fixes], fontsize=9)
ax2.set_xlim(0, 33)
ax2.set_xlabel("TCP error removed  (mm)")
ax2.set_title("B   What each fix buys\nsorted by payoff",
              loc="left", fontsize=12, fontweight="bold", color=INK)
ax2.grid(axis="x", alpha=0.25, ls=":")
ax2.set_axisbelow(True)
for s in ("top", "right"):
    ax2.spines[s].set_visible(False)

fig.suptitle("ARM-450 — compliance budget: stiffening the shell is NOT the win",
             fontsize=14.5, fontweight="bold", color=INK, x=0.02, ha="left", y=0.99)
fig.tight_layout(rect=(0, 0, 1, 0.94))
fig.savefig("figures/an_compliance.png", dpi=200, facecolor="white")
print("wrote figures/an_compliance.png")

# ===========================================================================
# FIG 2 — stress: how enormously overbuilt the shell is
# ===========================================================================
fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.4))
fig.patch.set_facecolor("white")

ts = np.linspace(1.2, 4.0, 40)
ax = axes[0]
for mat, col in (("PLA", ACC), ("PLA+CF", GOOD), ("SLA resin", WARN)):
    vm = [S.stress_report(t, mat)["vm"] for t in ts]
    ax.plot(ts, vm, color=col, lw=2.2, label=mat)
ax.axhline(S.ALLOW_FATIGUE, color=BAD, ls="--", lw=1.6)
ax.text(3.95, S.MATS["PLA"]["Sy_z"] * 1.05, "derated allowable ~9 MPa (fatigue+temp)",
        ha="right", fontsize=8.6, color=BAD)
ax.set_yscale("log")
ax.set_ylim(0.1, 90)
ax.set_xlabel("wall thickness t  (mm)")
ax.set_ylabel("von Mises stress at the root  (MPa)")
ax.set_title("C   Stress vs the weakest direction", loc="left",
             fontsize=11.5, fontweight="bold", color=INK)
ax.legend(frameon=False, fontsize=9)
ax.grid(alpha=0.25, ls=":")

ax = axes[1]
for mat, col in (("PLA", ACC), ("PLA+CF", GOOD), ("SLA resin", WARN)):
    d = [S.structural_droop(t, mat) for t in ts]
    ax.plot(ts, d, color=col, lw=2.2, label=mat)
ax.axhline(4.82, color=BAD, ls="--", lw=1.6)
ax.text(3.95, 4.98, "servo backlash floor 4.82 mm", ha="right",
        fontsize=8.6, color=BAD)
ax.axvspan(2.0, 2.0, color=STEEL)
ax.axvline(2.0, color=STEEL, ls=":", lw=1.4)
ax.text(2.05, 1.5, "your\ncurrent\nwall", fontsize=8.4, color=STEEL)
ax.set_xlabel("wall thickness t  (mm)")
ax.set_ylabel("elastic TCP droop  (mm)")
ax.set_ylim(0, 5.6)
ax.set_title("D   Droop never reaches the backlash floor", loc="left",
             fontsize=11.5, fontweight="bold", color=INK)
ax.legend(frameon=False, fontsize=9)
ax.grid(alpha=0.25, ls=":")

ax = axes[2]
for mat, col in (("PLA", ACC), ("PLA+CF", GOOD), ("SLA resin", WARN)):
    f = [S.natural_freq(t, mat) for t in ts]
    ax.plot(ts, f, color=col, lw=2.2, label=mat)
ax.axhspan(0, 10, color=BAD, alpha=0.10)
ax.text(2.6, 5, "too floppy to control well", fontsize=8.8, color=BAD, ha="center")
ax.set_xlabel("wall thickness t  (mm)")
ax.set_ylabel("first bending mode  (Hz)")
ax.set_title("E   Resonance sets your control bandwidth", loc="left",
             fontsize=11.5, fontweight="bold", color=INK)
ax.legend(frameon=False, fontsize=9)
ax.grid(alpha=0.25, ls=":")

for a in axes:
    for s in ("top", "right"):
        a.spines[s].set_visible(False)

fig.suptitle("ARM-450 — stress, droop and dynamics vs wall thickness "
             "(145 mm links, 300 g payload)",
             fontsize=14, fontweight="bold", color=INK, x=0.02, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig("figures/an_stress.png", dpi=200, facecolor="white")
print("wrote figures/an_stress.png")

# ===========================================================================
# FIG 3 — the seam
# ===========================================================================
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(14.5, 5.6),
                              gridspec_kw=dict(width_ratios=[1, 1.05], wspace=0.24))
fig.patch.set_facecolor("white")

labels = ["bending  I\n(seam irrelevant)", "torsion  J\n(seam critical)"]
closed = [S.box_I(S.W_AXIS, S.H_BEND, 2.0), S.box_J(S.W_AXIS, S.H_BEND, 2.0)]
openv = [S.box_I(S.W_AXIS, S.H_BEND, 2.0), S.open_J(S.W_AXIS, S.H_BEND, 2.0)]
x = np.arange(2)
ax.bar(x - 0.19, closed, 0.36, label="seam bolted (closed section)", color=GOOD)
ax.bar(x + 0.19, openv, 0.36, label="seam open (two loose halves)", color=BAD)
for i in range(2):
    lbl = "no loss" if closed[i]/openv[i] < 1.05 else f"{closed[i]/openv[i]:.0f}× loss"
    ax.text(i, max(closed[i], openv[i]) * 1.7, lbl, ha="center",
            fontsize=11.5, fontweight="bold", color=GOOD if lbl=="no loss" else BAD)
ax.set_yscale("log")
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylabel("section constant  (mm⁴, log)")
ax.set_title("F   What the seam is worth\n47.5 × 29.0 shell, t = 2.0 mm",
             loc="left", fontsize=11.8, fontweight="bold", color=INK)
ax.legend(frameon=False, fontsize=9, loc="lower left")
ax.grid(axis="y", alpha=0.25, ls=":")
ax.set_axisbelow(True)

pitches = np.array([10, 15, 20, 25, 30, 40, 50, 60, 80])
q, _ = S.seam_analysis(2.0)
F = q * pitches
ax2.plot(pitches, F, "o-", color=ACC, lw=2.2, ms=6)
ax2.text(78, 10.6, "an M3 bolt shears at ~2000 N —\nstrength is NOT the limit here",
         ha="right", fontsize=9.2, color=STEEL, style="italic")
ax2.axvspan(0, 25, color=GOOD, alpha=0.13)
ax2.axvline(25, color=GOOD, lw=1.8, ls="--")
ax2.text(24, 8.4, "recommended\npitch ≤ 25 mm\n(stiffness, not strength)",
         ha="right", fontsize=9.2, color=GOOD, fontweight="bold")
ax2.set_xlabel("fastener pitch along the seam  (mm)")
ax2.set_ylabel("shear force per fastener  (N)")
ax2.set_ylim(0, 12)
ax2.set_title(f"G   Seam torsional shear flow q = {q:.2f} N/mm\n"
              "every pitch passes on strength — pitch is set by SLIP",
              loc="left", fontsize=11.8, fontweight="bold", color=INK)
ax2.grid(alpha=0.25, ls=":")
ax2.set_axisbelow(True)

for a in (ax, ax2):
    for s in ("top", "right"):
        a.spines[s].set_visible(False)

fig.suptitle("ARM-450 — the bolted seam is the one structural change that matters",
             fontsize=14, fontweight="bold", color=INK, x=0.02, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.92))
fig.savefig("figures/an_seam.png", dpi=200, facecolor="white")
print("wrote figures/an_seam.png")
