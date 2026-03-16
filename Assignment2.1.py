import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

#APP CONFIGURATION
st.set_page_config(page_title="ThermoViz: Non-Flow Processes", layout="wide")
st.title("Non-Flow Process Front End Visualizer")

#NAVIGATION
with st.sidebar:
    st.header("1. Selection")
    process = st.selectbox("Select Process", [
        "Constant Volume", 
        "Constant Pressure", 
        "Polytropic", 
        "Adiabatic", 
        "Isothermal"
    ])
    
    fluid = st.selectbox("Working Fluid", ["Air", "Methane"])
    
    st.header("2. Initial State (1)")
    p1 = st.number_input("Pressure P1 (bar)", value=10.0)
    t1_c = st.number_input("Temperature T1 (°C)", value=250.0)
    m = st.number_input("Mass (kg)", value=1.0)
    
    st.header("3. Process Target (2)")
    if process == "Constant Pressure":
        v_ratio = st.slider("Volume Expansion Ratio (V2/V1)", 1.1, 3.0, 2.0)
    elif process == "Isothermal":
        v2_spec = st.number_input("Final Specific Volume (m³/kg)", value=0.28)
    else:
        p2 = st.number_input("Final Pressure P2 (bar)", value=3.5)

    #Polytropic Index (n)
    n = 1.25 if process == "Polytropic" else 1.0

#FLUID PROPERTIES
# Constants: R (kJ/kgK), Cv (kJ/kgK), Cp (kJ/kgK), Gamma y
if fluid == "Air":
    r, cv, cp = 0.287, 0.718, 1.005
else: # Methane
    r, cv, cp = 0.518, 1.735, 2.253
gamma = cp / cv

# Convert to Temperature to Kelvin
t1_k = t1_c + 273.15
v1 = (m * r * t1_k) / (p1 * 100) # Volume in m³ (100 converts bar to kPa)

#PROCESS CALCULATIONS
if process == "Constant Volume":
    v2 = v1
    t2_k = t1_k * (p2 / p1)
    work = 0
    heat = m * cv * (t2_k - t1_k)
    delta_s = m * cv * np.log(t2_k / t1_k)

elif process == "Constant Pressure":
    p2 = p1
    v2 = v1 * v_ratio
    t2_k = t1_k * (v2 / v1)
    work = p1 * 100 * (v2 - v1)
    heat = m * cp * (t2_k - t1_k)
    delta_s = m * cp * np.log(t2_k / t1_k)

elif process == "Isothermal":
    t2_k = t1_k
    v2 = v2_spec * m
    p2 = p1 * (v1 / v2)
    work = m * r * t1_k * np.log(v2 / v1)
    heat = work
    delta_s = m * r * np.log(v2 / v1)

elif process == "Adiabatic":
    # p1*v1^gamma = p2*v2^gamma
    v2 = v1 * (p1 / p2)**(1/gamma)
    t2_k = t1_k * (p2 / p1)**((gamma-1)/gamma)
    work = (p1*100*v1 - p2*100*v2) / (gamma - 1)
    heat = 0
    delta_s = 0

elif process == "Polytropic":
    v2 = v1 * (p1 / p2)**(1/n)
    t2_k = t1_k * (p2 / p1)**((n-1)/n)
    work = (p1*100*v1 - p2*100*v2) / (n - 1)
    # Heat for polytropic: Q = W * (gamma - n) / (gamma - 1)
    heat = work * (gamma - n) / (gamma - 1)
    delta_s = m * cv * ((gamma - n) / (1 - n)) * np.log(t2_k / t1_k)

#VISUALIZATION
col1, col2 = st.columns(2)
v_path = np.linspace(v1, v2, 100)

#PV Diagram
with col1:
    fig_pv, ax_pv = plt.subplots()
    if process == "Constant Volume":
        ax_pv.plot([v1, v1], [p1, p2], 'r-o', lw=2)
    elif process == "Constant Pressure":
        ax_pv.plot([v1, v2], [p1, p1], 'r-o', lw=2)
    else:
        # P = C / V^n
        p_path = p1 * (v1 / v_path)**(gamma if process == "Adiabatic" else (n if process == "Polytropic" else 1))
        ax_pv.plot(v_path, p_path, 'r-', lw=2)
        ax_pv.scatter([v1, v2], [p1, p2], color='red')
    
    ax_pv.set_title(f"P-V Diagram: {process}")
    ax_pv.set_xlabel("Volume (m³)")
    ax_pv.set_ylabel("Pressure (bar)")
    st.pyplot(fig_pv)

#TS Diagram
with col2:
    fig_ts, ax_ts = plt.subplots()
    # Simplified paths for T-s visualization
    t_path = np.linspace(t1_k, t2_k, 100)
    s_path = np.linspace(0, delta_s, 100)
    ax_ts.plot(s_path, t_path, 'b-', lw=2)
    ax_ts.scatter([s_path[0], s_path[-1]], [t1_k, t2_k], color='red')
    
    ax_ts.set_title(f"T-s Diagram: {process}")
    ax_ts.set_xlabel("Change in Entropy (kJ/K)")
    ax_ts.set_ylabel("Temperature (K)")
    st.pyplot(fig_ts)

# DATA TABLE
st.divider()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Final Temp", f"{t2_k - 273.15:.2f} °C")
c2.metric("Work (W)", f"{work:.2f} kJ")
c3.metric("Heat (Q)", f"{heat:.2f} kJ")
c4.metric("ΔS", f"{delta_s:.4f} kJ/K")