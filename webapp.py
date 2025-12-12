import streamlit as st
from CoolProp.CoolProp import PropsSI
import math

# Sayfa Başlığı
st.title("💧 Basınç Kaybı Hesaplayıcı ")

# Sidebar (Sol Menü) - Girdiler buraya
st.sidebar.header("Input")

# Tkinter'daki Entry -> st.number_input
temp = st.sidebar.number_input("Sıcaklık (°C)", value=120.0)
pressure = st.sidebar.number_input("Basınç (bar)", value=40.0)
flow = st.sidebar.number_input("Kütlesel Debi (t/h)", value=100.0)
length = st.sidebar.number_input("Boru Uzunluğu (m)", value=5000.0)

# Tkinter'daki Combobox -> st.selectbox
material = st.sidebar.selectbox(
    "Malzeme Seçin",
    ["carbon steel", "stainless steel", "copper", "PVC"]
)

# Hesaplama Butonu
if st.button("HESAPLA"):
    # --- Senin Mühendislik Kodların Burada Çalışacak ---
    # Arka plandaki matematik AYNI kalıyor!
    
    # 1. Birim Çevirme
    T_kelvin = temp + 273.15
    P_pascal = pressure * 100000
    
    # 2. CoolProp Çağırma
    try:
        rho = PropsSI('D', 'T', T_kelvin, 'P', P_pascal, 'Water')
        visc = PropsSI('V', 'T', T_kelvin, 'P', P_pascal, 'Water')
        
        # 3. Sonuçları Ekrana Yazma
        st.success("Hesaplama Başarılı!")
        
        # Sonuçları sütunlar halinde gösterelim
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Yoğunluk (kg/m³)", f"{rho:.2f}")
        with col2:
            st.metric("Viskozite (Pa.s)", f"{visc:.6f}")
            
    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")
            
    except Exception as e:

        st.error(f"Bir hata oluştu: {e}")
