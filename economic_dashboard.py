import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from dateutil.relativedelta import relativedelta
from fredapi import Fred
from datetime import datetime, timedelta
import requests 
from flask_cors import CORS
import streamlit as st


st.set_page_config(layout="wide")

st.title('📈 Economic Dashboard')

fred = Fred(api_key='PASTE FRED API') # FREAD API

today = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.write("""
         ### Upcoming Events: 
         UTC Time: """  ) 
    today

today = (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')

start_date = (datetime.now() + timedelta(days=0)).strftime('%Y-%m-%d')
end_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')

api_key = "financialmodelingprep API"  
response = requests.get(f"https://financialmodelingprep.com/api/v3/economic_calendar?from={start_date}&to={end_date}&apikey={api_key}")
    
data = []
if response.status_code == 200:
    data = response.json()
else:
    pass
    
df = pd.DataFrame(data)

filtered_df = df[(df['country'] == 'US') & (df['impact'].isin(['High', 'Medium']))]
filtered_df = filtered_df.sort_values("date")
filtered_df = filtered_df.fillna('No Data')
        
renamed_df = filtered_df.rename(columns={
    'date': 'Time',
    'event': 'Event',
    'currency': 'Currency',
    'actual': 'Actual',
    'estimate': 'Forecast',
    'previous': 'Previous',
    'impact': 'Impact'
})

selected_columns = renamed_df[['Time', 'Event', 'Actual', 'Forecast', 'Previous', 'Impact']]

selected_columns = selected_columns.reset_index(drop=True)

selected_columns['Actual'] = pd.to_numeric(selected_columns['Actual'], errors='coerce')
selected_columns['Forecast'] = pd.to_numeric(selected_columns['Forecast'], errors='coerce')
selected_columns['Previous'] = pd.to_numeric(selected_columns['Previous'], errors='coerce')


def highlight_actual(val):
    if pd.isna(val['Actual']) or pd.isna(val['Forecast']):
        return [''] * len(val)
    if val['Actual'] > val['Forecast']:
        return ['color: green' if col == 'Actual' else '' for col in val.index]
    elif val['Actual'] < val['Forecast']:
        return ['color: red' if col == 'Actual' else '' for col in val.index]
    else:
        return [''] * len(val)


styled_df = selected_columns.style.apply(highlight_actual, axis=1)
styled_df = styled_df.format({'Actual': '{:.2f}', 'Forecast': '{:.2f}', 'Previous': '{:.2f}'})

with col1:
    with st.expander("View events"):
        st.dataframe(styled_df)


with col1:
    st.write("""
         ### Past Events:"""  ) 


start_date_2 = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
end_date_2 = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

response_2 = requests.get(f"https://financialmodelingprep.com/api/v3/economic_calendar?from={start_date_2}&to={end_date_2}&apikey={api_key}")
    
data_2 = []
if response_2.status_code == 200:
    data = response_2.json()
else:
    pass
    
df_2 = pd.DataFrame(data)

filtered_df_2 = df_2[(df_2['country'] == 'US') & (df_2['impact'].isin(['High', 'Medium']))]
filtered_df_2 = filtered_df_2.fillna('No Data')
        
renamed_df_2 = filtered_df_2.rename(columns={
        'date': 'Time',
        'event': 'Event',
        'currency': 'Currency',
        'actual': 'Actual',
        'estimate': 'Forecast',
        'previous': 'Previous',
        'impact': 'Impact'
    })

selected_columns_2 = renamed_df_2[['Time', 'Event', 'Actual', 'Forecast', 'Previous', 'Impact']]

selected_columns_2 = selected_columns_2.reset_index(drop=True)

selected_columns_2['Actual'] = pd.to_numeric(selected_columns['Actual'], errors='coerce')
selected_columns_2['Forecast'] = pd.to_numeric(selected_columns['Forecast'], errors='coerce')
selected_columns_2['Previous'] = pd.to_numeric(selected_columns['Previous'], errors='coerce')

styled_df_2 = selected_columns_2.style.apply(highlight_actual, axis=1)
styled_df_2 = styled_df_2.format({'Actual': '{:.2f}', 'Forecast': '{:.2f}', 'Previous': '{:.2f}'})

with col1:
    with st.expander("View events"):
        st.dataframe(styled_df_2)


default_date = datetime.now() - relativedelta(years=5)
spy_start_year = default_date.year
spy_start_month = default_date.month
cpi_start_year = default_date.year
cpi_start_month = 1  

plot_url1 = plot_url2 = plot_url3 = None

default_spy_year = 2020
default_spy_month = 1
default_cpi_year = 2020
default_cpi_month = 1

st.sidebar.title("Settings")
st.sidebar.write("### SPY Charts:")
spy_start_year = st.sidebar.number_input('Start Year for SPY', value=default_spy_year, min_value=1950, step=1)

spy_start_month = st.sidebar.number_input('Start Month for SPY', value=default_spy_month, min_value=1, max_value=12, step=1)

spy_start_date = datetime(year=spy_start_year, month=spy_start_month, day=1)

spy_data = yf.download('SPY', start=spy_start_date.strftime('%Y-%m-%d'), interval='1mo')
monthly_returns = spy_data['Close'].pct_change()
spy_cpi_data = fred.get_series("CPILFESL", observation_start=spy_start_year)
spy_monthly_core_cpi_data = spy_cpi_data.pct_change()
real_return = monthly_returns - spy_monthly_core_cpi_data
real_return = real_return.dropna()
real_return_adjusted = (1 + real_return).cumprod() - 1

spy_initial_price = spy_data['Close'].iloc[0]  
spy_final_price = spy_data['Close'].iloc[-1]  
spy_return_show = ((spy_final_price - spy_initial_price) / spy_initial_price) * 100

if not real_return_adjusted.empty:
    last_real_return = real_return_adjusted.iloc[-1] * 100
else:
    last_real_return = None  

def plot_line(data, title, ylabel):
    fig, ax = plt.subplots()
    ax.plot(data, color='red', linewidth=2, label=ylabel)
    ax.set_title(title, color='white')
    ax.set_ylabel(ylabel, color='#999999')
    ax.set_facecolor('#000000')
    ax.grid(True, color='#333333', linestyle='--', linewidth=0.5)
    plt.yticks(color='#999999')
    ax.spines['bottom'].set_color('#999999')
    ax.spines['left'].set_color('#999999')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(loc='upper left', frameon=False)
    fig.patch.set_facecolor('#000000')  
    ax.patch.set_alpha(0)  
    return fig




with col2:
    with st.expander("SPY Prices", expanded=True):
        fig_spy_prices = plot_line(spy_data['Close'], 'SPY Prices', 'Price')
        st.pyplot(fig_spy_prices)
        st.write(f"Return: {spy_return_show:.2f}%")
with col3:
    with st.expander("SPY Inflation-Adjusted Returns", expanded=True):
        fig_real_returns = plot_line(real_return_adjusted, 'SPY Inflation-Adjusted Returns', 'Return')
        st.pyplot(fig_real_returns)
        st.write(f"Real Return: {last_real_return:.2f}%")


st.sidebar.write("### Month-over-Month Inflation Rate:")
cpi_start_year = st.sidebar.number_input('Start Year for CPI', value=default_spy_year, min_value=1950, step=1)
cpi_start_month = st.sidebar.number_input('Start Month for CPI', value=default_spy_month, min_value=1, max_value=12, step=1)
cpi_data = fred.get_series("CPILFESL", observation_start=datetime(cpi_start_year, cpi_start_month, 1))
monthly_core_cpi_data = cpi_data.pct_change()

def plot_bar(data, title, ylabel, bar_width=0.8):
    fig2, ax2 = plt.subplots(figsize=(15, 6))
    monthly_core_cpi_data.plot(kind="bar", ax=ax2, title='Month-over-Month Inflation Rate', color='red')
    ax2.set_title(title, color='white')
    ax2.set_xlabel('Date')
    ax2.set_ylabel(ylabel, color='#e0e0e0')
    ax2.set_facecolor('#000000')
    ax2.figure.set_facecolor('#000000')
    ax2.spines['bottom'].set_color('#999999')
    ax2.spines['left'].set_color('#999999')
    ax2.tick_params(colors='#e0e0e0', which='both')
    ax2.yaxis.label.set_color('#e0e0e0')
    ax2.title.set_color('#e0e0e0')
    ax2.axhline(y=0, color='white', linestyle='--')
    plt.close()
    return  fig2

with col1:
    st.write("### Month-over-Month Inflation Rate")
    with st.expander("View Graph", expanded=False):
        fig_barnhart = plot_bar(monthly_core_cpi_data, 'Month-over-Month Inflation Rate', 'CPI')
        st.pyplot(fig_barnhart)

st.sidebar.write("### Quarterly GDP Growth:")
gdp_start_year = st.sidebar.number_input('Start Year for GDP', value=default_spy_year, min_value=1950, step=1)
gdp_start_month = st.sidebar.number_input('Start Month for GDP', value=default_spy_month, min_value=1, max_value=12, step=1)
gdp_data = fred.get_series("A939RX0Q048SBEA", observation_start=datetime(gdp_start_year, gdp_start_month, 1))
gdp_data = gdp_data.pct_change()
gdp_data.index = pd.to_datetime(gdp_data.index)

def plot_bar_gdp(data, title, ylabel, bar_width=0.8):
    fig, ax = plt.subplots(figsize=(15, 6))
    data.plot(kind="bar", ax=ax, title=title, color='red')
    ax.set_ylabel(ylabel, color='#e0e0e0')
    ax.set_facecolor('#000000')
    ax.figure.set_facecolor('#000000')
    ax.spines['bottom'].set_color('#999999')
    ax.spines['left'].set_color('#999999')
    ax.tick_params(colors='#e0e0e0', which='both')
    ax.yaxis.label.set_color('#e0e0e0')
    ax.title.set_color('#e0e0e0')
    ax.axhline(y=0, color='white', linestyle='--')  
    plt.xticks(rotation=45)  
    plt.close()
    return fig

with col1:
    st.write("### Quarterly GDP Growth")
    with st.expander("View Graph", expanded=False):
        fig_gdp = plot_bar_gdp(gdp_data, 'Quaterly GDP Growth', 'GDP')
        st.pyplot(fig_gdp)

st.sidebar.write("### Unemployment Rate:")
unemployment_start_year = st.sidebar.number_input('Start Year for Unemployment Rate', value=default_spy_year, min_value=1950, step=1)
unemployment_start_month = st.sidebar.number_input('Start Month for Unemployment Rate', value=default_spy_month, min_value=1, max_value=12, step=1)
unemployment_data = fred.get_series("UNRATE", observation_start=datetime(unemployment_start_year, unemployment_start_month, 1))
unemployment_data.index = pd.to_datetime(unemployment_data.index)

def plot_bar_unemployment(data, title, ylabel, bar_width=0.8):
    fig, ax = plt.subplots(figsize=(15, 6))
    data.index = pd.to_datetime(data.index)  
    data.plot(kind="bar", ax=ax, title=title, color='red')
    ax.set_ylabel(ylabel, color='#e0e0e0')
    ax.set_facecolor('#000000')
    ax.figure.set_facecolor('#000000')
    ax.spines['bottom'].set_color('#999999')
    ax.spines['left'].set_color('#999999')
    ax.tick_params(colors='#e0e0e0', which='both')
    ax.yaxis.label.set_color('#e0e0e0')
    ax.title.set_color('#e0e0e0')
    ax.axhline(y=0, color='white', linestyle='--') 
    plt.close()
    return fig



with col1:
    st.write("### Unemployment Rate")
    with st.expander("View Graph", expanded=False):
        fig_unemployment = plot_bar_unemployment(unemployment_data, 'Unemployment Rate', 'Percent')
        st.pyplot(fig_unemployment)

import yfinance as yf
import streamlit as st

with col2:
    with st.expander("Compare with other Ticker", expanded=False):
        ticker = st.text_input("Search Ticker:")
        try:
            ticker_data = yf.download(ticker, start=spy_start_date.strftime('%Y-%m-%d'), interval='1mo')
            if not ticker_data.empty:

                initial_price = ticker_data['Close'].iloc[0]
                final_price = ticker_data['Close'].iloc[-1]
                stock_return = ((final_price - initial_price) / initial_price) * 100

                fig_ticker_prices = plot_line(ticker_data['Close'], title='Stock Closing Prices', ylabel='Price')
                st.pyplot(fig_ticker_prices)

                st.write(f"Return from {spy_start_date.strftime('%Y-%m-%d')} to {ticker_data.index[-1].strftime('%Y-%m-%d')}: {stock_return:.2f}%")
            else:
                st.error("No data found for the given ticker.")
        except Exception as e:
            st.error(f"Failed to fetch data: {e}")

