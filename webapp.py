import streamlit as st
from CoolProp.CoolProp import PropsSI
import math

# --- 1. SAYFA AYARLARI ---
st.set_page_config(
    page_title="HydraulicCalc Pro",
    page_icon="⚙️",
    layout="centered", # 'wide' yerine 'centered' yaptım, form gibi ortada dursun
    initial_sidebar_state="collapsed"
)

# --- 2. VERİTABANI (Sözlükler) ---
# Malzeme Pürüzlülükleri (mm)
material_list = {
    "Carbon Steel": 0.045,
    "Stainless Steel": 0.0015,
    "Copper": 0.0015,
    "PVC": 0.0015,
    "Concrete": 0.01,
    "Galvanised Steel": 0.15
}

# Boru Çapları Veritabanı (Örnek veriler)
pipe_database = {
    "1/2 inch": {"40": {"OD": 21.3, "WT": 2.77}, "80": {"OD": 21.3, "WT": 3.73}},
    "1 inch":   {"40": {"OD": 33.4, "WT": 3.38}, "80": {"OD": 33.4, "WT": 4.55}},
    "2 inch":   {"40": {"OD": 60.3, "WT": 3.91}, "80": {"OD": 60.3, "WT": 5.54}},
    "3 inch":   {"40": {"OD": 88.9, "WT": 5.49}, "80": {"OD": 88.9, "WT": 7.62}},
    "4 inch":   {"40": {"OD": 114.3, "WT": 6.02}, "80": {"OD": 114.3, "WT": 8.56}},
    "6 inch":   {"40": {"OD": 168.3, "WT": 7.11}, "80": {"OD": 168.3, "WT": 10.97}},
    "8 inch":   {"40": {"OD": 219.1, "WT": 8.18}, "80": {"OD": 219.1, "WT": 12.70}},
    "10 inch":  {"40": {"OD": 273.0, "WT": 9.27}, "80": {"OD": 273.0, "WT": 15.09}},
    "12 inch":  {"STD": {"OD": 323.8, "WT": 9.53}, "XS": {"OD": 323.8, "WT": 12.70}}
}

# Yardımcı Fonksiyon: İç Çap Bulucu
def get_ID(nps, sch):
    if nps in pipe_database and sch in pipe_database[nps]:
        d = pipe_database[nps][sch]
        return d["OD"] - 2 * d["WT"]
    return None

# --- 3. ARAYÜZ TASARIMI (GİRDİLER) ---
st.title("💧 Pressure Loss Calculator")
st.markdown("---") # Çizgi çeker

st.subheader("1. Process Data")
# Girdileri yan yana 2 kolona bölüyoruz
col1, col2 = st.columns(2)

with col1:
    temp = st.number_input("Temperature (°C)", value=120.0, step=1.0)
    flow = st.number_input("Mass Flow Rate (t/h)", value=100.0, step=10.0)

with col2:
    pressure = st.number_input("Basınç (bar)", value=40.0, step=1.0)
    length = st.number_input("Boru Uzunluğu (m)", value=5000.0, step=50.0)

st.subheader("2. Pipe Specifications")
col3, col4 = st.columns(2)

with col3:
    material_name = st.selectbox("Choose Material", list(material_list.keys()))
    # Seçilen NPS'ye göre Schedule listesini güncellemek için önce NPS'yi alıyoruz
    nps_selected = st.selectbox("Nominal Diameter (NPS)", list(pipe_database.keys()), index=4) # Varsayılan 4 inch

with col4:
    # Schedule kutusu, seçilen çapa göre otomatik doluyor
    available_schedules = list(pipe_database[nps_selected].keys())
    sch_selected = st.selectbox("Schedule ", available_schedules)
    
    # Bilgi amaçlı seçilen boruyu gösterelim
    current_ID = get_ID(nps_selected, sch_selected)
    st.info(f"ID: **{current_ID:.2f} mm**")

# --- 4. HESAPLAMA MOTORU ---
st.markdown("---")
# Butonu ortalamak için boş kolonlar kullanabiliriz veya direkt basabiliriz
if st.button("CALCULATE", type="primary", use_container_width=True):
    
    # Verileri Hazırla
    roughness = material_list[material_name]
    ID_mm = current_ID
    
    # Fiziksel Dönüşümler
    T_kelvin = temp + 273.15
    P_pascal = pressure * 100000
    m_dot_kg_s = flow * 1000 / 3600
    ID_m = ID_mm / 1000
    
    try:
        # CoolProp ile Özellikleri Çek
        rho = PropsSI('D', 'T', T_kelvin, 'P', P_pascal, 'Water') # Yoğunluk
        mu = PropsSI('V', 'T', T_kelvin, 'P', P_pascal, 'Water')  # Viskozite
        
        # Hidrolik Hesaplar
        Area = math.pi * (ID_m / 2)**2
        velocity = m_dot_kg_s / (rho * Area)
        Re = (rho * velocity * ID_m) / mu
        
        # Sürtünme Faktörü (Colebrook-White Yaklaşımı)
        if Re > 4000:
            # Türbülanslı Akış
            f = (-1.8 * math.log10((roughness/1000/ID_m/3.7)**1.11 + 6.9/Re))**-2
        elif Re > 0:
            # Laminar Akış
            f = 64 / Re
        else:
            f = 0
            
        # Basınç Kaybı (Darcy-Weisbach)
        dP_pascal = f * (length / ID_m) * (rho * velocity**2 / 2)
        dP_bar = dP_pascal / 100000
        
        # --- SONUÇLARI GÖSTER ---
        st.success("Calculation Successfully Completed!")
        
        # Sonuçları 4'lü kartlar halinde gösterelim
        res1, res2, res3, res4 = st.columns(4)
        
        res1.metric("Pressure Loss", f"{dP_bar:.1f} bar", delta_color="inverse")
        res2.metric("Fluid Velocity", f"{velocity:.2f} m/s")
        res3.metric("Reynolds Number", f"{Re:.0f}")
        res4.metric("Fraction Factor", f"{f:.5f}")
        
        # Detaylar için genişletilebilir alan
        with st.expander("Detailed Fluid Properties"):
            st.write(f"- **Density:** {rho:.2f} kg/m³")
            st.write(f"- **Viscosity:** {mu:.6f} Pa.s")
            st.write(f"- **Area:** {Area:.6f} m²")

    except Exception as e:
        st.error(f"Calculation Error: {e}")
