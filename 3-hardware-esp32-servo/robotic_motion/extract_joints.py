#!/usr/bin/env python3
"""Extract the 6 joint centres from the assembled mesh by clustering the
JOINT-indicating bodies (servos, motor-mounts, bearings, joint housings) and
report inter-joint distances = link lengths. Link-cover bodies are excluded so
clusters localise on the joints, not link middles.

These centres are geometrically reliable (~mm); axis DIRECTIONS still need a
ground-truth anchor, so this is the measured skeleton, not a certified DH."""
import numpy as np, trimesh
from scipy.cluster.vq import kmeans2

ASM = "/home/user/Desktop/Robotic_arm_design/Robo_2_assembled.stl"
LIB = {  # name -> sorted dims ; role
 "servo": ((24.7,37.8,45.2), "joint"), "mount_J1": ((24.,40.,40.), "joint"),
 "mount_wrist": ((23.,40.,40.), "joint"), "mount_J2": ((38.2,46.,46.), "joint"),
 "mount_base": ((33.,46.,46.), "joint"), "bearing": ((3.7,42.,42.), "joint"),
 "J2_p1": ((64.8,80.,85.5), "joint"), "J4_p1": ((57.,63.8,79.8), "joint"),
 "wrist_p1": ((58.2,62.7,72.2), "joint"),
 "link": ((29.,47.5,147.5), "link"), "base_p1": ((43.,56.,72.9), "link"),
}
def role(size):
    s=np.sort(size); best,bd,ro="?",1e9,"?"
    for n,(d,r) in LIB.items():
        e=np.abs(s-np.array(d)).sum()
        if e<bd: bd,best,ro=e,n,r
    return (best,ro) if bd<20 else ("?","link")

m=trimesh.load(ASM, process=True)
parts=[p for p in m.split(only_watertight=False) if max(p.extents)>20 and len(p.faces)>200]
J=[]  # joint-body centroids (weighted by faces)
for p in parts:
    name,ro=role(p.extents)
    if ro=="joint":
        J.append((p.bounds.mean(0), len(p.faces), name))
pts=np.array([c for c,_,_ in J]); w=np.array([f for _,f,_ in J],float)

# seed 6 clusters near the visually-identified joint regions
seeds=np.array([[-8,0,40],[-8,0,110],[50,-195,114],[24,-160,150],
                [34,-123,178],[85,-80,178]],float)
cen,lab=kmeans2(pts, seeds, minit="matrix", iter=50)
# weighted recompute of centres
order=[]
for k in range(6):
    msk=lab==k
    if msk.sum():
        cen[k]=np.average(pts[msk],axis=0,weights=w[msk])
        order.append((k,msk.sum()))
print("Joint centres (mm) and link lengths from mesh:")
names=["J1 base","J2 shoulder","J3 elbow","J4","J5 wrist","J6 end"]
prev=None
for k in range(6):
    c=cen[k]
    d=f"   link to prev = {np.linalg.norm(c-prev):6.1f} mm" if prev is not None else ""
    nb=(lab==k).sum()
    print(f"  {names[k]:12s} ({c[0]:7.1f},{c[1]:7.1f},{c[2]:7.1f})  [{nb} bodies]{d}")
    prev=c
tot=sum(np.linalg.norm(cen[i+1]-cen[i]) for i in range(5))
print(f"  total base->tip chain length = {tot:.1f} mm  "
      f"(straightened reach approx, folded pose)")
