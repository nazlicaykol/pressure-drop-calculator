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

# --- 3. SABİTLER & VERİLER ---

material_list_roughness = {
    "Carbon Steel (New)": 0.045,
    "Carbon Steel (Corroded)": 0.5,
    "Stainless Steel": 0.0015,
    "Copper": 0.0015,
    "PVC / Plastic": 0.0015,
    "Concrete": 0.01,
    "Galvanized Steel": 0.15
}

# Fitting Eşdeğer Uzunluk Katsayıları (Le/D)
# Kaynak: Crane Technical Paper 410
fitting_led_database = {
    "Elbow 90° (Standard Radius)": 30,
    "Elbow 90° (Long Radius)": 20,
    "Elbow 45°": 16,
    "Tee (Flow through Run)": 20,
    "Tee (Flow through Branch)": 60,
    "Gate Valve (Fully Open)": 8,
    "Globe Valve (Fully Open)": 340,
    "Swing Check Valve": 100,
    "Butterfly Valve": 45,
    "Ball Valve (Reduced Bore)": 3
}

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

# --- GELİŞMİŞ HESAPLAMA FONKSİYONU ---
def calculate_hydraulics(temp_c, flow_th, press_bar, length_m, fitting_len_m, elevation_m, pump_eff, material, nps, sch):
    try:
        roughness = material_list_roughness.get(material, 0.045)
        
        if nps not in pipe_database or sch not in pipe_database[nps]:
            return None

        d_info = pipe_database[nps][sch]
        ID_mm = d_info["OD"] - 2 * d_info["WT"]
        
        if ID_mm <= 0: return None
            
        ID_m = ID_mm / 1000.0
        
        T_K = temp_c + 273.15
        P_Pa = press_bar * 100000
        m_kg_s = flow_th * 1000 / 3600
        
        try:
            rho = PropsSI('D', 'T', T_K, 'P', P_Pa, 'Water')
            mu = PropsSI('V', 'T', T_K, 'P', P_Pa, 'Water')
        except:
            return None
        
        Area = math.pi * (ID_m / 2)**2
        velocity = m_kg_s / (rho * Area)
        Re = (rho * velocity * ID_m) / mu
        
        # --- REYNOLDS KONTROLÜ ---
        if Re >= 2300:
            if roughness/1000/ID_m/3.7 <= 0 and Re == 0:
                 f = 0
            else:
                 f = (-1.8 * math.log10((roughness/1000/ID_m/3.7)**1.11 + 6.9/Re))**-2
        elif Re > 0:
            f = 64 / Re
        else:
            f = 0
            
        # Toplam eşdeğer uzunluk (Boru + Fittingler)
        total_effective_length = length_m + fitting_len_m
        dP_friction_Pa = f * (total_effective_length / ID_m) * (rho * velocity**2 / 2)
        
        # Statik Yük (Elevation)
        g = 9.81
        dP_static_Pa = rho * g * elevation_m
        dP_total_Pa = dP_friction_Pa + dP_static_Pa
        dP_total_bar = dP_total_Pa / 100000
        
        # Pompa Yükü (mSS)
        head_m = dP_total_Pa / (rho * g)
        
        # Hidrolik Güç
        flow_m3_h = flow_th / (rho / 1000) 
        power_hydraulic_kW = (flow_m3_h * head_m * rho * g) / (3.6 * 1e6)
        
        eff_factor = pump_eff / 100.0 if pump_eff > 0 else 0.01
        power_shaft_kW = power_hydraulic_kW / eff_factor
        
        return {
            "dp_total": dP_total_bar, 
            "dp_friction": dP_friction_Pa/100000,
            "dp_static": dP_static_Pa/100000, # Bar cinsinden statik
            "head_m": head_m,
            "vel": velocity, 
            "re": Re, "f": f,
            "rho": rho, "mu": mu, "id_mm": ID_mm, 
            "power_hyd": power_hydraulic_kW,
            "power_shaft": power_shaft_kW,
            "total_len": total_effective_length
        }
    except Exception as e:
        return None

# ==================================================
# SOL MENÜ
# ==================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3093/3093409.png", width=80)
    st.title("HydraulicSuite Pro")
    st.info("Select a module below to start.")
    
    page_selection = st.radio(
        "Modules:",
        [
            "🏠 Pressure Drop Calc", 
            "🛡️ Wall Thickness Check", 
            "📈 Analytics & Simulation",
            "📚 Project History"
        ]
    )
    st.markdown("---")
    st.caption("v5.1 | Engineering Tools") 

