"""Render ARM-450 equations in the user's own notation.

pandoc -> OMML turns left-prescripts like {}^{i-1}_{i}T into empty boxes and
cannot be fixed. matplotlib mathtext handles prescripts, but NOT \begin{array},
so matrices use the custom bracket drawer from the thesis book toolchain.
"""
import os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

EQ = "figures/eq"
os.makedirs(EQ, exist_ok=True)


def eq(name, latex, fontsize=24):
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0.5, 0.5, f"${latex}$", fontsize=fontsize, ha="center", va="center")
    fig.savefig(os.path.join(EQ, name + ".png"), dpi=200, bbox_inches="tight",
                pad_inches=0.08, facecolor="white")
    plt.close(fig)


def matrix_eq(name, lhs, rows, fontsize=19, col_w=2.8, lhs_w=3.0):
    nr, nc = len(rows), len(rows[0])
    D, row_h, gap = 0.55, 1.0, 0.7
    mat_w = nc * col_w
    W = lhs_w + gap + mat_w + 1.0
    H = nr * row_h + 1.0
    fig = plt.figure(figsize=(W * D, H * D)); fig.patch.set_facecolor("white")
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.set_xlim(0, W); ax.set_ylim(0, H)
    ycen = H / 2.0
    ax.text(0.15, ycen, rf"${lhs} =$", fontsize=fontsize, ha="left", va="center")
    mat_left = lhs_w + gap
    xs = [mat_left + col_w * (c + 0.5) for c in range(nc)]
    ys = [ycen + ((nr - 1) / 2.0 - i) * row_h for i in range(nr)]
    for i, row in enumerate(rows):
        for c, cell in enumerate(row):
            ax.text(xs[c], ys[i], rf"${cell}$", fontsize=fontsize, ha="center", va="center")
    top, bot = ycen + nr * row_h / 2.0, ycen - nr * row_h / 2.0
    xl, xr = mat_left, mat_left + mat_w
    for xb, sgn in ((xl, 1), (xr, -1)):
        ax.plot([xb, xb], [bot, top], color="k", lw=1.8)
        ax.plot([xb, xb + sgn * 0.22], [top, top], color="k", lw=1.8)
        ax.plot([xb, xb + sgn * 0.22], [bot, bot], color="k", lw=1.8)
    fig.savefig(os.path.join(EQ, name + ".png"), dpi=200, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    matrix_eq("dh_transform", r"^{i-1}_{\ i}T", [
        [r"c\theta_i", r"-s\theta_i", r"0", r"a_{i-1}"],
        [r"s\theta_i c\alpha_{i-1}", r"c\theta_i c\alpha_{i-1}",
         r"-s\alpha_{i-1}", r"-s\alpha_{i-1} d_i"],
        [r"s\theta_i s\alpha_{i-1}", r"c\theta_i s\alpha_{i-1}",
         r"c\alpha_{i-1}", r"c\alpha_{i-1} d_i"],
        [r"0", r"0", r"0", r"1"]], col_w=3.4, lhs_w=2.2)

    eq("fk", r"^{0}_{6}T(q)=\ ^{0}_{1}T\ ^{1}_{2}T\ ^{2}_{3}T\ ^{3}_{4}T\ ^{4}_{5}T\ ^{5}_{6}T")
    eq("fk_tcp", r"^{0}_{TCP}T=\ ^{0}_{6}T\cdot Trans_z(d_{tool}),\qquad d_{tool}=60\ mm")
    eq("omega", r"^{i+1}\omega_{i+1}=\ ^{i+1}_{\ i}R\ ^{i}\omega_i"
                r"+\dot\theta_{i+1}\ ^{i+1}\hat{Z}_{i+1}")
    eq("vel", r"^{i+1}v_{i+1}=\ ^{i+1}_{\ i}R\left(^{i}v_i"
              r"+\ ^{i}\omega_i\times\ ^{i}P_{i+1}\right)+\dot d_{i+1}\ ^{i+1}\hat{Z}_{i+1}")
    matrix_eq("jac_col", r"J_i", [[r"\hat Z_i\times(P_{tcp}-P_i)"], [r"\hat Z_i"]],
              col_w=6.4, lhs_w=1.4)
    eq("reach", r"R_{max}=a_2+d_4+d_{tool}=119+181+60=360\ mm")
    eq("deadzone", r"r_{inner}=\max\left(0,\ |a_2-d_4|-d_{tool}\right)"
                   r"=\max(0,\ 62-60)=2\ mm\ \rightarrow\ measured\ 0.3\ mm")
    print("  wrote", len(os.listdir(EQ)), "equation images to", EQ)
