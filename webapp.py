import streamlit as st
import pandas as pd
import sqlite3
import math
from CoolProp.CoolProp import PropsSI
import plotly.express as px

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="HydraulicCalc Pro",
    page_icon="⚙️",
    layout="wide", # Geniş ekran modu
    initial_sidebar_state="expanded" # Yan menü açık başlasın
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
            velocity REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- 3. VERİTABANLARI (ASME B31.3 & B36.10M) ---
material_list = {
    "ASME B31.3 - Carbon Steel (A106 Gr.B)": 0.045,
    "ASME B31.3 - Stainless Steel (A312 TP304/316)": 0.015,
    "ASME B31.3 - Galvanized Steel": 0.15,
    "Commercial Steel": 0.045,
    "Drawn Brass / Copper": 0.0015,
    "PVC / Thermoplastics": 0.0015,
    "Concrete (Smooth)": 0.3,
    "Cast Iron": 0.26
}

pipe_database = {
    "1/8 inch": {"10": {"OD": 10.3, "WT": 1.24}, "40": {"OD": 10.3, "WT": 1.73}, "STD": {"OD": 10.3, "WT": 1.73}, "80": {"OD": 10.3, "WT": 2.41}, "XS": {"OD": 10.3, "WT": 2.41}},
    "1/4 inch": {"10": {"OD": 13.7, "WT": 1.65}, "40": {"OD": 13.7, "WT": 2.24}, "STD": {"OD": 13.7, "WT": 2.24}, "80": {"OD": 13.7, "WT": 3.02}, "XS": {"OD": 13.7, "WT": 3.02}},
    "3/8 inch": {"10": {"OD": 17.1, "WT": 1.65}, "40": {"OD": 17.1, "WT": 2.31}, "STD": {"OD": 17.1, "WT": 2.31}, "80": {"OD": 17.1, "WT": 3.20}, "XS": {"OD": 17.1, "WT": 3.20}},
    "1/2 inch": {"10": {"OD": 21.3, "WT": 2.11}, "40": {"OD": 21.3, "WT": 2.77}, "STD": {"OD": 21.3, "WT": 2.77}, "80": {"OD": 21.3, "WT": 3.73}, "XS": {"OD": 21.3, "WT": 3.73}, "160": {"OD": 21.3, "WT": 4.78}, "XXS": {"OD": 21.3, "WT": 7.47}},
    "3/4 inch": {"10": {"OD": 26.7, "WT": 2.11}, "40": {"OD": 26.7, "WT": 2.87}, "STD": {"OD": 26.7, "WT": 2.87}, "80": {"OD": 26.7, "WT": 3.91}, "XS": {"OD": 26.7, "WT": 3.91}, "160": {"OD": 26.7, "WT": 5.56}, "XXS": {"OD": 26.7, "WT": 7.82}},
    "1 inch":   {"5": {"OD": 33.4, "WT": 1.65}, "10": {"OD": 33.4, "WT": 2.77}, "40": {"OD": 33.4, "WT": 3.38}, "STD": {"OD": 33.4, "WT": 3.38}, "80": {"OD": 33.4, "WT": 4.55}, "XS": {"OD": 33.4, "WT": 4.55}, "160": {"OD": 33.4, "WT": 6.35}, "XXS": {"OD": 33.4, "WT": 9.09}},
    "1 1/2 inch": {"10": {"OD": 48.3, "WT": 2.77}, "40": {"OD": 48.3, "WT": 3.68}, "STD": {"OD": 48.3, "WT": 3.68}, "80": {"OD": 48.3, "WT": 5.08}, "XS": {"OD": 48.3, "WT": 5.08}, "160": {"OD": 48.3, "WT": 7.14}, "XXS": {"OD": 48.3, "WT": 10.15}},
    "2 inch":   {"10": {"OD": 60.3, "WT": 2.77}, "40": {"OD": 60.3, "WT": 3.91}, "STD": {"OD": 60.3, "WT": 3.91}, "80": {"OD": 60.3, "WT": 5.54}, "XS": {"OD": 60.3, "WT": 5.54}, "160": {"OD": 60.3, "WT": 8.74}, "XXS": {"OD": 60.3, "WT": 11.07}},
    "2 1/2 inch": {"10": {"OD": 73.0, "WT": 3.05}, "40": {"OD": 73.0, "WT": 5.16}, "STD": {"OD": 73.0, "WT": 5.16}, "80": {"OD": 73.0, "WT": 7.01}, "XS": {"OD": 73.0, "WT": 7.01}, "160": {"OD": 73.0, "WT": 9.53}, "XXS": {"OD": 73.0, "WT": 14.02}},
    "3 inch":   {"10": {"OD": 88.9, "WT": 3.05}, "40": {"OD": 88.9, "WT": 5.49}, "STD": {"OD": 88.9, "WT": 5.49}, "80": {"OD": 88.9, "WT": 7.62}, "XS": {"OD": 88.9, "WT": 7.62}, "160": {"OD": 88.9, "WT": 11.13}, "XXS": {"OD": 88.9, "WT": 15.24}},
    "4 inch":   {"10": {"OD": 114.3, "WT": 3.05}, "40": {"OD": 114.3, "WT": 6.02}, "STD": {"OD": 114.3, "WT": 6.02}, "80": {"OD": 114.3, "WT": 8.56}, "XS": {"OD": 114.3, "WT": 8.56}, "120": {"OD": 114.3, "WT": 11.13}, "160": {"OD": 114.3, "WT": 13.49}, "XXS": {"OD": 114.3, "WT": 17.12}},
    "6 inch":   {"10": {"OD": 168.3, "WT": 3.40}, "40": {"OD": 168.3, "WT": 7.11}, "STD": {"OD": 168.3, "WT": 7.11}, "80": {"OD": 168.3, "WT": 10.97}, "XS": {"OD": 168.3, "WT": 10.97}, "120": {"OD": 168.3, "WT": 14.27}, "160": {"OD": 168.3, "WT": 18.26}, "XXS": {"OD": 168.3, "WT": 21.95}},
    "8 inch":   {"10": {"OD": 219.1, "WT": 3.76}, "40": {"OD": 219.1, "WT": 8.18}, "STD": {"OD": 219.1, "WT": 8.18}, "60": {"OD": 219.1, "WT": 10.31}, "80": {"OD": 219.1, "WT": 12.70}, "XS": {"OD": 219.1, "WT": 12.70}, "100": {"OD": 219.1, "WT": 15.09}, "120": {"OD": 219.1, "WT": 18.26}, "140": {"OD": 219.1, "WT": 20.62}, "160": {"OD": 219.1, "WT": 23.01}, "XXS": {"OD": 219.1, "WT": 22.23}},
    "10 inch":  {"10": {"OD": 273.0, "WT": 4.19}, "20": {"OD": 273.0, "WT": 6.35}, "30": {"OD": 273.0, "WT": 7.80}, "40": {"OD": 273.0, "WT": 9.27}, "STD": {"OD": 273.0, "WT": 9.27}, "60": {"OD": 273.0, "WT": 12.70}, "XS": {"OD": 273.0, "WT": 12.70}, "80": {"OD": 273.0, "WT": 15.09}, "100": {"OD": 273.0, "WT": 18.26}, "120": {"OD": 273.0, "WT": 21.44}, "140": {"OD": 273.0, "WT": 25.40}, "XXS": {"OD": 273.0, "WT": 25.40}, "160": {"OD": 273.0, "WT": 28.58}},
    "12 inch":  {"10": {"OD": 323.8, "WT": 4.57}, "20": {"OD": 323.8, "WT": 6.35}, "30": {"OD": 323.8, "WT": 8.38}, "40": {"OD": 323.8, "WT": 10.31}, "STD": {"OD": 323.8, "WT": 9.53}, "XS": {"OD": 323.8, "WT": 12.70}, "60": {"OD": 323.8, "WT": 14.27}, "80": {"OD": 323.8, "WT": 17.48}, "100": {"OD": 323.8, "WT": 21.44}, "120": {"OD": 323.8, "WT": 25.40}, "140": {"OD": 323.8, "WT": 28.58}, "160": {"OD": 323.8, "WT": 33.32}, "XXS": {"OD": 323.8, "WT": 25.40}}
}

