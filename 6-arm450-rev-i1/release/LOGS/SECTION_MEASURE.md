# Manual verification by slicing -- measured in each joint's section

**Total clashes: 0**

## J1 base yaw  (cut: point (np.float64(0.0), np.float64(0.0), np.float64(0.0)), normal (np.float64(0.0), np.float64(1.0), np.float64(0.0)); 10 parts in the cut)

| part A | part B | overlap mm2 | overlap thickness | gap | verdict |
|---|---|---|---|---|---|
| J2_turret_p1 | base | 0.00 | 0.000 | 0.50 | gap 0.50 |
| J2_turret_p1 | brg_J1_z3 | 0.00 | 0.000 | 0.00 | contact |
| J2_turret_p1 | brg_J1_z43 | 0.00 | 0.000 | 0.00 | contact |
| J2_turret_p1 | j1_hub | 0.00 | 0.000 | 0.12 | gap 0.12 |
| J2_turret_p1 | spigot_collar | 0.00 | 0.000 | 0.07 | gap 0.07 |
| base | brg_J1_z3 | 0.00 | 0.000 | 0.00 | contact |
| base | brg_J1_z43 | 0.00 | 0.000 | 0.00 | contact |
| base | spigot_collar | 0.00 | 0.000 | 0.50 | gap 0.50 |
| brg_J1_z3 | spigot_collar | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J1_0 | j1_hub | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J1_0 | servo_J1 | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J1_180 | j1_hub | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J1_180 | servo_J1 | 0.00 | 0.000 | 0.00 | contact |
| j1_hub | j1_mount | 0.00 | 0.000 | 0.96 | gap 0.96 |
| j1_hub | servo_J1 | 0.00 | 0.000 | 0.00 | contact |
| j1_hub | spigot_collar | 0.00 | 0.000 | 0.76 | gap 0.76 |
| j1_mount | servo_J1 | 0.00 | 0.000 | 0.00 | contact |
| j1_mount | spigot_collar | 0.00 | 0.000 | 1.31 | gap 1.31 |

## J2 shoulder  (cut: point (np.float64(0.0), np.float64(0.0), np.float64(90.0)), normal (np.float64(0.0), np.float64(0.0), np.float64(1.0)); 16 parts in the cut)

