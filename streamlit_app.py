import streamlit as st
import pvlib
import pandas as pd
import matplotlib.pyplot as plt

# Configuração da página para ficar mais larga (estilo dashboard)
st.set_page_config(page_title="Portal Solar", layout="wide")

st.title('☀️ Portal de Decomposição de Irradiância Solar')
st.write('Use o menu lateral esquerdo para escolher o período e interagir com os dados meteorológicos.')

# ----------------- MENU LATERAL (SIDEBAR) -----------------
st.sidebar.header("⚙️ Parâmetros de Entrada")
st.sidebar.write("Selecione o período de análise:")

# Seletores de data (padrão configurado para a janela do seu código original)
data_inicio = st.sidebar.date_input("Data de Início", pd.to_datetime('2021-01-20'))
data_fim = st.sidebar.date_input("Data Final", pd.to_datetime('2021-01-30'))

# Botão de ação
calcular = st.sidebar.button("Gerar Análise")
# ----------------------------------------------------------

@st.cache_data
def load_data(start, end):
    latitude = 44.0446
    longitude = -123.0726
    altitude = 123.0
    loc = pvlib.location.Location(latitude, longitude, altitude=altitude, tz='Etc/GMT+8')

    # Puxa os dados com base nas datas que o usuário escolheu no menu
    df_weather = pvlib.iotools.read_midc_raw_data_from_nrel(
        'UOSMRL', pd.Timestamp(start), pd.Timestamp(end)
    )

    df_weather = df_weather[['Global CMP22 [W/m^2]', 'Diffuse [W/m^2]',
                             'Direct CHP1 [W/m^2]','Air Temperature [deg C]', 
                             'Avg Wind Speed @ 10m [m/s]', 'Station Pressure [mBar]', 
                             'Zenith Angle [degrees]']]
    
    df_weather.columns = ['ghi', 'dhi', 'dni', 'temp_air', 'wind_speed', 'air_pressure', 'teta_z']
    df_weather = df_weather.resample('h').mean().copy()
    
    solpos = loc.get_solarposition(df_weather.index)
    
    out_erbs = pvlib.irradiance.erbs(df_weather['ghi'], solpos['zenith'], df_weather.index)
    out_erbs = out_erbs.rename(columns={'dni': 'dni_erbs', 'dhi': 'dhi_erbs'})

    out_disc = pvlib.irradiance.disc(df_weather['ghi'], solpos.zenith, df_weather.index, df_weather['air_pressure']*100)
    out_disc = out_disc.rename(columns={'dni': 'dni_disc'})

    return df_weather, out_erbs, out_disc

# Lógica principal: só calcula se o botão for clicado ou se for a primeira vez
if calcular or 'dados_carregados' not in st.session_state:
    st.session_state['dados_carregados'] = True
    
    with st.spinner("A conectar com a base do NREL e processar algoritmos..."):
        try:
            df_weather, out_erbs, out_disc = load_data(data_inicio, data_fim)
            st.success("✅ Dados processados com sucesso!")
            
            # Dividindo a tela em duas colunas para os gráficos ficarem lado a lado
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("GHI Medido (W/m²)")
                fig1, ax1 = plt.subplots(figsize=(8, 4))
                ax1.plot(df_weather.index, df_weather['ghi'], label='Measured GHI', color='black', linewidth=2)
                ax1.set_xlabel('Data')
                ax1.set_ylabel('GHI (W/m²)')
                ax1.legend()
                ax1.grid(True, linestyle='--', alpha=0.6)
                st.pyplot(fig1)

            with col2:
                st.subheader("Comparação de Modelos - DNI (W/m²)")
                fig2, ax2 = plt.subplots(figsize=(8, 4))
                ax2.plot(df_weather.index, df_weather['dni'], label='Measured DNI', color='black', linewidth=2)
                ax2.plot(out_erbs.index, out_erbs['dni_erbs'], label='ERBS', linestyle='--')
                ax2.plot(out_disc.index, out_disc['dni_disc'], label='DISC', linestyle='--')
                ax2.set_xlabel('Data')
                ax2.set_ylabel('DNI (W/m²)')
                ax2.legend()
                ax2.grid(True, linestyle='--', alpha=0.6)
                st.pyplot(fig2)
                
        except Exception as e:
            st.error(f"Erro ao buscar os dados. Verifique se o intervalo de datas é válido. Detalhe técnico: {e}")
