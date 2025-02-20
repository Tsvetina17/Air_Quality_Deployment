import streamlit as st
import pandas as pd
import locale
from pathlib import Path
from datetime import datetime, timedelta
from scripts.language_utils import get_text
from scripts.data_handler import get_current_hour_data, get_some_stations, round_to_nearest_hour
from scripts.map_helpers import stations_data, forecast_data
from scripts.prediction import get_highest_aqi

# Get current data of stations and forecast of the stations
data = stations_data
forecast = forecast_data

df_guidelines_en = pd.read_csv(Path(__file__).resolve().parent.parent / 'Dashboard_data' / 'Merged Table Guidelines EN.csv')
df_guidelines_es = pd.read_csv(Path(__file__).resolve().parent.parent / 'Dashboard_data' / 'Merged Table Guidelines ES.csv', encoding='latin1')

def get_index(ind, lang):
    status = {
        
        1: {
            'en': 'Good',
            'es': 'Buena'
        },
        2: {
            'en': 'Acceptable',
            'es': 'Aceptable'
        },
        3: {
            'en': 'Bad',
            'es': 'Mala'
        },
        4: {
            'en': 'Very Bad',
            'es': 'Muy Mala'
        },
        5: {
            'en': 'Extremely Bad',
            'es': 'Extremadamente Mala'
        },
        6: {
            'en': 'No data',
            'es': 'Sin Datos'
        }
        }
    
    return status[ind][lang]

# Set locale to Spanish (replace 'es_MX' with your system's Spanish locale if needed)
locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")  # Use "es_MX.UTF-8" for Mexico-specific locale

# Style the dataframe
def color_risk(val):
    if val == 'Low' or val == 'Bajo':
        return 'color: #00E400'
    elif val == 'Moderate' or val == 'Moderado':
        return 'color: #FFFF00'
    elif val == 'High' or val == 'Alto':
        return 'color: #FF7E00'
    elif val == 'Very High' or val == 'Muy Alto':
        return 'color: #FF0000'
    else:
        return 'color: #8F3F97'

# Style the dataframe
def color_air_quality(val):
    if val == 'Good' or val == 'Buena':
        return 'color: #00E400'
    elif val == 'Acceptable' or val == 'Aceptable':
        return 'color: #FFFF00'
    elif val == 'Bad' or val == 'Mala':
        return 'color: #FF7E00'
    elif val == 'Very bad' or val == 'Muy Mala':
        return 'color: #FF0000'
    else:
        return 'color: #8F3F97'

# Function to get formatted date and time in a specific language
def get_date_time(lang):
    if lang == "en":
        locale.setlocale(locale.LC_TIME, "en_US.UTF-8")  # Set locale to English
    elif lang == "es":
        locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")  # Set locale to Spanish
    else:
        raise ValueError("Unsupported language. Please choose 'English' or 'Spanish'.")

    current_date = datetime.now().strftime("%A %d de %B de %Y")
    formatted_date = current_date.capitalize()
    current_time = datetime.now().strftime("%H:%M")
    return formatted_date, current_time

