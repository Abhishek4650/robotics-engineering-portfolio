import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import precision as P

INK,STEEL,GOOD,BAD,WARN,ACC="#1b2733","#6b7f95","#1e7d3c","#b03a2e","#d09a2c","#2e7d9a"
b=P.budget(); acc,rep,uni=P.repeatability_vs_accuracy(); paths=P.improvement_paths()

fig=plt.figure(figsize=(16.5,9.4)); fig.patch.set_facecolor("white")
gs=fig.add_gridspec(2,2,height_ratios=[1,1],width_ratios=[1.15,1],hspace=.34,wspace=.22,
                    left=.19,right=.985,top=.90,bottom=.07)

# A: budget
ax=fig.add_subplot(gs[0,0])
items=sorted(((n,np.sqrt((e**2).mean())*1000,s) for n,(e,s) in b.items()),key=lambda r:r[1])
y=np.arange(len(items))
cols=[BAD if "ASSUMED" in s else (WARN if "CALCULATED" in s else GOOD) for _,_,s in items]
ax.barh(y,[v for _,v,_ in items],color=cols,height=.62,edgecolor="white")
for i,(_,v,_) in enumerate(items): ax.text(v*1.05,i,f"{v:.3f}",va="center",fontsize=9.5,fontweight="bold")
ax.set_yticks(y); ax.set_yticklabels([n for n,_,_ in items],fontsize=9.5)
ax.set_xscale("log"); ax.set_xlim(0.002,4)
ax.set_xlabel("RMS contribution to TCP error (mm, log)")
ax.set_title("A   Error budget — red = ASSUMED, amber = calculated, green = measured",
             loc="left",fontsize=11.8,fontweight="bold",color=INK)
ax.grid(axis="x",alpha=.25,ls=":"); ax.set_axisbelow(True)
for s in("top","right"): ax.spines[s].set_visible(False)

# B: accuracy vs repeatability
ax=fig.add_subplot(gs[0,1])
data=[("absolute\naccuracy",acc,ACC),("repeatability\nDIRECTION REVERSED",rep,BAD),
      ("repeatability\nSAME approach",uni,GOOD)]
for i,(l,e,c) in enumerate(data):
    ax.bar(i,np.sqrt((e**2).mean()),color=c,width=.6)
    ax.errorbar(i,np.sqrt((e**2).mean()),yerr=[[0],[np.percentile(e,95)-np.sqrt((e**2).mean())]],
                color=INK,capsize=6,lw=1.4)
    ax.text(i,np.percentile(e,95)*1.04,f"{np.sqrt((e**2).mean()):.2f}",ha="center",
            fontsize=11,fontweight="bold")
ax.set_xticks(range(3)); ax.set_xticklabels([l for l,_,_ in data],fontsize=9.5)
ax.set_ylabel("TCP error (mm)   bar = RMS, whisker = 95 %")
ax.set_title("B   Backlash is a dead zone, not noise",loc="left",
             fontsize=11.8,fontweight="bold",color=INK)
ax.grid(axis="y",alpha=.25,ls=":"); ax.set_axisbelow(True)
for s in("top","right"): ax.spines[s].set_visible(False)

# C: improvement paths
ax=fig.add_subplot(gs[1,:])
ks=list(paths.keys()); v=[np.sqrt((paths[k]**2).mean()) for k in ks]
cols=[BAD,WARN,WARN,GOOD,GOOD]
ax.barh(np.arange(len(ks)),v,color=cols,height=.6,edgecolor="white")
for i,x in enumerate(v):
    ax.text(x*1.04,i,f"{x:.3f} mm",va="center",fontsize=10.5,fontweight="bold")
ax.set_yticks(np.arange(len(ks))); ax.set_yticklabels(ks,fontsize=10)
ax.set_xscale("log"); ax.set_xlim(0.05,3)
ax.set_xlabel("RMS TCP error (mm, log scale)")
ax.set_title("C   What actually buys precision — only encoders change the order of magnitude",
             loc="left",fontsize=11.8,fontweight="bold",color=INK)
ax.grid(axis="x",alpha=.25,ls=":"); ax.set_axisbelow(True)
for s in("top","right"): ax.spines[s].set_visible(False)
ax.invert_yaxis()

fig.suptitle("ARM-450 — precision budget, Monte-Carlo through the Jacobian over the drawing band",
             fontsize=15,fontweight="bold",color=INK,x=.02,ha="left",y=.965)
fig.savefig("figures/precision.png",dpi=185,facecolor="white")
print("wrote figures/precision.png")