# ==================================================
# SAYFA 1: PRESSURE DROP CALCULATOR (GELİŞMİŞ)
# ==================================================
if page_selection == "🏠 Pressure Drop Calc":
    st.title("💧 Pressure Drop & Pump Power")
    
    col_input, col_result = st.columns([1, 1.2])
    
    with col_input:
        with st.container(border=True):
            st.header("1. Design Inputs")
            
            # --- Boru ve Malzeme Seçimi (Önce bunu alıyoruz ki çap belli olsun) ---
            st.subheader("🛠️ Pipe & Material")
            material_name = st.selectbox("Material", list(material_list_roughness.keys()))
            
            c3, c4 = st.columns(2)
            with c3:
                nps_selected = st.selectbox("Nominal Size (Inch)", list(pipe_database.keys()), index=6)
            with c4:
                available_schedules = list(pipe_database[nps_selected].keys())
                sch_selected = st.selectbox("Schedule", available_schedules)
            
            # Seçilen borunun ID'sini hemen alalım (Hesap için lazım)
            current_ID_mm = get_ID(nps_selected, sch_selected)
            current_ID_m = current_ID_mm / 1000.0

            st.markdown("---")
            
            # --- Akışkan ve Hat Bilgileri ---
            st.subheader("⚙️ Process Data")
            c1, c2 = st.columns(2)
            with c1:
                flow = st.number_input("Mass Flow (t/h)", 100.0, step=10.0)
                temp = st.number_input("Temperature (°C)", 120.0, step=1.0)
                pressure = st.number_input("Line Pressure (bar)", 40.0)
            with c2:
                length = st.number_input("Straight Pipe Length (m)", 1000.0, step=50.0)
                elevation = st.number_input("Elevation Change (m)", 0.0, help="Vertical lift (+ for up, - for down)")

            # --- YENİ: FITTING HESAPLAYICI (EXPANDER) ---
            calculated_fitting_len = 0.0
            with st.expander("🔧 Fitting & Valve Calculator (Optional)"):
                st.caption("Select quantities to calculate Equivalent Length (Le)")
                
                col_fit1, col_fit2 = st.columns(2)
                fitting_quantities = {}
                
                # Fittingleri iki kolona bölerek gösterelim
                items = list(fitting_led_database.items())
                half = len(items) // 2
                
                with col_fit1:
                    for name, led_val in items[:half]:
                        qty = st.number_input(f"{name}", 0, step=1, key=f"fit_{name}")
                        if qty > 0:
                            # Le = (Le/D) * ID
                            eq_len = qty * led_val * current_ID_m
                            calculated_fitting_len += eq_len
                            
                with col_fit2:
                    for name, led_val in items[half:]:
                        qty = st.number_input(f"{name}", 0, step=1, key=f"fit_{name}")
                        if qty > 0:
                            eq_len = qty * led_val * current_ID_m
                            calculated_fitting_len += eq_len
                
                if calculated_fitting_len > 0:
                    st.info(f"Total Equivalent Length added: **{calculated_fitting_len:.2f} m**")
                else:
                    st.caption("No fittings added.")

            st.markdown("---")
            pump_eff = st.number_input("Pump Efficiency (%)", 75.0, step=5.0)
            project_name = st.text_input("Project Name (Optional)", "New-Design-01")

            if st.button("🚀 CALCULATE", type="primary", use_container_width=True):
                # Hesaplama (calculated_fitting_len'i fonksiyona yolluyoruz)
                res = calculate_hydraulics(temp, flow, pressure, length, calculated_fitting_len, elevation, pump_eff, material_name, nps_selected, sch_selected)
                
                if res:
                    st.session_state['res_dp'] = res
                    conn = sqlite3.connect(DB_FILE)
                    cur = conn.cursor()
                    cur.execute("INSERT INTO projects (name, material, nps, sch, pressure_drop, velocity) VALUES (?,?,?,?,?,?)", 
                                (project_name, material_name, nps_selected, sch_selected, res['dp_total'], res['vel']))
                    conn.commit()
                    conn.close()
                    st.toast("Calculation saved!", icon="✅")
                else:
                    st.error("Calculation Error! Check inputs.")

    with col_result:
        if 'res_dp' in st.session_state:
            res = st.session_state['res_dp']
            st.header("2. Results")
            
            # --- Ana Sonuçlar ---
            with st.container(border=True):
                st.subheader("⚡ Pump Requirements")
                k1, k2, k3 = st.columns(3)
                k1.metric("Total Pump Head", f"{res['head_m']:.1f} mSS", help="Total Dynamic Head required")
                k2.metric("Shaft Power", f"{res['power_shaft']:.2f} kW", help="Motor power required")
                k3.metric("Hydraulic Power", f"{res['power_hyd']:.2f} kW", help="Power transferred to fluid")
                [Image of centrifugal pump curve]
                st.markdown("---")
                st.subheader("🌊 Flow Analysis")
                m1, m2 = st.columns(2)
                m1.metric("Total Pressure Drop", f"{res['dp_total']:.4f} bar", delta_color="inverse")
                m2.metric("Flow Velocity", f"{res['vel']:.2f} m/s")
            
            # --- Detaylı Analiz (Görsel Grafik) ---
            st.subheader("Pressure Drop Breakdown")
            
            # Basınç Kaybı Dağılım Grafiği (Friction vs Static)
            # Eğer statik yük varsa gösterelim
            breakdown_data = {
                "Loss Type": ["Friction Loss", "Static Head (Elevation)"],
                "Value (bar)": [res['dp_friction'], res['dp_static']]
            }
            
            # Negatif statik yük (aşağı basma) grafikte garip durabilir, mutlak değer veya net gösterim gerekebilir.
            # Şimdilik standart gösterim yapıyoruz.
            fig_pie = px.pie(
                values=[max(0, res['dp_friction']), max(0, res['dp_static'])], 
                names=["Friction Loss (Pipe+Fittings)", "Static Head (Elevation)"],
                hole=0.4,
                color_discrete_sequence=['#FF4B4B', '#00CC96']
            )
            fig_pie.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)

            with st.expander("🔎 Detailed Calculations"):
                st.write(f"**Total Equivalent Length:** {res['total_len']:.2f} m")
                st.write(f"**Friction Loss:** {res['dp_friction']:.4f} bar")
                st.write(f"**Static Head:** {res['dp_static']:.4f} bar")
                st.write(f"**Reynolds No:** {res['re']:.0f}")
                st.write(f"**Fluid Density:** {res['rho']:.2f} kg/m³")
                
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
            
            c_s