def get_ID(nps, sch):
    if nps in pipe_database and sch in pipe_database[nps]:
        d = pipe_database[nps][sch]
        return d["OD"] - 2 * d["WT"]
    return None

# ==================================================
# SOL SÜTUN: ENGINEERING CALCULATOR (GİRDİLER)
# ==================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3093/3093409.png", width=80)
    st.title("🔧 Engineering Calculator")
    st.markdown("---")

    # Bölüm 1: Proses Verileri (Açılır/Kapanır)
    with st.expander("1. Process Data", expanded=True):
        temp = st.number_input("Temperature (°C)", 120.0, step=1.0)
        pressure = st.number_input("Pressure (bar)", 40.0, step=1.0)
        flow = st.number_input("Mass Flow (t/h)", 100.0, step=5.0)
        length = st.number_input("Pipe Length (m)", 5000.0, step=50.0)

    # Bölüm 2: Boru Seçimi (Açılır/Kapanır)
    with st.expander("2. Pipe Selection", expanded=True):
        material_name = st.selectbox("Material", list(material_list.keys()))
        nps_selected = st.selectbox("Nominal Size (NPS)", list(pipe_database.keys()), index=12)
        
        # Schedule dinamik doluyor
        sch_selected = st.selectbox("Schedule", list(pipe_database[nps_selected].keys()))
        
        current_ID = get_ID(nps_selected, sch_selected)
        st.info(f"📏 ID: {current_ID:.2f} mm")

    # Bölüm 3: Kayıt İşlemi
    with st.expander("3. Save Options", expanded=False):
        project_name = st.text_input("Project Name", "New-Project-01")

    st.markdown("---")
    # Ana Hesapla Butonu (Sidebar'ın en altında)
    calculate_btn = st.button("🚀 CALCULATE & SAVE", type="primary", use_container_width=True)