def information_page():
    lang = st.session_state.language

    selected_station = st.selectbox((get_text('station', lang)).capitalize(), get_some_stations())
    formatted_date, current_time = get_date_time(lang)
    st.markdown(
                f"""
                
                📅 {formatted_date} &nbsp;&nbsp;&nbsp;&nbsp;
                🕒 {current_time} &nbsp;&nbsp;&nbsp;&nbsp; 
                """,
                unsafe_allow_html=True
            )

    # Get the nearest hour
    nearest_hour = round_to_nearest_hour(datetime.now())

    # Get the end hour to be displayed which is three hours from the nearest hour
    end_hour = nearest_hour + timedelta(hours=23)
    
    # Let's get the current levels of the pollutants from all the stations
    list_of_stations = {"PED": "Pedregal",
                    "UIZ": "UAM Iztapalapa",
                    "BJU": "Benito Juarez",
                    "MER": "Merced"}

    # get AQI ranges
    forecast_index = get_highest_aqi(forecast, selected_station, forecast=True)
    
    # Page title and description
    st.title(get_text('information', lang))
    
    # Create two columns for best/worst time cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"🌟 {get_text('best_time', lang)}\n\n"
                "**8:00 - 11:00**\n\n"
                f"{get_text('current_forecast', lang)}: {get_index(forecast_index[0], lang)}")
    
    with col2:
        st.info(f"⚠️ {get_text('worst_time', lang)}\n\n"
                "**14:00 - 17:00**\n\n"
                f"{get_text('current_forecast', lang)}: {get_index(forecast_index[1], lang)}")
    
    # Create two columns for user selection of time and group
    col1, col2 = st.columns(2)
    
    with col1:
        option_time = st.selectbox(get_text('select_time', lang), ("06:00 - 09:00", "09:00 - 12:00", "12:00 - 15:00", "15:00 - 18:00", "18:00 - 21:00", "21:00 - 00:00", "00:00 - 03:00", "03:00 - 06:00"))
        st.write(get_text('selected', lang), option_time)
    
    with col2:
        option_group = st.selectbox(get_text('select_group', lang), (get_text('general_population', lang), get_text('children_and_pregnant', lang), get_text('people_cardiovascular', lang)))
        st.write(get_text('selected', lang), option_group)
    
    # Create the main recommendations table
    st.markdown(f"### {get_text('information_based_on_selection', lang)}")

    # Filter the data according to the selected station and time
    filtered_data = forecast_data[(forecast_data['station'] == selected_station) & (forecast_data['datetime'].dt.hour >= 6) & (forecast_data['datetime'].dt.hour < 9)]
    filtered_data = filtered_data[['datetime', 'AirQualityIndex']]

    # Merge the filtered data with the guidelines data
    merged_data_en = pd.merge(filtered_data, df_guidelines_en, left_on='AirQualityIndex', right_on='Index', how='left')
    merged_data_es = pd.merge(filtered_data, df_guidelines_es, left_on='AirQualityIndex', right_on='Index', how='left')

    # Display the table according to the selected group and language
    if option_group == get_text('general_population', lang) and lang == 'en':
        result = merged_data_en[['datetime', 'Air Quality', 'Risk level', 'Description of risk: General population', 'General population']]
        result.columns = ['Time Period', 'Air Quality', 'Risk level', 'Description of risk', 'Messages']
        
        # Apply styling
        styled_df = result.style.applymap(color_risk, subset=['Risk level']).applymap(color_air_quality, subset=['Air Quality'])
        st.table(styled_df)

    if option_group == get_text('children_and_pregnant', lang) and lang == 'en':
        result = merged_data_en[['datetime', 'Air Quality', 'Risk level', 'Description of risk: Sensitive Population', 'Children under 12 years old and pregnant people']]
        result.columns = ['Time Period', 'Air Quality', 'Risk level', 'Description of risk', 'Messages']
        
        # Apply styling
        styled_df = result.style.applymap(color_risk, subset=['Risk level']).applymap(color_air_quality, subset=['Air Quality'])
        st.table(styled_df)

    if option_group == get_text('people_cardiovascular', lang) and lang == 'en':
        result = merged_data_en[['datetime', 'Air Quality', 'Risk level', 'Description of risk: Sensitive Population', 'People with cardiovascular or respiratory diseases and those over 60 years of age']]
        result.columns = ['Time Period', 'Air Quality', 'Risk level', 'Description of risk', 'Messages']
        
        # Apply styling
        styled_df = result.style.applymap(color_risk, subset=['Risk level']).applymap(color_air_quality, subset=['Air Quality'])
        st.table(styled_df)

    if option_group == get_text('general_population', lang) and lang == 'es':
        result_es = merged_data_es[['datetime', 'Air Quality', 'Risk level', 'Description of risk: General population', 'General population']]
        result_es.columns = ['Hora', 'Calidad del aire', 'Nivel de riesgo', 'Descripción del riesgo', 'Mensajes']
        
        # Apply styling
        styled_df_es = result_es.style.applymap(color_risk, subset=['Nivel de riesgo']).applymap(color_air_quality, subset=['Calidad del aire'])
        st.table(styled_df_es)

    if option_group == get_text('children_and_pregnant', lang) and lang == 'es':
        result_es = merged_data_es[['datetime', 'Air Quality', 'Risk level', 'Description of risk: Sensitive Population', 'Children under 12 years old and pregnant people']]
        result_es.columns = ['Hora', 'Calidad del aire', 'Nivel de riesgo', 'Descripción del riesgo', 'Mensajes']
        
        # Apply styling
        styled_df_es = result_es.style.applymap(color_risk, subset=['Nivel de riesgo']).applymap(color_air_quality, subset=['Calidad del aire'])
        st.table(styled_df_es)

    if option_group == get_text('people_cardiovascular', lang) and lang == 'es':
        result_es = merged_data_es[['datetime', 'Air Quality', 'Risk level', 'Description of risk: Sensitive Population', 'People with cardiovascular or respiratory diseases and those over 60 years of age']]
        result_es.columns = ['Hora', 'Calidad del aire', 'Nivel de riesgo', 'Descripción del riesgo', 'Mensajes']
        
        # Apply styling
        styled_df_es = result_es.style.applymap(color_risk, subset=['Nivel de riesgo']).applymap(color_air_quality, subset=['Calidad del aire'])
        st.table(styled_df_es)

    
    # Add explanatory notes
    st.markdown(get_text('notes', lang))



if __name__ == "__main__":
    st.set_page_config(
        page_title="Information",
        page_icon="🌎",
        layout="wide"
    )
    information_page()