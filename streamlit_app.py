import streamlit as st
import pvlib
import pandas as pd
import matplotlib.pyplot as plt

st.title('Modelos de Decomposição de Irradiância Solar')
st.write('Este portal compara diferentes modelos matemáticos de decomposição de irradiância.')

@st.cache_data
def load_data():
    # Location
    latitude = 44.0446
    longitude = -123.0726
    altitude = 123.0
    loc = pvlib.location.Location(latitude, longitude, altitude=altitude, tz='Etc/GMT+8')

    # In-Field Data (Reduzido para 10 dias para ser mais rápido no portal)
    df_weather = pvlib.iotools.read_midc_raw_data_from_nrel('UOSMRL', 
                                                    pd.Timestamp('20210120'), 
                                                    pd.Timestamp('20210130'))

    df_weather = df_weather[['Global CMP22 [W/m^2]', 'Diffuse [W/m^2]',
                             'Direct CHP1 [W/m^2]','Air Temperature [deg C]', 'Avg Wind Speed @ 10m [m/s]', 'Station Pressure [mBar]', 
                             'Zenith Angle [degrees]']]
    # Rename the columns
    df_weather.columns = ['ghi', 'dhi', 'dni', 'temp_air', 'wind_speed', 'air_pressure', 'teta_z']
    df_weather = df_weather.resample('h').mean().copy()
    
    # Decomposition Models
    solpos = loc.get_solarposition(df_weather.index)
    clearsky = loc.get_clearsky(df_weather.index, model='ineichen', solar_position=solpos)
    dni_extra = pvlib.irradiance.get_extra_radiation(df_weather.index)

    # Aplicar os modelos
    out_erbs = pvlib.irradiance.erbs(df_weather['ghi'], solpos['zenith'], df_weather.index)
    out_erbs = out_erbs.rename(columns={'dni': 'dni_erbs', 'dhi': 'dhi_erbs'})

    out_disc = pvlib.irradiance.disc(df_weather['ghi'], solpos.zenith, df_weather.index, df_weather['air_pressure']*100)
    out_disc = out_disc.rename(columns={'dni': 'dni_disc'})

    return df_weather, out_erbs, out_disc

with st.spinner("A transferir dados meteorológicos do NREL..."):
    df_weather, out_erbs, out_disc = load_data()

st.success("Dados carregados com sucesso!")

# Gráfico 1: GHI
st.subheader("GHI Medido (W/m²)")
fig1, ax1 = plt.subplots(figsize=(10, 4))
ax1.plot(df_weather.index, df_weather['ghi'], label='Measured GHI', color='black', linewidth=2)
ax1.set_xlabel('Data')
ax1.set_ylabel('GHI (W/m²)')
ax1.legend()
ax1.grid()
st.pyplot(fig1)

# Gráfico 2: Comparação DNI
st.subheader("Comparação de Modelos - DNI (W/m²)")
fig2, ax2 = plt.subplots(figsize=(10, 4))
ax2.plot(df_weather.index, df_weather['dni'], label='Measured DNI', color='black', linewidth=2)
ax2.plot(out_erbs.index, out_erbs['dni_erbs'], label='ERBS', linestyle='--')
ax2.plot(out_disc.index, out_disc['dni_disc'], label='DISC', linestyle='--')
ax2.set_xlabel('Data')
ax2.set_ylabel('DNI (W/m²)')
ax2.legend()
ax2.grid()
st.pyplot(fig2)
