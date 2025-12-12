import streamlit as st
from CoolProp.CoolProp import PropsSI
import math
import plotly.express as px

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="HydraulicCalc Pro",
    page_icon="💧",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. TAM KAPSAMLI BORU VERİTABANI (PDF'ten Alınan Veriler) ---
pipe_database = {
    "1/8 inch": {
        "10": {"OD": 10.3, "WT": 1.24}, "30": {"OD": 10.3, "WT": 1.45}, "40": {"OD": 10.3, "WT": 1.73}, 
        "STD": {"OD": 10.3, "WT": 1.73}, "80": {"OD": 10.3, "WT": 2.41}, "XS": {"OD": 10.3, "WT": 2.41}
    },
    "1/4 inch": {
        "10": {"OD": 13.7, "WT": 1.65}, "30": {"OD": 13.7, "WT": 1.85}, "40": {"OD": 13.7, "WT": 2.24}, 
        "STD": {"OD": 13.7, "WT": 2.24}, "80": {"OD": 13.7, "WT": 3.02}, "XS": {"OD": 13.7, "WT": 3.02}
    },
    "3/8 inch": {
        "10": {"OD": 17.1, "WT": 1.65}, "30": {"OD": 17.1, "WT": 1.85}, "40": {"OD": 17.1, "WT": 2.31}, 
        "STD": {"OD": 17.1, "WT": 2.31}, "80": {"OD": 17.1, "WT": 3.20}, "XS": {"OD": 17.1, "WT": 3.20}
    },
    "1/2 inch": {
        "5": {"OD": 21.3, "WT": 1.65}, "10": {"OD": 21.3, "WT": 2.11}, "30": {"OD": 21.3, "WT": 2.41}, 
        "40": {"OD": 21.3, "WT": 2.77}, "STD": {"OD": 21.3, "WT": 2.77}, "80": {"OD": 21.3, "WT": 3.73}, 
        "XS": {"OD": 21.3, "WT": 3.73}, "160": {"OD": 21.3, "WT": 4.78}, "XXS": {"OD": 21.3, "WT": 7.47}
    },
    "3/4 inch": {
        "5": {"OD": 26.7, "WT": 1.65}, "10": {"OD": 26.7, "WT": 2.11}, "30": {"OD": 26.7, "WT": 2.41}, 
        "40": {"OD": 26.7, "WT": 2.87}, "STD": {"OD": 26.7, "WT": 2.87}, "80": {"OD": 26.7, "WT": 3.91}, 
        "XS": {"OD": 26.7, "WT": 3.91}, "160": {"OD": 26.7, "WT": 5.56}, "XXS": {"OD": 26.7, "WT": 7.82}
    },
    "1 inch": {
        "5": {"OD": 33.4, "WT": 1.65}, "10": {"OD": 33.4, "WT": 2.77}, "30": {"OD": 33.4, "WT": 2.90}, 
        "40": {"OD": 33.4, "WT": 3.38}, "STD": {"OD": 33.4, "WT": 3.38}, "80": {"OD": 33.4, "WT": 4.55}, 
        "XS": {"OD": 33.4, "WT": 4.55}, "160": {"OD": 33.4, "WT": 6.35}, "XXS": {"OD": 33.4, "WT": 9.09}
    },
    "1 1/4 inch": {
        "5": {"OD": 42.2, "WT": 1.65}, "10": {"OD": 42.2, "WT": 2.77}, "30": {"OD": 42.2, "WT": 2.97}, 
        "40": {"OD": 42.2, "WT": 3.56}, "STD": {"OD": 42.2, "WT": 3.56}, "80": {"OD": 42.2, "WT": 4.85}, 
        "XS": {"OD": 42.2, "WT": 4.85}, "160": {"OD": 42.2, "WT": 6.35}, "XXS": {"OD": 42.2, "WT": 9.70}
    },
    "1 1/2 inch": {
        "5": {"OD": 48.3, "WT": 1.65}, "10": {"OD": 48.3, "WT": 2.77}, "30": {"OD": 48.3, "WT": 3.18}, 
        "40": {"OD": 48.3, "WT": 3.68}, "STD": {"OD": 48.3, "WT": 3.68}, "80": {"OD": 48.3, "WT": 5.08}, 
        "XS": {"OD": 48.3, "WT": 5.08}, "160": {"OD": 48.3, "WT": 7.14}, "XXS": {"OD": 48.3, "WT": 10.15}
    },
    "2 inch": {
        "5": {"OD": 60.3, "WT": 1.65}, "10": {"OD": 60.3, "WT": 2.77}, "30": {"OD": 60.3, "WT": 3.18}, 
        "40": {"OD": 60.3, "WT": 3.91}, "STD": {"OD": 60.3, "WT": 3.91}, "80": {"OD": 60.3, "WT": 5.54}, 
        "XS": {"OD": 60.3, "WT": 5.54}, "160": {"OD": 60.3, "WT": 8.74}, "XXS": {"OD": 60.3, "WT": 11.07}
    },
    "2 1/2 inch": {
        "5": {"OD": 73.0, "WT": 2.11}, "10": {"OD": 73.0, "WT": 3.05}, "30": {"OD": 73.0, "WT": 4.78}, 
        "40": {"OD": 73.0, "WT": 5.16}, "STD": {"OD": 73.0, "WT": 5.16}, "80": {"OD": 73.0, "WT": 7.01}, 
        "XS": {"OD": 73.0, "WT": 7.01}, "160": {"OD": 73.0, "WT": 9.53}, "XXS": {"OD": 73.0, "WT": 14.02}
    },
    "3 inch": {
        "5": {"OD": 88.9, "WT": 2.11}, "10": {"OD": 88.9, "WT": 3.05}, "30": {"OD": 88.9, "WT": 4.78}, 
        "40": {"OD": 88.9, "WT": 5.49}, "STD": {"OD": 88.9, "WT": 5.49}, "80": {"OD": 88.9, "WT": 7.62}, 
        "XS": {"OD": 88.9, "WT": 7.62}, "160": {"OD": 88.9, "WT": 11.13}, "XXS": {"OD": 88.9, "WT": 15.24}
    },
    "3 1/2 inch": {
        "5": {"OD": 101.6, "WT": 2.11}, "10": {"OD": 101.6, "WT": 3.05}, "30": {"OD": 101.6, "WT": 4.78}, 
        "40": {"OD": 101.6, "WT": 6.02}, "STD": {"OD": 101.6, "WT": 6.02}, "80": {"OD": 101.6, "WT": 8.08}, 
        "XS": {"OD": 101.6, "WT": 8.08}
    },
    "4 inch": {
        "5": {"OD": 114.3, "WT": 2.11}, "10": {"OD": 114.3, "WT": 3.05}, "30": {"OD": 114.3, "WT": 4.78}, 
        "40": {"OD": 114.3, "WT": 6.02}, "STD": {"OD": 114.3, "WT": 6.02}, "80": {"OD": 114.3, "WT": 8.56}, 
        "XS": {"OD": 114.3, "WT": 8.56}, "120": {"OD": 114.3, "WT": 11.13}, "160": {"OD": 114.3, "WT": 13.49}, 
        "XXS": {"OD": 114.3, "WT": 17.12}
    },
    "5 inch": {
        "5": {"OD": 141.3, "WT": 2.77}, "10": {"OD": 141.3, "WT": 3.40}, "40": {"OD": 141.3, "WT": 6.55}, 
        "STD": {"OD": 141.3, "WT": 6.55}, "80": {"OD": 141.3, "WT": 9.53}, "XS": {"OD": 141.3, "WT": 9.53}, 
        "120": {"OD": 141.3, "WT": 12.70}, "160": {"OD": 141.3, "WT": 15.88}, "XXS": {"OD": 141.3, "WT": 19.05}
    },
    "6 inch": {
        "5": {"OD": 168.3, "WT": 2.77}, "10": {"OD": 168.3, "WT": 3.40}, "40": {"OD": 168.3, "WT": 7.11}, 
        "STD": {"OD": 168.3, "WT": 7.11}, "80": {"OD": 168.3, "WT": 10.97}, "XS": {"OD": 168.3, "WT": 10.97}, 
        "120": {"OD": 168.3, "WT": 14.27}, "160": {"OD": 168.3, "WT": 18.26}, "XXS": {"OD": 168.3, "WT": 21.95}
    },
    "8 inch": {
        "5": {"OD": 219.1, "WT": 2.77}, "10": {"OD": 219.1, "WT": 3.76}, "20": {"OD": 219.1, "WT": 6.35}, 
        "30": {"OD": 219.1, "WT": 7.04}, "40": {"OD": 219.1, "WT": 8.18}, "STD": {"OD": 219.1, "WT": 8.18}, 
        "60": {"OD": 219.1, "WT": 10.31}, "80": {"OD": 219.1, "WT": 12.70}, "XS": {"OD": 219.1, "WT": 12.70}, 
        "100": {"OD": 219.1, "WT": 15.09}, "120": {"OD": 219.1, "WT": 18.26}, "140": {"OD": 219.1, "WT": 20.62}, 
        "160": {"OD": 219.1, "WT": 23.01}, "XXS": {"OD": 219.1, "WT": 22.23}
    },
    "10 inch": {
        "5": {"OD": 273.0, "WT": 3.40}, "10": {"OD": 273.0, "WT": 4.19}, "20": {"OD": 273.0, "WT": 6.35}, 
        "30": {"OD": 273.0, "WT": 7.80}, "40": {"OD": 273.0, "WT": 9.27}, "STD": {"OD": 273.0, "WT": 9.27}, 
        "60": {"OD": 273.0, "WT": 12.70}, "XS": {"OD": 273.0, "WT": 12.70}, "80": {"OD": 273.0, "WT": 15.09}, 
        "100": {"OD": 273.0, "WT": 18.26}, "120": {"OD": 273.0, "WT": 21.44}, "140": {"OD": 273.0, "WT": 25.40}, 
        "XXS": {"OD": 273.0, "WT": 25.40}, "160": {"OD": 273.0, "WT": 28.58}
    },
    "12 inch": {
        "5": {"OD": 323.8, "WT": 3.96}, "10": {"OD": 323.8, "WT": 4.57}, "20": {"OD": 323.8, "WT": 6.35}, 
        "30": {"OD": 323.8, "WT": 8.38}, "STD": {"OD": 323.8, "WT": 9.53}, "40": {"OD": 323.8, "WT": 10.31}, 
        "XS": {"OD": 323.8, "WT": 12.70}, "60": {"OD": 323.8, "WT": 14.27}, "80": {"OD": 323.8, "WT": 17.48}, 
        "100": {"OD": 323.8, "WT": 21.44}, "120": {"OD": 323.8, "WT": 25.40}, "XXS": {"OD": 323.8, "WT": 25.40}, 
        "140": {"OD": 323.8, "WT": 28.58}, "160": {"OD": 323.8, "WT": 33.32}
    }
}

material_list = {
    "Karbon Çelik (Carbon Steel)": 0.045, "Paslanmaz Çelik (Stainless Steel)": 0.0015,
    "Bakır (Copper)": 0.0015, "PVC": 0.0015, "Beton (Concrete)": 0.01, "Galvanizli Çelik": 0.15
}

def get_ID(nps, sch):
    if nps in pipe_database and sch in pipe_database[nps]:
        d = pipe_database[nps][sch]
        return d["OD"] - 2 * d["WT"]
    return None

# --- 3. ARAYÜZ (GİRDİLER) ---
st.title("💧 Basınç Kaybı Hesaplayıcı")
st.markdown("---")

st.subheader("1. Proses Verileri")
col1, col2 = st.columns(2)
with col1:
    temp = st.number_input("Sıcaklık (°C)", value=120.0, step=1.0)
    flow = st.number_input("Kütlesel Debi (t/h)", value=100.0, step=10.0)
with col2:
    pressure = st.number_input("Basınç (bar)", value=40.0, step=1.0)
    length = st.number_input("Boru Uzunluğu (m)", value=5000.0, step=50.0)

st.subheader("2. Boru Özellikleri")
col3, col4 = st.columns(2)
with col3:
    material_name = st.selectbox("Malzeme Seçin", list(material_list.keys()))
    nps_selected = st.selectbox("Nominal Çap (NPS)", list(pipe_database.keys()), index=12) # Varsayılan 4 inch

with col4:
    available_schedules = list(pipe_database[nps_selected].keys())
    sch_selected = st.selectbox("Schedule (Et Kalınlığı)", available_schedules)
    
    current_ID = get_ID(nps_selected, sch_selected)
    
    # KULLANICI KONTROLÜ İÇİN EK BİLGİ (DEBUG)
    if nps_selected in pipe_database and sch_selected in pipe_database[nps_selected]:
        d_info = pipe_database[nps_selected][sch_selected]
        st.info(f"📋 Seçilen: {nps_selected} - {sch_selected} | OD: {d_info['OD']} mm | WT: {d_info['WT']} mm")
    
    st.success(f"Hesaplanan İç Çap (ID): **{current_ID:.2f} mm**")

# --- 4. HESAPLAMA MOTORU ---
st.markdown("---")
if st.button("🚀 HESAPLA", type="primary", use_container_width=True):
    roughness = material_list[material_name]
    ID_mm = current_ID
    
    T_kelvin = temp + 273.15
    P_pascal = pressure * 100000
    m_dot_kg_s = flow * 1000 / 3600
    ID_m = ID_mm / 1000
    
    try:
        rho = PropsSI('D', 'T', T_kelvin, 'P', P_pascal, 'Water')
        mu = PropsSI('V', 'T', T_kelvin, 'P', P_pascal, 'Water')
        
        Area = math.pi * (ID_m / 2)**2
        velocity = m_dot_kg_s / (rho * Area)
        Re = (rho * velocity * ID_m) / mu
        
        if Re > 4000:
            f = (-1.8 * math.log10((roughness/1000/ID_m/3.7)**1.11 + 6.9/Re))**-2
        elif Re > 0:
            f = 64 / Re
        else:
            f = 0
            
        dP_pascal = f * (length / ID_m) * (rho * velocity**2 / 2)
        dP_bar = dP_pascal / 100000
        
        st.success("Hesaplama Başarıyla Tamamlandı!")
        
        res1, res2, res3, res4 = st.columns(4)
        res1.metric("Basınç Kaybı", f"{dP_bar:.4f} bar", delta_color="inverse")
        res2.metric("Akış Hızı", f"{velocity:.2f} m/s")
        res3.metric("Reynolds Sayısı", f"{Re:.0f}")
        res4.metric("Sürtünme Faktörü", f"{f:.5f}")
        
        with st.expander("Detaylı Akışkan Özellikleri"):
            st.write(f"- **Yoğunluk:** {rho:.2f} kg/m³")
            st.write(f"- **Viskozite:** {mu:.6f} Pa.s")
            st.write(f"- **Akış Alanı:** {Area:.6f} m²")

    except Exception as e:
        st.error(f"Hesaplama Hatası: {e}")
