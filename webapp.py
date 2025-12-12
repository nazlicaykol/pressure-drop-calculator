import streamlit as st
import pandas as pd
import sqlite3
import math
from CoolProp.CoolProp import PropsSI
import plotly.express as px
import plotly.graph_objects as go

# --- 1. SAYFA AYARLARI (Page Config) ---
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

# --- 3. VERİTABANLARI (GENİŞLETİLMİŞ) ---
# Malzeme Pürüzlülüğü (mm) ve İzin Verilen Gerilme (Allowable Stress - MPa) [Yaklaşık Değerler]
material_props = {
    "Carbon Steel (A106 Gr.B)": {"roughness": 0.045, "stress": 138.0},  # ~20,000 psi
    "Stainless Steel (A312 TP304)": {"roughness": 0.015, "stress": 115.0}, # ~16,700 psi
    "PVC (Sch 40/80)": {"roughness": 0.0015, "stress": 14.0},       # ~2,000 psi
    "Copper (B88)": {"roughness": 0.0015, "stress": 41.0},          # ~6,000 psi
    "Galvanized Steel": {"roughness": 0.15, "stress": 138.0}
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
    
    # SAYFA SEÇİMİ (NAVIGASYON)
    page_selection = st.radio(
        "Go to Module:",
        ["🏠 Pressure Drop Calc", "🛡️ Wall Thickness Check", "📊 Project Database"]
    )
    st.markdown("---")
    
    # Global Girdiler (Tüm sayfalarda kullanılabilir)
    st.write("🔧 **Quick Settings**")
    material_name = st.selectbox("Material", list(material_props.keys()))
    nps_selected = st.selectbox("Nominal Size (NPS)", list(pipe_database.keys()), index=6)
    
    available_schedules = list(pipe_database[nps_selected].keys())
    sch_selected = st.selectbox("Schedule", available_schedules)
    
    current_ID = get_ID(nps_selected, sch_selected)
    d_info = pipe_database[nps_selected][sch_selected]
    
    st.info(f"OD: {d_info['OD']} mm | WT: {d_info['WT']} mm")
    st.caption("v2.1 | ASME B31.3 Compliant")

# ==================================================
# SAYFA 1: PRESSURE DROP CALCULATOR (MEVCUT SİSTEM)
# ==================================================
if page_selection == "🏠 Pressure Drop Calc":
    st.title("💧 Pressure Drop Calculator")
    st.markdown("Calculate head loss in pipes using Darcy-Weisbach equation.")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Process Inputs")
            temp = st.number_input("Temperature (°C)", 120.0, step=1.0)
            pressure = st.number_input("Pressure (bar)", 40.0, step=1.0)
            flow = st.number_input("Mass Flow (t/h)", 100.0, step=10.0)
            length = st.number_input("Length (m)", 5000.0, step=50.0)
            
    with col2:
        with st.container(border=True):
            st.subheader("Results Dashboard")
            if st.button("🚀 CALCULATE PRESSURE DROP", type="primary", use_container_width=True):
                roughness = material_props[material_name]["roughness"]
                ID_mm = current_ID
                T_K = temp + 273.15
                P_Pa = pressure * 100000
                m_kg_s = flow * 1000 / 3600
                ID_m = ID_mm / 1000
                
                try:
                    rho = PropsSI('D', 'T', T_K, 'P', P_Pa, 'Water')
                    mu = PropsSI('V', 'T', T_K, 'P', P_Pa, 'Water')
                    Area = math.pi * (ID_m / 2)**2
                    velocity = m_dot_kg_s / (rho * Area)
                    Re = (rho * velocity * ID_m) / mu
                    
                    if Re > 4000:
                        f = (-1.8 * math.log10((roughness/1000/ID_m/3.7)**1.11 + 6.9/Re))**-2
                    elif Re > 0:
                        f = 64 / Re
                    else:
                        f = 0
                        
                    dP_Pa = f * (length / ID_m) * (rho * velocity**2 / 2)
                    dP_bar = dP_Pa / 100000
                    
                    # Sonuçlar
                    c1, c2 = st.columns(2)
                    c1.metric("Pressure Drop", f"{dP_bar:.4f} bar", delta_color="inverse")
                    c2.metric("Velocity", f"{velocity:.2f} m/s")
                    st.metric("Reynolds Number", f"{Re:.0f}")
                    
                    # Veritabanına Yaz
                    conn = sqlite3.connect("project_data.db")
                    cur = conn.cursor()
                    cur.execute("INSERT INTO projects (name, material, nps, sch, pressure_drop, velocity) VALUES (?,?,?,?,?,?)", 
                                ("Pressure Calc", material_name, nps_selected, sch_selected, dP_bar, velocity))
                    conn.commit()
                    conn.close()
                    st.toast("Result saved to database!")
                    
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.info("Click the button to start calculation.")

# ==================================================
# SAYFA 2: WALL THICKNESS SAFETY CHECK (YENİ MODÜL!)
# ==================================================
elif page_selection == "🛡️ Wall Thickness Check":
    st.title("🛡️ Pipe Wall Thickness Safety Check")
    st.markdown("Check if the selected pipe can withstand the internal pressure (ASME B31.3 Standard).")
    
    col_safe1, col_safe2 = st.columns([1, 1])
    
    with col_safe1:
        with st.container(border=True):
            st.subheader("Design Conditions")
            design_pres = st.number_input("Design Pressure (bar)", value=40.0)
            design_temp = st.number_input("Design Temperature (°C)", value=120.0)
            
            # ASME Formülü Gösterimi
            st.markdown("### Formula (ASME B31.3)")
            st.latex(r''' t_{min} = \frac{P \cdot D}{2 (S \cdot E + P \cdot Y)} ''')
            st.caption("P: Pressure, D: OD, S: Stress, E: Quality Factor, Y: Temp Coeff")

    with col_safe2:
        if st.button("🛡️ RUN SAFETY ANALYSIS", type="primary", use_container_width=True):
            # Parametreler
            P_MPa = design_pres / 10.0 # Bar -> MPa
            S_MPa = material_props[material_name]["stress"] # Malzeme dayanımı
            OD_mm = pipe_database[nps_selected][sch_selected]["OD"]
            WT_actual = pipe_database[nps_selected][sch_selected]["WT"]
            
            # Sabitler (Basitleştirilmiş)
            E = 1.0 # Seamless Pipe assumed
            Y = 0.4 # For Ferritic steels < 482 C
            
            # Hesaplama: Gereken Minimum Et Kalınlığı
            # t = (P * D) / (2 * (S*E + P*Y))
            t_required = (P_MPa * OD_mm) / (2 * (S_MPa * E + P_MPa * Y))
            
            # Korozyon Payı (Corrosion Allowance - C)
            C = 1.0 # 1 mm pay bırakalım
            t_min_total = t_required + C
            
            # Güvenlik Kontrolü
            safety_ratio = WT_actual / t_min_total
            is_safe = safety_ratio >= 1.0
            
            # Sonuç Kartları
            st.subheader("Analysis Result")
            
            m1, m2 = st.columns(2)
            m1.metric("Required Thickness (w/ Corrosion)", f"{t_min_total:.2f} mm")
            m2.metric("Actual Thickness (Selected)", f"{WT_actual:.2f} mm")
            
            # Görsel Gösterge (Gauge Chart benzeri)
            st.write("### Safety Status")
            if is_safe:
                st.success(f"✅ SAFE! The pipe is strong enough. (Safety Factor: {safety_ratio:.2f})")
                st.progress(min(safety_ratio/3, 1.0)) # Barı doldur
            else:
                st.error(f"⚠️ UNSAFE! Pipe wall is too thin. Need at least {t_min_total:.2f} mm")
                st.progress(min(safety_ratio/3, 1.0))

            # Grafiksel Gösterim (Required vs Actual)
            fig_safe = go.Figure()
            fig_safe.add_trace(go.Bar(x=["Required", "Actual"], y=[t_min_total, WT_actual], 
                                     marker_color=['red', 'green']))
            fig_safe.update_layout(title="Thickness Comparison", yaxis_title="Thickness (mm)")
            st.plotly_chart(fig_safe, use_container_width=True)

# ==================================================
# SAYFA 3: DATABASE & ANALYTICS
# ==================================================
elif page_selection == "📊 Project Database":
    st.title("📊 Project Database & Analytics")
    
    conn = sqlite3.connect("project_data.db")
    df = pd.read_sql("SELECT * FROM projects ORDER BY id DESC", conn)
    conn.close()
    
    if not df.empty:
        col_db1, col_db2 = st.columns([2, 1])
        
        with col_db1:
            st.subheader("Saved Calculations")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Database (CSV)", csv, "database.csv", "text/csv")
            
        with col_db2:
            st.subheader("Insights")
            # Basit bir analiz grafiği: Çaplara göre Basınç Kaybı dağılımı
            fig_stat = px.box(df, x="nps", y="pressure_drop", title="Pressure Drop Distribution by Size")
            st.plotly_chart(fig_stat, use_container_width=True)
    else:
        st.info("No data saved yet. Go to Calculator and save a project.")