# ==================================================
# ANA EKRAN: SONUÇLAR VE VERİTABANI
# ==================================================

st.title("📊 Project Dashboard")

# Hesapla butonuna basıldıysa işlemleri yap
if calculate_btn:
    roughness = material_list[material_name]
    ID_mm = current_ID
    
    # Fiziksel Hesaplar
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
        
        # Sonuçları Session State'e kaydet (Sayfa yenilense de kalsın diye)
        st.session_state['result'] = {
            "dp": dP_bar, "vel": velocity, "re": Re, "f": f,
            "rho": rho, "mu": mu, "id": ID_mm
        }

        # Veritabanına Yaz
        conn = sqlite3.connect("project_data.db")
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO projects (name, material, nps, sch, pressure_drop, velocity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (project_name, material_name, nps_selected, sch_selected, dP_bar, velocity))
        conn.commit()
        conn.close()
        
        st.toast("Calculation Saved Successfully!", icon="✅")

    except Exception as e:
        st.error(f"Error: {e}")

# --- SONUÇLARI GÖSTER (Dashboard Kısmı) ---
if 'result' in st.session_state:
    res = st.session_state['result']
    
    # 1. Büyük Kartlar (Metrics)
    st.subheader("Calculation Results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pressure Drop", f"{res['dp']:.4f} bar", delta_color="inverse")
    c2.metric("Velocity", f"{res['vel']:.2f} m/s")
    c3.metric("Reynolds No", f"{res['re']:.0f}")
    c4.metric("Friction Factor", f"{res['f']:.5f}")

    # 2. Detaylı Özellikler (Expander)
    with st.expander("Show Fluid Properties"):
        st.write(f"Density: {res['rho']:.2f} kg/m³ | Viscosity: {res['mu']:.6f} Pa.s | Pipe ID: {res['id']:.2f} mm")

st.markdown("---")

# --- ALT KISIM: VERİTABANI TABLOSU VE GRAFİKLER ---
tab_db, tab_graph = st.tabs(["📂 Project Database (Excel)", "📈 Analysis Graph"])

with tab_db:
    conn = sqlite3.connect("project_data.db")
    df = pd.read_sql("SELECT * FROM projects ORDER BY id DESC", conn)
    conn.close()
    
    # Excel Görünümü
    edited_df = st.data_editor(
        df, hide_index=True, use_container_width=True, num_rows="dynamic",
        column_config={
            "pressure_drop": st.column_config.NumberColumn("Drop (bar)", format="%.4f"),
            "velocity": st.column_config.NumberColumn("Vel (m/s)", format="%.2f"),
            "timestamp": "Date"
        }
    )
    # İndirme Butonu
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download List", csv, "projects.csv", "text/csv")

with tab_graph:
    if st.button("Generate Diameter Comparison Graph"):
        # Grafik için hızlı hesaplama döngüsü (Girdiler Sidebar'dan alınıyor)
        graph_data = []
        try:
            # Sabitleri al
            T_K = temp + 273.15
            P_Pa = pressure * 100000
            m_kg_s = flow * 1000 / 3600
            rho = PropsSI('D', 'T', T_K, 'P', P_Pa, 'Water')
            mu = PropsSI('V', 'T', T_K, 'P', P_Pa, 'Water')
            rough = material_list[material_name]

            for size in pipe_database.keys():
                if sch_selected in pipe_database[size]:
                    d_props = pipe_database[size][sch_selected]
                    cur_ID = d_props['OD'] - 2*d_props['WT']
                    ID_m = cur_ID / 1000
                    area = math.pi * (ID_m/2)**2
                    v = m_kg_s / (rho * area)
                    re = (rho * v * ID_m) / mu
                    
                    if re > 4000:
                        f = (-1.8 * math.log10((rough/1000/ID_m/3.7)**1.11 + 6.9/re))**-2
                    else:
                        f = 64/re if re>0 else 0
                    
                    dp_b = (f * (length/ID_m) * (rho * v**2 / 2)) / 100000
                    if dp_b < 500:
                        graph_data.append({"NPS": size, "Pressure Drop (bar)": dp_b})
            
            df_g = pd.DataFrame(graph_data)
            fig = px.line(df_g, x="NPS", y="Pressure Drop (bar)", markers=True, 
                          title=f"Pressure Drop vs Diameter ({sch_selected})")
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error("Check inputs.")