| part A | part B | overlap mm2 | overlap thickness | gap | verdict |
|---|---|---|---|---|---|
| J2_shaft | J2_turret_p1 | 0.00 | 0.000 | 0.54 | gap 0.54 |
| J2_shaft | brg_J2_drive | 0.00 | 0.000 | 0.02 | gap 0.02 |
| J2_shaft | brg_J2_idle | 0.00 | 0.000 | 0.02 | gap 0.02 |
| J2_shaft | horn_screw_J2_0 | 0.00 | 0.000 | 0.00 | contact |
| J2_shaft | horn_screw_J2_180 | 0.00 | 0.000 | 0.00 | contact |
| J2_shaft | link_set_1_270 | 0.00 | 0.000 | 0.00 | contact |
| J2_shaft | link_set_1_90 | 0.00 | 0.000 | 0.00 | contact |
| J2_shaft | link_set_2_270 | 0.00 | 0.000 | 0.00 | contact |
| J2_shaft | link_set_2_90 | 0.00 | 0.000 | 0.00 | contact |
| J2_shaft | servo_J2 | 0.00 | 0.000 | 0.00 | contact |
| J2_shaft | shaft_clamp_1 | 0.00 | 0.000 | 0.79 | gap 0.79 |
| J2_shaft | shaft_clamp_2 | 0.00 | 0.000 | 0.79 | gap 0.79 |
| J2_turret_p1 | J2_turret_p2 | 0.00 | 0.000 | 0.00 | contact |
| J2_turret_p1 | brg_J2_drive | 0.00 | 0.000 | 0.00 | contact |
| J2_turret_p1 | brg_J2_idle | 0.00 | 0.000 | 0.00 | contact |
| J2_turret_p1 | link_upper_groove | 0.00 | 0.000 | 1.00 | gap 1.00 |
| J2_turret_p1 | link_upper_tongue | 0.00 | 0.000 | 1.00 | gap 1.00 |
| J2_turret_p1 | servo_J2 | 0.00 | 0.000 | 0.00 | contact |
| J2_turret_p2 | servo_J2 | 0.00 | 0.000 | 0.40 | gap 0.40 |
| horn_screw_J2_0 | servo_J2 | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J2_180 | servo_J2 | 0.00 | 0.000 | 0.00 | contact |
| link_set_1_270 | link_upper_groove | 3.96 | 0.397 | 0.00 | thread 0.40 (M5 set screw forms its thread in the link's O4.2 hole) |
| link_set_1_270 | shaft_clamp_1 | 0.00 | 0.000 | 0.20 | gap 0.20 |
| link_set_1_90 | link_upper_groove | 3.96 | 0.397 | 0.00 | thread 0.40 (M5 set screw forms its thread in the link's O4.2 hole) |
| link_set_1_90 | shaft_clamp_1 | 0.00 | 0.000 | 0.20 | gap 0.20 |
| link_set_2_270 | link_upper_tongue | 3.96 | 0.397 | 0.00 | thread 0.40 (M5 set screw forms its thread in the link's O4.2 hole) |
| link_set_2_270 | shaft_clamp_2 | 0.00 | 0.000 | 0.20 | gap 0.20 |
| link_set_2_90 | link_upper_tongue | 3.96 | 0.397 | 0.00 | thread 0.40 (M5 set screw forms its thread in the link's O4.2 hole) |
| link_set_2_90 | shaft_clamp_2 | 0.00 | 0.000 | 0.20 | gap 0.20 |
| link_upper_groove | link_upper_tongue | 0.00 | 0.000 | 0.00 | contact |
| link_upper_groove | shaft_clamp_1 | 0.00 | 0.000 | 0.02 | gap 0.02 |
| link_upper_groove | shaft_clamp_2 | 0.00 | 0.000 | 0.74 | gap 0.74 |
| link_upper_tongue | shaft_clamp_1 | 0.00 | 0.000 | 0.50 | gap 0.50 |
| link_upper_tongue | shaft_clamp_2 | 0.00 | 0.000 | 0.02 | gap 0.02 |
| shaft_clamp_1 | shaft_clamp_2 | 0.00 | 0.000 | 1.00 | gap 1.00 |

## J3 elbow  (cut: point (np.float64(0.0), np.float64(0.0), np.float64(0.0)), normal (np.float64(1.0), np.float64(0.0), np.float64(0.0)); 30 parts in the cut)

| part A | part B | overlap mm2 | overlap thickness | gap | verdict |
|---|---|---|---|---|---|
| J3_p1 | J3_p2 | 0.00 | 0.000 | 0.00 | contact |
| J3_p1 | J3_shaft | 0.00 | 0.000 | 0.54 | gap 0.54 |
| J3_p1 | brg_J3_drive | 0.00 | 0.000 | 0.00 | contact |
| J3_p1 | brg_J3_idle | 0.00 | 0.000 | 0.00 | contact |
| J3_p1 | ear_bolt_fore | 0.00 | 0.000 | 1.20 | gap 1.20 |
| J3_p1 | link_fore_groove | 0.00 | 0.000 | 1.00 | gap 1.00 |
| J3_p1 | link_fore_tongue | 0.00 | 0.000 | 1.00 | gap 1.00 |
| J3_p1 | link_upper_tongue | 0.00 | 0.000 | 0.00 | contact |
| J3_p1 | pin_J3_fork_+1 | 0.00 | 0.000 | 0.55 | gap 0.55 |
| J3_p1 | pin_J3_fork_+1_ins | 0.00 | 0.000 | 0.00 | contact |
| J3_p1 | pin_J3_fork_-1 | 0.00 | 0.000 | 0.55 | gap 0.55 |
| J3_p1 | pin_J3_fork_-1_ins | 0.00 | 0.000 | 0.00 | contact |
| J3_p1 | servo_J3 | 0.00 | 0.000 | 0.00 | contact |
| J3_p1 | shaft_clamp_3 | 0.00 | 0.000 | 1.00 | gap 1.00 |
| J3_p1 | spring_J3_+1 | 0.00 | 0.000 | 1.51 | gap 1.51 |
| J3_p1 | spring_J3_-1 | 0.00 | 0.000 | 1.51 | gap 1.51 |
| J3_p2 | servo_J3 | 0.00 | 0.000 | 0.40 | gap 0.40 |
| J3_shaft | brg_J3_drive | 0.00 | 0.000 | 0.02 | gap 0.02 |
| J3_shaft | brg_J3_idle | 0.00 | 0.000 | 0.02 | gap 0.02 |
| J3_shaft | horn_screw_J3_0 | 0.00 | 0.000 | 0.00 | contact |
| J3_shaft | horn_screw_J3_180 | 0.00 | 0.000 | 0.00 | contact |
| J3_shaft | link_fore_groove | 0.00 | 0.000 | 1.02 | gap 1.02 |
| J3_shaft | link_fore_tongue | 0.00 | 0.000 | 1.02 | gap 1.02 |
| J3_shaft | servo_J3 | 0.00 | 0.000 | 0.00 | contact |
| J3_shaft | shaft_clamp_3 | 0.23 | 0.016 | 0.00 | fit/seat 0.016 |
| J3_shaft | shaft_clamp_4 | 0.23 | 0.016 | 0.00 | fit/seat 0.016 |
| collar_upper_+y | link_upper_tongue | 0.00 | 0.000 | 0.20 | gap 0.20 |
| collar_upper_+y | pin_J2_collar_+1 | 0.00 | 0.000 | 0.30 | gap 0.30 |
| collar_upper_+y | pin_J2_collar_+1_ins | 0.00 | 0.000 | 0.00 | contact |
| collar_upper_+y | spring_J2_+1 | 0.00 | 0.000 | 1.51 | gap 1.51 |
| collar_upper_-y | link_upper_groove | 0.00 | 0.000 | 0.20 | gap 0.20 |
| collar_upper_-y | pin_J2_collar_-1 | 0.00 | 0.000 | 0.30 | gap 0.30 |
| collar_upper_-y | pin_J2_collar_-1_ins | 0.00 | 0.000 | 0.00 | contact |
| collar_upper_-y | spring_J2_-1 | 0.00 | 0.000 | 1.51 | gap 1.51 |
| ear_bolt_fore | ear_ins_fore | 0.00 | 0.000 | 0.00 | contact |
| ear_bolt_fore | link_fore_groove | 0.00 | 0.000 | 0.50 | gap 0.50 |
| ear_bolt_fore | link_fore_tongue | 0.00 | 0.000 | 0.00 | contact |
| ear_ins_fore | link_fore_groove | 0.00 | 0.000 | 0.00 | contact |
| ear_ins_fore | link_fore_tongue | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J3_0 | servo_J3 | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J3_180 | servo_J3 | 0.00 | 0.000 | 0.00 | contact |
| link_fore_groove | link_fore_tongue | 0.00 | 0.000 | 0.00 | contact |
| link_fore_groove | shaft_clamp_3 | 0.00 | 0.000 | 0.08 | gap 0.08 |
| link_fore_groove | shaft_clamp_4 | 0.00 | 0.000 | 0.77 | gap 0.77 |
| link_fore_tongue | shaft_clamp_3 | 0.00 | 0.000 | 0.51 | gap 0.51 |
| link_fore_tongue | shaft_clamp_4 | 0.00 | 0.000 | 0.08 | gap 0.08 |
| link_upper_groove | link_upper_tongue | 0.00 | 0.000 | 0.00 | contact |
| pin_J2_collar_+1 | pin_J2_collar_+1_ins | 0.00 | 0.000 | 0.00 | contact |
| pin_J2_collar_+1 | spring_J2_+1 | 0.00 | 0.000 | 0.00 | contact |
| pin_J2_collar_-1 | pin_J2_collar_-1_ins | 0.00 | 0.000 | 0.00 | contact |
| pin_J2_collar_-1 | spring_J2_-1 | 0.00 | 0.000 | 0.00 | contact |
| pin_J3_fork_+1 | pin_J3_fork_+1_ins | 0.00 | 0.000 | 0.00 | contact |
| pin_J3_fork_+1 | spring_J3_+1 | 0.00 | 0.000 | 0.00 | contact |
| pin_J3_fork_-1 | pin_J3_fork_-1_ins | 0.00 | 0.000 | 0.00 | contact |
| pin_J3_fork_-1 | spring_J3_-1 | 0.00 | 0.000 | 0.00 | contact |
| shaft_clamp_3 | shaft_clamp_4 | 0.00 | 0.000 | 1.00 | gap 1.00 |

## J4 forearm roll  (cut: point (np.float64(0.0), np.float64(0.0), np.float64(0.0)), normal (np.float64(0.0), np.float64(1.0), np.float64(0.0)); 10 parts in the cut)

| part A | part B | overlap mm2 | overlap thickness | gap | verdict |
|---|---|---|---|---|---|
| J5_p1 | j4_hub | 0.00 | 0.000 | 0.00 | contact |
| brg_J4 | j4_cap | 0.00 | 0.000 | 0.00 | contact |
| brg_J4 | j4_hub | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J4_0 | j4_hub | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J4_0 | servo_J4 | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J4_180 | j4_hub | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J4_180 | servo_J4 | 0.00 | 0.000 | 0.00 | contact |
| j4_base | link_fore_tongue | 0.00 | 0.000 | 0.00 | contact |
| j4_base | servo_J4 | 0.00 | 0.000 | 0.00 | contact |
| j4_cap | j4_hub | 0.00 | 0.000 | 0.50 | gap 0.50 |
| j4_hub | servo_J4 | 0.00 | 0.000 | 0.00 | contact |

## J5 wrist pitch  (cut: point (np.float64(0.0), np.float64(0.0), np.float64(0.0)), normal (np.float64(1.0), np.float64(0.0), np.float64(0.0)); 13 parts in the cut)

| part A | part B | overlap mm2 | overlap thickness | gap | verdict |
|---|---|---|---|---|---|
| J5_p1 | J5_p2 | 0.00 | 0.000 | 0.00 | contact |
| J5_p1 | J5_shaft | 0.00 | 0.000 | 0.54 | gap 0.54 |
| J5_p1 | J5_spacer_B | 0.00 | 0.000 | 0.50 | gap 0.50 |
| J5_p1 | brg_J5_drive | 0.00 | 0.000 | 0.00 | contact |
| J5_p1 | brg_J5_idle | 0.00 | 0.000 | 0.00 | contact |
| J5_p1 | j4_hub | 0.00 | 0.000 | 0.00 | contact |
| J5_p1 | j6_body | 0.00 | 0.000 | 1.00 | gap 1.00 |
| J5_p1 | servo_J5 | 0.00 | 0.000 | 0.00 | contact |
| J5_p2 | servo_J5 | 0.00 | 0.000 | 0.40 | gap 0.40 |
| J5_shaft | J5_spacer_A | 0.00 | 0.000 | 0.12 | gap 0.12 |
| J5_shaft | J5_spacer_B | 0.00 | 0.000 | 0.12 | gap 0.12 |
| J5_shaft | brg_J5_drive | 0.00 | 0.000 | 0.02 | gap 0.02 |
| J5_shaft | brg_J5_idle | 0.00 | 0.000 | 0.02 | gap 0.02 |
| J5_shaft | horn_screw_J5_0 | 0.00 | 0.000 | 0.00 | contact |
| J5_shaft | horn_screw_J5_180 | 0.00 | 0.000 | 0.00 | contact |
| J5_shaft | j6_body | 0.00 | 0.000 | 0.09 | gap 0.09 |
| J5_shaft | servo_J5 | 0.00 | 0.000 | 0.00 | contact |
| J5_spacer_A | brg_J5_drive | 0.00 | 0.000 | 0.00 | contact |
| J5_spacer_A | j6_body | 0.00 | 0.000 | 0.00 | contact |
| J5_spacer_B | brg_J5_idle | 0.00 | 0.000 | 0.00 | contact |
| J5_spacer_B | j6_body | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J5_0 | servo_J5 | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J5_180 | servo_J5 | 0.00 | 0.000 | 0.00 | contact |
| j6_body | servo_J6 | 6.42 | 0.110 | 0.00 | fit/seat 0.110 |

## J6 tool roll  (cut: point (np.float64(0.0), np.float64(0.0), np.float64(0.0)), normal (np.float64(0.0), np.float64(1.0), np.float64(0.0)); 9 parts in the cut)

| part A | part B | overlap mm2 | overlap thickness | gap | verdict |
|---|---|---|---|---|---|
| J5_shaft | j6_body | 0.00 | 0.000 | 0.05 | gap 0.05 |
| brg_J6 | j6_cap | 0.00 | 0.000 | 0.00 | contact |
| brg_J6 | j6_flange | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J6_0 | j6_flange | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J6_0 | servo_J6 | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J6_180 | j6_flange | 0.00 | 0.000 | 0.00 | contact |
| horn_screw_J6_180 | servo_J6 | 0.00 | 0.000 | 0.00 | contact |
| j6_body | servo_J6 | 0.00 | 0.000 | 0.00 | contact |
| j6_cap | j6_flange | 0.00 | 0.000 | 0.50 | gap 0.50 |
| j6_flange | servo_J6 | 0.00 | 0.000 | 0.00 | contact |
