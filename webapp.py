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

# --- VERİTABANI DOSYA ADI ---
DB_FILE = "project_data_final.db"

# --- 2. DATABASE KURULUMU ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
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

# --- 3. VERİTABANLARI & SABİTLER ---

# Malzeme Pürüzlülükleri
material_list_roughness = {
    "Carbon Steel (New)": 0.045,
    "Carbon Steel (Corroded)": 0.5,
    "Stainless Steel": 0.0015,
    "Copper": 0.0015,
    "PVC / Plastic": 0.0015,
    "Concrete": 0.01,
    "Galvanized Steel": 0.15
}

# ASME Malzeme Dayanımları
asme_material_data = {
    "--- CARBON STEEL ---": 0,
    "A106 Grade A": 110.0,
    "A106 Grade B": 138.0,
    "A106 Grade C": 161.0,
    "A53 Grade A": 110.0,
    "A53 Grade B": 138.0,
    "API 5L Grade B": 138.0,
    "API 5L X42 (L290)": 138.0,
    "API 5L X52 (L360)": 153.0,
    "API 5L X60 (L415)": 173.0,
    "API 5L X65 (L450)": 178.0,
    "A333 Grade 6 (Low Temp)": 138.0,
    "--- STAINLESS STEEL ---": 0,
    "SS 304 (A312 TP304)": 138.0,
    "SS 304L (A312 TP304L)": 115.0,
    "SS 316 (A312 TP316)": 138.0,
    "SS 316L (A312 TP316L)": 115.0,
    "SS 321 (A312 TP321)": 138.0,
    "SS 347 (A312 TP347)": 138.0,
    "--- ALLOY STEEL ---": 0,
    "A335 P11 (1-1/4 Cr)": 126.0,
    "A335 P22 (2-1/4 Cr)": 126.0,
    "A335 P5 (5 Cr)": 126.0,
    "A335 P9 (9 Cr)": 138.0,
    "A335 P91 (9 Cr-V)": 195.0
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

# --- ORTAK HESAPLAMA FONKSİYONU ---
def calculate_hydraulics(temp_c, flow_th, press_bar, length_m, material, nps, sch):
    try:
        roughness = material_list_roughness.get(material, 0.045)
        d_info = pipe_database[nps][sch]
        ID_mm = d_info["OD"] - 2 * d_info["WT"]
        ID_m = ID_mm / 1000.0
        
        T_K = temp_c + 273.15
        P_Pa = press_bar * 100000
        m_kg_s = flow_th * 1000 / 3600
        
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
            
        dP_Pa = f * (length_m / ID_m) * (rho * velocity**2 / 2)
        dP_bar = dP_Pa / 100000
        
        return {
            "dp": dP_bar, "vel": velocity, "re": Re, "f": f,
            "rho": rho, "mu": mu, "id_mm": ID_mm, "nps": nps
        }
    except Exception as e:
        return None

# ==================================================
# SOL MENÜ (NAVİGASYON)
# ==================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3093/3093409.png", width=80)
    st.title("HydraulicSuite Pro")
    
    st.info("Select a module below to start.")
    
    # ARTIK 4 MODÜL VAR
    page_selection = st.radio(
        "Modules:",
        [
            "🏠 Pressure Drop Calc", 
            "🛡️ Wall Thickness Check", 
            "📈 Analytics & Simulation",  # Yeni Modül 3
            "📚 Project History"          # Yeni Modül 4
        ]
    )
    
    st.markdown("---")
    st.caption("v4.0 | Engineering Tools") 

# ==================================================
# SAYFA 1: PRESSURE DROP CALCULATOR
# ==================================================
if page_selection == "🏠 Pressure Drop Calc":
    st.title("💧 Pressure Drop Calculator")
    
    col_input, col_result = st.columns([1, 1.2])
    
    with col_input:
        with st.container(border=True):
            st.header("1. Inputs")
            
            c1, c2 = st.columns(2)
            with c1:
                temp = st.number_input("Temperature (°C)", 120.0, step=1.0)
                flow = st.number_input("Mass Flow (t/h)", 100.0, step=10.0)
            with c2:
                pressure = st.number_input("Pressure (bar)", 40.0, step=1.0)
                length = st.number_input("Length (m)", 5000.0, step=50.0)

            st.markdown("---")
            material_name = st.selectbox("Material", list(material_list_roughness.keys()))
            
            c3, c4 = st.columns(2)
            with c3:
                nps_selected = st.selectbox("Nominal Size (Inch)", list(pipe_database.keys()), index=6) 
            with c4:
                available_schedules = list(pipe_database[nps_selected].keys())
                sch_selected = st.selectbox("Schedule (Thickness)", available_schedules)
            
            project_name = st.text_input("Project Name (Optional)", "My-Calculation-01")

            if st.button("🚀 CALCULATE", type="primary", use_container_width=True):
                res = calculate_hydraulics(temp, flow, pressure, length, material_name, nps_selected, sch_selected)
                
                if res:
                    st.session_state['res_dp'] = res
                    conn = sqlite3.connect(DB_FILE)
                    cur = conn.cursor()
                    cur.execute("INSERT INTO projects (name, material, nps, sch, pressure_drop, velocity) VALUES (?,?,?,?,?,?)", 
                                (project_name, material_name, nps_selected, sch_selected, res['dp'], res['vel']))
                    conn.commit()
                    conn.close()
                    st.toast("Calculation saved!", icon="✅")
                else:
                    st.error("Calculation Error! Check inputs.")

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
            selectable_materials = [k for k,v in asme_material_data.items() if v > 0]
            mat_safe = st.selectbox("ASME Material Spec", selectable_materials, index=1, key="safe_mat")
            st.caption(f"Allowable Stress (S): **{asme_material_data[mat_safe]} MPa**")
            
            c_s1, c_s2 = st.columns(2)
            with c_s1:
                nps_safe = st.selectbox("Size (Inch)", list(pipe_database.keys()), index=6, key="safe_nps")
            with c_s2:
                sch_safe = st.selectbox("Schedule", list(pipe_database[nps_safe].keys()), key="safe_sch")
                
            design_pres = st.number_input("Design Pressure (bar)", value=40.0)
            
            if st.button("🛡️ CHECK SAFETY", type="primary", use_container_width=True):
                P_MPa = design_pres / 10.0
                S_MPa = asme_material_data[mat_safe]
                OD_mm = pipe_database[nps_safe][sch_safe]["OD"]
                WT_actual = pipe_database[nps_safe][sch_safe]["WT"]
                
                t_req = (P_MPa * OD_mm) / (2 * (S_MPa * 1.0 + P_MPa * 0.4))
                t_min = t_req + 1.0 
                safety_factor = WT_actual / t_min
                is_safe = safety_factor >= 1.0
                
                st.session_state['res_safe'] = {
                    "req": t_min, "act": WT_actual, "safe": is_safe, "sf": safety_factor, "mat": mat_safe
                }

    with col_safe2:
        if 'res_safe' in st.session_state:
            res = st.session_state['res_safe']
            st.subheader(f"Result: {res['mat']}")
            k1, k2 = st.columns(2)
            k1.metric("Required", f"{res['req']:.2f} mm")
            k2.metric("Actual", f"{res['act']:.2f} mm")
            
            if res['safe']:
                st.success(f"✅ SAFE! Factor: {res['sf']:.2f}")
            else:
                st.error(f"⚠️ UNSAFE! Need > {res['req']:.2f} mm")
                
            fig_safe = go.Figure()
            fig_safe.add_trace(go.Bar(x=["Required", "Actual"], y=[res['req'], res['act']], marker_color=['#FF4B4B', '#00CC96']))
            st.plotly_chart(fig_safe, use_container_width=True)

# ==================================================
# SAYFA 3: ANALYTICS & SIMULATION (GRAFİK MERKEZİ)
# ==================================================
elif page_selection == "📈 Analytics & Simulation":
    st.title("📈 Analytics & Simulation Hub")
    
    # Sekmeler: Biri simülasyon, biri geçmiş veri grafikleri
    tab_sim, tab_hist = st.tabs(["⚡ Live Simulation", "📊 Historical Charts"])
    
    # --- 1. CANLI SİMÜLASYON ---
    with tab_sim:
        st.subheader("Hydraulic Performance Simulator")
        st.markdown("Compare all pipe sizes instantly.")
        
        with st.container(border=True):
            col_sim1, col_sim2, col_sim3 = st.columns(3)
            with col_sim1:
                sim_flow = st.number_input("Flow Rate (t/h)", 100.0, step=10.0, key="sim_flow")
                sim_mat = st.selectbox("Material", list(material_list_roughness.keys()), key="sim_mat")
            with col_sim2:
                sim_pres = st.number_input("Pressure (bar)", 40.0, key="sim_pres")
                sim_temp = st.number_input("Temp (°C)", 120.0, key="sim_temp")
            with col_sim3:
                sim_len = st.number_input("Length (m)", 1000.0, step=100.0, key="sim_len")
                btn_simulate = st.button("🔄 RUN SIMULATION", type="primary", use_container_width=True)
        
        if btn_simulate:
            results_list = []
            for size_name, schedules in pipe_database.items():
                sch_to_use = "40" if "40" in schedules else list(schedules.keys())[0]
                res = calculate_hydraulics(sim_temp, sim_flow, sim_pres, sim_len, sim_mat, size_name, sch_to_use)
                if res:
                    results_list.append({
                        "NPS": size_name, "ID (mm)": res['id_mm'],
                        "Velocity (m/s)": res['vel'], "Pressure Drop (bar)": res['dp']
                    })
            
            df_sim = pd.DataFrame(results_list)
            
            c_chart, c_tbl = st.columns([1.5, 1])
            with c_chart:
                fig_sim = px.scatter(df_sim, x="Velocity (m/s)", y="Pressure Drop (bar)",
                                     color="NPS", size="ID (mm)", size_max=40,
                                     text="NPS", title="Velocity vs Pressure Drop Trade-off")
                fig_sim.update_traces(textposition='top center')
                st.plotly_chart(fig_sim, use_container_width=True)
            with c_tbl:
                st.dataframe(df_sim.sort_values("Velocity (m/s)", ascending=False), hide_index=True, use_container_width=True)

    # --- 2. GEÇMİŞ VERİ GRAFİKLERİ ---
    with tab_hist:
        conn = sqlite3.connect(DB_FILE)
        df_hist = pd.read_sql("SELECT * FROM projects", conn)
        conn.close()
        
        if not df_hist.empty:
            st.subheader("Historical Data Analysis")
            col_h1, col_h2 = st.columns(2)
            
            with col_h1:
                st.caption("Commonly Used Materials")
                fig_pie = px.pie(df_hist, names='material', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with col_h2:
                st.caption("Calculated Velocities Overview")
                fig_hist = px.histogram(df_hist, x="velocity", nbins=10, title="Velocity Distribution")
                st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No historical data available yet.")

# ==================================================
# SAYFA 4: PROJECT HISTORY (SADECE VERİ)
# ==================================================
elif page_selection == "📚 Project History":
    st.title("📚 Project History")
    st.markdown("Access your full calculation database here.")
    
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM projects ORDER BY id DESC", conn)
    conn.close()
    
    if not df.empty:
        # Arama Filtresi
        search_term = st.text_input("🔍 Search by Project Name or Material", "")
        if search_term:
            df = df[df['name'].str.contains(search_term, case=False) | df['material'].str.contains(search_term, case=False)]
        
        st.dataframe(
            df, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "timestamp": st.column_config.DatetimeColumn("Date", format="D MMM YYYY, HH:mm"),
                "pressure_drop": st.column_config.NumberColumn("dP (bar)", format="%.4f"),
                "velocity": st.column_config.NumberColumn("Vel (m/s)", format="%.2f"),
            }
        )
        
        st.markdown("---")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Full Database as CSV",
            data=csv,
            file_name="project_history_export.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.warning("Database is empty. No records found.")
