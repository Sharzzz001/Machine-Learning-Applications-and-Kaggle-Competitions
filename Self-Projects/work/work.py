import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Example data
data = {
    'Date': pd.date_range(start='2024-01-01', periods=186, freq='D'),
    'Bonds': [100] * 186, 'Derivatives': [50] * 186,
    'Equities': [75] * 186, 'Funds': [30] * 186,
    'Structured Products': [20] * 186
}
df = pd.DataFrame(data)

# Time taken per trade (minutes)
maker_time = {'Bonds': 5, 'Derivatives': 7, 'Equities': 6, 'Funds': 8, 'Structured Products': 10}
checker_time = {'Bonds': 3, 'Derivatives': 4, 'Equities': 5, 'Funds': 6, 'Structured Products': 8}

# Makers and Checkers Count
makers_count = 5
checkers_count = 3
total_capacity = (makers_count + checkers_count) * 480  # Total daily capacity in minutes

# Calculate total workload
for product in ['Bonds', 'Derivatives', 'Equities', 'Funds', 'Structured Products']:
    df[f'{product}_Time'] = df[product] * (maker_time[product] + checker_time[product])

df['Total Time'] = df[[f'{product}_Time' for product in ['Bonds', 'Derivatives', 'Equities', 'Funds', 'Structured Products']]].sum(axis=1)

# Identify capacity breaches
df['Exceeds Capacity'] = df['Total Time'] > total_capacity

# Forecast trade volumes
forecast_dfs = []
for product in ['Bonds', 'Derivatives', 'Equities', 'Funds', 'Structured Products']:
    model = ExponentialSmoothing(df[product], trend='add', seasonal='add', seasonal_periods=30)
    fit = model.fit()
    forecast = fit.forecast(30)  # Forecast 30 days ahead
    forecast_dfs.append(pd.DataFrame({'Date': pd.date_range(start=df['Date'].iloc[-1] + pd.Timedelta(days=1), periods=30),
                                       f'{product}_Forecast': forecast}))

forecast_df = pd.concat(forecast_dfs, axis=1)
forecast_df = forecast_df.loc[:, ~forecast_df.columns.duplicated()]  # Remove duplicate Date columns

# Calculate forecasted workload
for product in ['Bonds', 'Derivatives', 'Equities', 'Funds', 'Structured Products']:
    forecast_df[f'{product}_Time_Forecast'] = forecast_df[f'{product}_Forecast'] * (maker_time[product] + checker_time[product])

forecast_df['Total Forecast Time'] = forecast_df[[f'{product}_Time_Forecast' for product in ['Bonds', 'Derivatives', 'Equities', 'Funds', 'Structured Products']]].sum(axis=1)

# Identify future breaches
forecast_df