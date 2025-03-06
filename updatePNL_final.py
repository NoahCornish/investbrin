import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import requests

# Function to get the previous trading day's closing price and sector
def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5)
    hist = stock.history(start=start_date, end=end_date)
    if not hist.empty:
        close = hist['Close'].iloc[-1]
        sector = stock.info.get('sector', 'Unknown')
        return close, sector
    return None, 'Unknown'

# Function to get USD to CAD exchange rate
def get_usd_to_cad_rate():
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    try:
        response = requests.get(url)
        data = response.json()
        return data['rates']['CAD']
    except Exception as e:
        print(f"Error fetching exchange rate: {e}. Using default rate of 1.35")
        return 1.35

# Hardcoded portfolio data
portfolio_data = [
    {'Stock': 'JNJ', 'Shares': 15, 'AvgCost': 159.53, 'DivAmnt': 4.96},
    {'Stock': 'UNH', 'Shares': 5, 'AvgCost': 479.65, 'DivAmnt': 8.4},
    {'Stock': 'AMZN', 'Shares': 30, 'AvgCost': 222.85, 'DivAmnt': 0.00},
    {'Stock': 'COST', 'Shares': 6, 'AvgCost': 863.00, 'DivAmnt': 4.64},
    {'Stock': 'MSFT', 'Shares': 17, 'AvgCost': 335.17, 'DivAmnt': 3.00},
    {'Stock': 'GDX', 'Shares': 25, 'AvgCost': 42.06, 'DivAmnt': 0},
    {'Stock': 'CU.TO', 'Shares': 103, 'AvgCost': 30.92, 'DivAmnt': 1.83},
    {'Stock': 'QSR.TO', 'Shares': 35, 'AvgCost': 109.96, 'DivAmnt': 2.48},
    {'Stock': 'RUS.TO', 'Shares': 50, 'AvgCost': 43.45, 'DivAmnt': 1.68},
    {'Stock': 'SLF.TO', 'Shares': 50, 'AvgCost': 72.97, 'DivAmnt': 3.36},
    {'Stock': 'TOU.TO', 'Shares': 30, 'AvgCost': 58.49, 'DivAmnt': 1.28},
    {'Stock': 'FFH.TO', 'Shares': 1, 'AvgCost': 1994.42, 'DivAmnt': 15},
    {'Stock': 'BCE.TO', 'Shares': 47, 'AvgCost': 1.00, 'DivAmnt': 3.99},
    {'Stock': 'CNQ.TO', 'Shares': 354, 'AvgCost': 34.65, 'DivAmnt': 2.55},
    {'Stock': 'ENB.TO', 'Shares': 195, 'AvgCost': 53.45, 'DivAmnt': 3.77},
    {'Stock': 'T.TO', 'Shares': 131, 'AvgCost': 27.14, 'DivAmnt': 1.52},
    {'Stock': 'CM.TO', 'Shares': 26, 'AvgCost': 1, 'DivAmnt': 3.60},
    {'Stock': 'RY.TO', 'Shares': 551, 'AvgCost': 85.92, 'DivAmnt': 5.92},
]

# Create DataFrame from the hardcoded data
df = pd.DataFrame(portfolio_data)

# Add new columns
df['Close'] = 0.0
df['Sector'] = ''
df['Currency'] = df['Stock'].apply(lambda x: 'CAD' if '.TO' in x else 'USD')

# Fetch closing prices and sectors
for index, row in df.iterrows():
    symbol = row['Stock']
    close, sector = get_stock_data(symbol)
    if close is not None:
        df.at[index, 'Close'] = close
        df.at[index, 'Sector'] = sector

# Get USD to CAD exchange rate
usd_to_cad = get_usd_to_cad_rate()

# Handle AMZN special case
amzn_mask = df['Stock'] == 'AMZN'
df.loc[amzn_mask, 'Close'] = df.loc[amzn_mask, 'Close'] * usd_to_cad
df.loc[amzn_mask, 'Currency'] = 'CAD'

# Calculate additional columns
df['MktValue'] = df['Shares'] * df['Close']

# Calculate market value in CAD for all stocks
df['MktValueCAD'] = df.apply(
    lambda row: row['MktValue'] * usd_to_cad if row['Currency'] == 'USD' else row['MktValue'], 
    axis=1
)

# Calculate total portfolio value in CAD
total_mkt_value_cad = df['MktValueCAD'].sum()

# Calculate weight as a percentage of total portfolio value in CAD
df['Weight'] = (df['MktValueCAD'] / total_mkt_value_cad) * 100

# Continue with other calculations
df['PnL'] = df['MktValue'] - (df['Shares'] * df['AvgCost'])
df['%Ret'] = (df['PnL'] / (df['Shares'] * df['AvgCost'])) * 100  # Percent return
df['DivYrAmnt'] = df['DivAmnt'] * df['Shares']
df['DivMnAmnt'] = df['DivYrAmnt'] / 12
df['DivDyAmnt'] = df['DivYrAmnt'] / 365.25
df['DivYield'] = df['DivYrAmnt'] / df['MktValue'] * 100

# Save Portfolio Report
df.to_csv("portfolio_report.csv", index=False, float_format="%.2f")

# Summarize CAD stocks
cad_df = df[df['Currency'] == 'CAD']
cad_summary = {
    'Total MktValue (CAD)': cad_df['MktValue'].sum(),
    'Total PnL (CAD)': cad_df['PnL'].sum(),
    'Total DivYrAmnt (CAD)': cad_df['DivYrAmnt'].sum()
}
pd.DataFrame.from_dict(cad_summary, orient='index', columns=['Value']).to_csv("cad_summary.csv", float_format="%.2f")

# Summarize USD stocks
usd_df = df[df['Currency'] == 'USD']
usd_summary = {
    'Total MktValue (USD)': usd_df['MktValue'].sum(),
    'Total PnL (USD)': usd_df['PnL'].sum(),
    'Total DivYrAmnt (USD)': usd_df['DivYrAmnt'].sum()
}
pd.DataFrame.from_dict(usd_summary, orient='index', columns=['Value']).to_csv("usd_summary.csv", float_format="%.2f")

# Overall summary in CAD
total_pnl_cad = cad_df['PnL'].sum() + (usd_df['PnL'].sum() * usd_to_cad)
total_div_yr_cad = cad_df['DivYrAmnt'].sum() + (usd_df['DivYrAmnt'].sum() * usd_to_cad)
total_div_mn_cad = total_div_yr_cad / 12
total_div_dy_cad = total_div_yr_cad / 365.25
total_yield = (total_div_yr_cad / total_mkt_value_cad) * 100 if total_mkt_value_cad != 0 else 0

overall_summary_data = {
    "Total Market Value (CAD)": [total_mkt_value_cad],
    "Total PnL (CAD)": [total_pnl_cad],
    "Total Annual Dividend (CAD)": [total_div_yr_cad],
    "Total Monthly Dividend (CAD)": [total_div_mn_cad],
    "Total Daily Dividend (CAD)": [total_div_dy_cad],
    "Total Yield (%)": [total_yield],
    "Exchange Rate Used (USD to CAD)": [usd_to_cad],
}

pd.DataFrame(overall_summary_data).to_csv("overall_summary.csv", index=False, float_format="%.2f")

print("CSV files saved successfully!")
