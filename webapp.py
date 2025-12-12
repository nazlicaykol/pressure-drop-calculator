import streamlit as st
import pandas as pd
import sqlite3
import math
from CoolProp.CoolProp import PropsSI
import plotly.express as px
import plotly.graph_objects as go

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="HydraulicSuite Pro",   
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. DATABASE KURULUMU ---
def init_db():
    conn = sqlite3.connect("project_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            material TEXT,
            nps TEXT,
            sch TEXT,
            pressure_drop REAL,
            velocity REAL,
            safety_factor REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- 3. VERİTABANLARI ---
material_list = {
    "Carbon Steel": 0.045,
    "Stainless Steel": 0.0015,
    "Copper": 0.0015,
    "PVC": 0.0015,
    "Concrete": 0.01,
    "Galvanized Steel": 0.15
}

# Malzeme Dayanımları (Safety Check için - MPa)
material_stress = {
    "Carbon Steel": 138.0,
    "Stainless Steel": 115.0,
    "Copper": 41.0,
    "PVC": 14.0,
    "Concrete": 20.0,
    "Galvanized Steel": 138.0
}

pipe_database = {
    "1/2 inch": {"10": {"OD": 21.3, "WT": 2.11}, "40": {"OD": 21.3, "WT": 2.77}, "80": {"OD": 21.3, "WT": 3.73}},
    "3/4 inch": {"10": {"OD": 26.7, "WT": 2.11}, "40": {"OD": 26.7, "WT": 2.87}, "80": {"OD": 26.7, "WT": 3.91}},
    "1 inch":   {"10": {"OD": 33.4, "WT": 2.77}, "40": {"OD": 33.4, "WT": 3.38}, "80": {"OD": 33.4, "WT": 4.55}},
    "1 1/2 inch": {"10": {"OD": 48.3, "WT": 2.77}, "40": {"OD": 48.3, "WT": 3.68}, "80": {"OD": 48.3, "WT": 5.08}},
    "2 inch":   {"10": {"OD": 60.3, "WT": 2.77}, "40": {"OD": 60.3, "WT": 3.91}, "80": {"OD": 60.3, "WT": 5.54}},
    "3 inch":   {"10": {"OD": 88.9, "WT": 3.05}, "40": {"OD": 88.9, "WT": 5.49}, "80": {"OD": 88.9, "WT": 7.62}},
    "4 inch":   {"10": {"OD": 114.3, "WT": 3.05}, "40": {"OD": 114.3, "WT": 6.02}, "80": {"OD": 114.3, "WT": 8.56}, "120": {"OD": 114.3, "WT": 11.13}, "160": {"OD": 114.3, "WT": 13.49}, "XXS": {"OD": 114.3, "WT": 17.12}},
    "6 inch":   {"10": {"OD": 168.3, "WT": 3.40}, "40": {"OD": 168.3, "WT": 7.11}, "80": {"OD": 168.3, "WT": 10.97}, "120": {"OD": 168.3, "WT": 14.27}, "160": {"OD": 168.3, "WT": 18.26}},
    "8 inch":   {"10": {"OD": 219.1, "WT": 3.76}, "40": {"OD": 219.1, "WT": 8.18}, "60": {"OD": 219.1, "WT": 10.31}, "80": {"OD": 219.1, "WT": 12.70}, "100": {"OD": 219.1, "WT": 15.09}, "120": {"OD": 219.1, "WT": 18.26}, "140": {"OD": 219.1, "WT": 20.62}, "160": {"OD": 219.1, "WT": 23.01}},
    "10 inch":  {"10": {"OD": 273.0, "WT": 4.19}, "20": {"OD": 273.0, "WT": 6.35}, "30": {"OD": 273.0, "WT": 7.80}, "40": {"OD": 273.0, "WT": 9.27}, "60": {"OD": 273.0, "WT": 12.70}, "80": {"OD": 273.0, "WT": 15.09}, "100": {"OD": 273.0, "WT": 18.26}, "120": {"OD": 273.0, "WT": 21.44}, "140": {"OD": 273.0, "WT": 25.40}, "160": {"OD": 273.0, "WT": 28.58}},
    "12 inch":  {"10": {"OD": 323.8, "WT": 4.57}, "20": {"OD": 323.8, "WT": 6.35}, "30": {"OD": 323.8, "WT": 8.38}, "40": {"OD": 323.8, "WT": 10.31}, "60": {"OD": 323.8, "WT": 14.27}, "80": {"OD": 323.8, "WT": 17.48}, "100": {"OD": 323.8, "WT": 21.44}, "120": {"OD": 323.8, "WT": 25.40}, "140": {"OD": 323.8, "WT": 28.58}, "160": {"OD": 323.8, "WT": 33.32}}
}

def get_ID(nps, sch):
    if nps in pipe_database and sch in pipe_database[nps]:
        d = pipe_database[nps][sch]
        return d["OD"] - 2 * d["WT"]
    return None

# ==================================================
# SOL MENÜ (NAVİGASYON)
# ==================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3093/3093409.png", width=80)
    st.title("HydraulicSuite Pro")
    
    st.info("Select a module below to start.")
    
    # SAYFA SEÇİMİ
    page_selection = st.radio(
        "Modules:",
        ["🏠 Pressure Drop Calc", "🛡️ Wall Thickness Check", "📊 Project Database"]
    )
    
    st.markdown("---")
    st.caption("v3.0 | Engineering Tools") 

# ==================================================
# SAYFA 1: PRESSURE DROP CALCULATOR
# ==================================================
if page_selection == "🏠 Pressure Drop Calc":
    st.title("💧 Pressure Drop Calculator")
    st.markdown("Calculate head loss, velocity and flow properties.")
    
    col_input, col_result = st.columns([1, 1.2])
    
    with col_input:
        with st.container(border=True):
            st.header("1. Inputs")
            
            st.subheader("Process Data")
            c1, c2 = st.columns(2)
            with c1:
                temp = st.number_input("Temperature (°C)", 120.0, step=1.0)
                flow = st.number_input("Mass Flow (t/h)", 100.0, step=10.0)
            with c2:
                pressure = st.number_input("Pressure (bar)", 40.0, step=1.0)
                length = st.number_input("Length (m)", 5000.0, step=50.0)

            st.markdown("---")
            st.subheader("Pipe & Material Selection")
            
            # --- Girdiler Artık Ana Ekranda ---
            material_name = st.selectbox("Material", list(material_list.keys()))
            
            c3, c4 = st.columns(2)
            with c3:
                nps_selected = st.selectbox("Nominal Size (Inch)", list(pipe_database.keys()), index=6) # 4 inch default
            with c4:
                available_schedules = list(pipe_database[nps_selected].keys())
                sch_selected = st.selectbox("Schedule (Thickness)", available_schedules)
            
            # Seçilen boru bilgisini göster
            current_ID = get_ID(nps_selected, sch_selected)
            d_info = pipe_database[nps_selected][sch_selected]
            st.info(f"📋 Info: OD {d_info['OD']} mm | WT {d_info['WT']} mm | ID {current_ID:.2f} mm")
            
            project_name = st.text_input("Project Name (Optional)", "My-Calculation-01")

            if st.button("🚀 CALCULATE", type="primary", use_container_width=True):
                roughness = material_list[material_name]
                ID_mm = current_ID
                T_K = temp + 273.15
                P_Pa = pressure * 100000
                m_kg_s = flow * 1000 / 3600
                ID_m = ID_mm / 1000
                
                try:
                    rho = PropsSI('D', 'T', T_K, 'P', P_Pa, 'Water')
                    mu = PropsSI('V', 'T', T_K, 'P', P_Pa, 'Water')
                    Area = math.pi * (ID_m / 2)**2
                    velocity = m_kg_s / (rho * Area)
                    Re = (rho * velocity * ID_m) / mu
                    
                    if Re > 4000:
                        f = (-1.8 * math.log10((roughness/1000/ID_m/3.7)**1.11 + 6.9/Re))**-2
                    elif Re > 0:
                        f = 64 / Re
                    else:
                        f = 0
                        
                    dP_Pa = f * (length / ID_m) * (rho * velocity**2 / 2)
                    dP_bar = dP_Pa / 100000
                    
                    # Session State'e Kaydet
                    st.session_state['res_dp'] = {
                        "dp": dP_bar, "vel": velocity, "re": Re, "f": f,
                        "rho": rho, "mu": mu
                    }
                    
                    # Veritabanına Kaydet
                    conn = sqlite3.connect("project_data.db")
                    cur = conn.cursor()
                    cur.execute("INSERT INTO projects (name, material, nps, sch, pressure_drop, velocity) VALUES (?,?,?,?,?,?)", 
                                (project_name, material_name, nps_selected, sch_selected, dP_bar, velocity))
                    conn.commit()
                    conn.close()
                    st.toast("Calculation saved!", icon="✅")
                    
                except Exception as e:
                    st.error(f"Error: {e}")

    with col_result:
        if 'res_dp' in st.session_state:
            res = st.session_state['res_dp']
            st.header("2. Results")
            
            with st.container(border=True):
                m1, m2 = st.columns(2)
                m1.metric("Pressure Drop", f"{res['dp']:.4f} bar", delta_color="inverse")
                m2.metric("Flow Velocity", f"{res['vel']:.2f} m/s")
                
                m3, m4 = st.columns(2)
                m3.metric("Reynolds No", f"{res['re']:.0f}")
                m4.metric("Friction Factor (f)", f"{res['f']:.5f}")
            
            st.subheader("Detailed Properties")
            st.write(f"Density: **{res['rho']:.2f} kg/m³**")
            st.write(f"Viscosity: **{res['mu']:.6f} Pa.s**")
            st.caption("Calculation based on Darcy-Weisbach & Colebrook-White equations.")
        else:
            st.info("👈 Please enter data and click Calculate.")

# ==================================================
# SAYFA 2: WALL THICKNESS SAFETY CHECK
# ==================================================
elif page_selection == "🛡️ Wall Thickness Check":
    st.title("🛡️ Wall Thickness Check")
    
    col_safe1, col_safe2 = st.columns([1, 1])
    
    with col_safe1:
        with st.container(border=True):
            st.subheader("Design Parameters")
            
            # Bu sayfada da kendi seçim kutuları olsun
            mat_safe = st.selectbox("Material", list(material_list.keys()), key="safe_mat")
            
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                nps_safe = st.selectbox("Size (Inch)", list(pipe_database.keys()), index=6, key="safe_nps")
            with c_s2:
                sch_safe = st.selectbox("Schedule", list(pipe_database[nps_safe].keys()), key="safe_sch")
                
            design_pres = st.number_input("Design Pressure (bar)", value=40.0)
            
            if st.button("🛡️ CHECK SAFETY", type="primary", use_container_width=True):
                P_MPa = design_pres / 10.0
                S_MPa = material_stress[mat_safe]
                OD_mm = pipe_database[nps_safe][sch_safe]["OD"]
                WT_actual = pipe_database[nps_safe][sch_safe]["WT"]
                
                # ASME B31.3 Basitleştirilmiş
                t_req = (P_MPa * OD_mm) / (2 * (S_MPa * 1.0 + P_MPa * 0.4))
                t_min = t_req + 1.0 # +1mm korozyon
                
                safety_factor = WT_actual / t_min
                is_safe = safety_factor >= 1.0
                
                st.session_state['res_safe'] = {
                    "req": t_min, "act": WT_actual, "safe": is_safe, "sf": safety_factor
                }

    with col_safe2:
        if 'res_safe' in st.session_state:
            res = st.session_state['res_safe']
            st.subheader("Safety Report")
            
            k1, k2 = st.columns(2)
            k1.metric("Required Thickness", f"{res['req']:.2f} mm")
            k2.metric("Actual Thickness", f"{res['act']:.2f} mm")
            
            if res['safe']:
                st.success(f"✅ SAFE! Pipe is strong enough. (Factor: {res['sf']:.2f})")
            else:
                st.error(f"⚠️ UNSAFE! Pipe is too thin. Need > {res['req']:.2f} mm")
                
            fig_safe = go.Figure()
            fig_safe.add_trace(go.Bar(x=["Required", "Actual"], y=[res['req'], res['act']], 
                                     marker_color=['red', 'green']))
            st.plotly_chart(fig_safe, use_container_width=True)

# ==================================================
# SAYFA 3: DATABASE
# ==================================================
elif page_selection == "📊 Project Database":
    st.title("📊 Project Database")
    
    conn = sqlite3.connect("project_data.db")
    df = pd.read_sql("SELECT * FROM projects ORDER BY id DESC", conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", csv, "projects.csv", "text/csv")
    else:
        st.info("Database is empty.")
