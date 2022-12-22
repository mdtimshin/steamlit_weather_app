import requests
import streamlit as st
import pandas as pd
import plost
from dotenv import load_dotenv
import os
import datetime
import numpy as np

load_dotenv()
ORS_API_KEY = os.getenv('ORS_API_KEY')


@st.cache
def geocode(query):
    parameters = {
        'api_key': ORS_API_KEY,
        'text': query
    }

    response = requests.get(
        'https://api.openrouteservice.org/geocode/search',
        params=parameters)
    if response.status_code == 200:
        data = response.json()
        if data['features']:
            x, y = data['features'][0]['geometry']['coordinates']
            return y, x


@st.cache
def get_weather(parameters):
    response = requests.get(
        'https://api.open-meteo.com/v1/forecast',
        params=parameters
    )
    if response.status_code == 200:
        data = response.json()
        return data


st.set_page_config(layout='wide', initial_sidebar_state='expanded')

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

address = st.text_input('Введите адрес.')

if address:
    results = geocode(address)
    if results:
        latitude, longtitude = results
        today = datetime.datetime.today().strftime('%Y-%m-%d')
        day_after_week = (datetime.datetime.today() + datetime.timedelta(days=14)).strftime('%Y-%m-%d')
        parameters = {
            'latitude': latitude,
            'longitude': longtitude,
            'current_weather': True,
            'windspeed_unit': 'ms',
            'timezone': 'auto',
            'hourly': ['relativehumidity_2m',
                       'temperature_2m',
                       'pressure_msl',
                       'precipitation',
                       'windspeed_10m',
                       'windspeed_80m',
                       'windspeed_120m',
                       'windspeed_180m'],
            'start_date': (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
            'end_date': day_after_week
        }
        weather = get_weather(parameters=parameters)
        current_temperature = weather['current_weather']['temperature']
        # current_wind_speed = weather['current_weather']['windspeed']

        df = pd.DataFrame()
        df['Дата'] = weather['hourly']['time']
        df['День'] = df['Дата'].str[-8:-6]
        df['Час'] = df['Дата'].str[-9:].str[-5:].str[:2]
        df['Относительная влажность'] = weather['hourly']['relativehumidity_2m']
        df['Температура'] = weather['hourly']['temperature_2m']
        df['Давление'] = weather['hourly']['pressure_msl']
        df['Осадки'] = weather['hourly']['precipitation']
        df['Скорость ветра'] = weather['hourly']['windspeed_10m']
        df['Скорость ветра 10м'] = weather['hourly']['windspeed_10m']
        df['Скорость ветра 80м'] = weather['hourly']['windspeed_80m']
        df['Скорость ветра 120м'] = weather['hourly']['windspeed_120m']
        df['Скорость ветра 180м'] = weather['hourly']['windspeed_180m']

        current_time = datetime.datetime.now().strftime("%H:%M")
        current_date = datetime.datetime.now().replace(microsecond=0, second=0).isoformat()
        result_df = df.loc[df['Дата'] == str(current_date)[:-5] + '00']
        current_relativehumidity = result_df['Относительная влажность'].iloc[0]
        current_wind_speed = result_df['Скорость ветра'].iloc[0]

        result_df_index = result_df.index[0]
        last_df_index = result_df_index - 1
        last_temperature = df.iloc[[last_df_index]]['Температура'].iloc[0]
        last_wind_speed = df.iloc[[last_df_index]]['Скорость ветра'].iloc[0]
        last_relativehumidity = df.iloc[[last_df_index]]['Относительная влажность'].iloc[0]






        # region sidebar
        st.sidebar.header('Прогноз погоды')

        st.sidebar.subheader('Параметр для тепловой карты')
        time_hist_color = st.sidebar.selectbox('Красить по', ('Относительная влажность', 'Температура', 'Давление', 'Осадки', 'Скорость ветра'))

        st.sidebar.subheader('Параметр для кольцевой диаграммы')
        donut_theta = st.sidebar.selectbox('Выбрать данные', ('Скорость ветра 10м', 'Скорость ветра 80м', 'Скорость ветра 120м', 'Скорость ветра 180м'))

        st.sidebar.subheader('Параметр для графика')
        plot_data = st.sidebar.multiselect('Выбрать данные', ['Относительная влажность', 'Температура', 'Давление', 'Осадки', 'Скорость ветра'],
                                           ['Температура'])
        plot_height = st.sidebar.slider('Задать высоту графика', 200, 500, 250)
        # endregion

        st.markdown('### Метрики')
        col1, col2, col3 = st.columns(3)
        col1.metric("Температура", f'{current_temperature}' "°C", f'{round(current_temperature - last_temperature, 2)} °C')
        col2.metric("Ветер", f'{current_wind_speed}' "м/с", f'{round(current_wind_speed - last_wind_speed, 2)}м/с')
        col3.metric("Влажность", f'{current_relativehumidity}' "%", f'{current_relativehumidity - last_relativehumidity}%')

        # stocks = pd.read_csv('https://raw.githubusercontent.com/dataprofessor/data/master/stocks_toy.csv')
        donut_df = pd.DataFrame()
        donut_df['Дата'] = df['Дата']
        donut_df['День'] = df['День'].astype('int')
        donut_df['Час'] = df['Час'].astype('int')
        donut_df['Скорость ветра 10м'] = df['Скорость ветра 10м']
        donut_df['Скорость ветра 80м'] = df['Скорость ветра 80м']
        donut_df['Скорость ветра 120м'] = df['Скорость ветра 120м']
        donut_df['Скорость ветра 180м'] = df['Скорость ветра 180м']
        donut_df = donut_df.groupby(['Час']).mean()
        donut_df.fillna(0, inplace=True)
        # print(donut_df)

        c1, c2 = st.columns((7, 3))
        with c1:
            st.markdown('### Тепловая карта')
            plost.time_hist(
                data=df,
                date='Дата',
                x_unit='dayofyear',
                y_unit='hours',
                color=time_hist_color,
                aggregate='median',
                legend='top',
                height=345,
                use_container_width=True
            )
        with c2:
            st.markdown('### Кольцевая диаграмма')
            print(donut_df)
            print(donut_theta)
            donut_df['Час дня'] = range(0, 24)

            plost.donut_chart(
                data=donut_df,
                theta='Час дня',
                color=donut_theta,
                legend='bottom',
                use_container_width=True
            )
        st.markdown('### График')
        st.line_chart(data=df, x='Дата', y=plot_data, height=plot_height)
    else:
        st.error('Результатов не найдено')

