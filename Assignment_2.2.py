import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from pyXSteam.XSteam import XSteam #Importing Python Steam Table Library.

# Initialize Steam Tables
# Note: Ensure 'pyXSteam' is installed via pip
steam_table = XSteam(XSteam.UNIT_SYSTEM_BARE) # m/kg/sec/K/MPa/W

st.set_page_config(page_title="Steam Process Analyzer", layout="wide")

## Navigation Configuration
st.sidebar.header("Initial State (Point 1)")
p1 = st.sidebar.number_input("Initial Pressure P1 (bar)", value=10.0)
t1_c = st.sidebar.number_input("Initial Temperature T1 (°C)", value=250.0)
m = st.sidebar.number_input("Mass m (kg)", value=1.0)

st.sidebar.header("Process Selection")
process = st.sidebar.selectbox("Select Process", 
    ["Constant Volume", "Constant Pressure", "Isothermal", "Adiabatic", "Polytropic"])

st.sidebar.header("Final State (Point 2)")
p2 = st.sidebar.number_input("Final Pressure P2 (bar)", value=3.5)

# Calculate State 1 Properties
# Convert bar to bar for the library if needed (usually 1 bar = 0.1 MPa in some versions)
# Here we assume the library handles bar directly as per setup
u1 = steam_table.u_pt(p1, t1_c)
s1 = steam_table.s_pt(p1, t1_c)
v1_spec = steam_table.v_pt(p1, t1_c)
v1 = v1_spec * m

# Process Logic
t2_c, u2, s2, v2 = 0, 0, 0, 0
work, heat = 0, 0

if process == "Constant Volume":
    v2 = v1
    v2_spec = v1 / m
    vf = steam_table.vL_p(p2)
    vg = steam_table.vV_p(p2)
    x2 = (v2_spec - vf) / (vg - vf)
    x2 = max(0, min(1, x2))
    
    sf, sg = steam_table.sL_p(p2), steam_table.sV_p(p2)
    s2 = sf + x2 * (sg - sf)
    uf, ug = steam_table.uL_p(p2), steam_table.uV_p(p2)
    u2 = uf + x2 * (ug - uf)
    try:
        t2_c = steam_table.tsat_p(p2)
    except:
        t2_c = steam_table.t_ps(p2, s2)
    
    work = 0
    heat = m * (u2 - u1)

elif process == "Constant Pressure":
    p2 = p1
    # For a given P, usually T2 or V2 is needed. Let's assume cooling to a specific T
    t2_c = st.sidebar.number_input("Final Temperature T2 (°C)", value=150.0)
    v2_spec = steam_table.v_pt(p2, t2_c)
    v2 = v2_spec * m
    u2 = steam_table.u_pt(p2, t2_c)
    s2 = steam_table.s_pt(p2, t2_c)
    
    work = p1 * 100 * (v2 - v1) # bar to kPa
    heat = m * (steam_table.h_pt(p2, t2_c) - steam_table.h_pt(p1, t1_c))

elif process == "Isothermal":
    t2_c = t1_c
    u2 = steam_table.u_pt(p2, t2_c)
    s2 = steam_table.s_pt(p2, t2_c)
    v2 = steam_table.v_pt(p2, t2_c) * m
    heat = m * (t2_c + 273.15) * (s2 - s1)
    work = heat - m * (u2 - u1)

elif process == "Adiabatic":
    s2 = s1
    t2_c = steam_table.t_ps(p2, s2)
    u2 = steam_table.u_ps(p2, s2)
    v2 = steam_table.v_ps(p2, s2) * m
    heat = 0
    work = m * (u1 - u2)

elif process == "Polytropic":
    n = 1.25
    v2_spec = (v1/m) * (p1/p2)**(1/n)
    v2 = v2_spec * m
    # Simplified lookup for T and U via v and p
    s2 = steam_table.s_Vp(v2_spec, p2)
    u2 = steam_table.u_ps(p2, s2)
    t2_c = steam_table.t_ps(p2, s2)
    work = (p1 * 100 * v1 - p2 * 100 * v2) / (n - 1)
    heat = m * (u2 - u1) + work

## UI Layout
st.title(f"🚀 Steam Analysis: {process}")
col1, col2 = st.columns(2)

with col1:
    st.metric("Work Done (W)", f"{work:.2f} kJ")
    st.metric("Heat Transfer (Q)", f"{heat:.2f} kJ")

with col2:
    st.metric("Final Temp (T2)", f"{t2_c:.2f} °C")
    st.metric("Final Volume (V2)", f"{v2:.4f} m³")

## Plotting
fig, (ax_pv, ax_ts) = plt.subplots(1, 2, figsize=(12, 5))

# PV Plot
ax_pv.plot([v1, v2], [p1, p2], 'ro-')
ax_pv.set_xlabel("Volume (m³)")
ax_pv.set_ylabel("Pressure (bar)")
ax_pv.set_title("P-V Diagram")
ax_pv.grid(True)

# TS Plot with Saturation Curve
p_range = np.linspace(0.01, 220, 100)
try:
    temp_sat = [steam_table.tsat_p(p) + 273.15 for p in p_range]
except:
    temp_sat = [steam_table.tSat_p(p) + 273.15 for p in p_range]
sf = [steam_table.sL_p(p) for p in p_range]
sg = [steam_table.sV_p(p) for p in p_range]

ax_ts.plot(sf, temp_sat, 'k--', alpha=0.5)
ax_ts.plot(sg, temp_sat, 'k--', alpha=0.5)
ax_ts.plot([s1, s2], [t1_c + 273.15, t2_c + 273.15], 'ro-')
ax_ts.set_xlabel("Entropy (kJ/kg·K)")
ax_ts.set_ylabel("Temperature (K)")
ax_ts.set_title("T-s Diagram")
ax_ts.grid(True)

st.pyplot(fig)