import numpy as np
import pandas as pd


def investment_round(df):
    money_cols = ["Total Cost", "Net Cost", "Total Earnings", "Net Earnings", "Fees", "Net Margin"]
    for col in money_cols:
        df[col] = round(df[col], 2)
    df["Price Per"] = round(df["Price Per"], 4)
    if df['Investment Type'].any() == 'Crypto':
        df["Quantity"] = round(df["Quantity"], 4)
    else:
        df["Quantity"] = round(df["Quantity"], 2)
    return df


def clean_table(df, investment_type: str, exchange_rates: list):
    df["Investment Type"] = investment_type
    df['Margin'] = df["Total Earnings"].fillna(0) - df["Total Cost"].fillna(0)
    df['Net Margin'] = df["Net Earnings"].fillna(0) - df["Total Cost"].fillna(0)
    df["Fees"] = df["Fees"].fillna(0)
    df["USD/EUR Exchange Rate"] = float(exchange_rates[0])
    df["EUR/USD Exchange Rate"] = float(exchange_rates[1])
    df["Transaction Date"] = pd.to_datetime(df["Transaction Date"])
    return df


def stonk_split(df, company, date, ratio):
    co_filter = (df["Company"] == company) | (df["Ticker"] == company)
    date_filter = (df["Transaction Date"] <= date)

    ## TODO Add more
    if ratio == "4:1":
        df.loc[(co_filter & date_filter), "Quantity"] *= 4
        df.loc[(co_filter & date_filter), "Price Per"] /= 4
    elif ratio == "2:1":
        df.loc[(co_filter & date_filter), "Quantity"] *= 2
        df.loc[(co_filter & date_filter), "Price Per"] /= 2
    return df


def get_totals_per_asset(df, metrics):
    df = (
        df.groupby(["Company", "Ticker", "Investment Type"])
            .agg({metric: np.sum for metric in metrics})
            .reset_index()
    )
    return df


def get_daily_totals(df, metrics):
    df = (
        df.groupby(["Transaction Date", "Ticker", "Investment Type"])
            .agg({metric: np.sum for metric in metrics})
            .reset_index()
    )
    return df


def get_p_and_l(df):
    df = (
        df.groupby(["Company", "Ticker", "Investment Type"])
            .filter(lambda x: x["Quantity"].sum().round(3) == 0)
            .groupby(["Company", "Investment Type"])
            .agg({"Quantity": np.sum, "Net Margin": np.sum})
            .reset_index()
    )
    return df


def avg_cost_per_asset(df):
    df = (
        df.groupby(["Company", "Ticker", "Investment Type"])
            .filter(lambda x: x["Quantity"].sum().round(3) > 0)
            .groupby(["Company", "Ticker", "Investment Type"])
            .agg({"Quantity": np.sum, "Net Cost": np.sum})
            .reset_index()
    )
    df["Avg Cost"] = round(abs(df["Net Cost"]) / df["Quantity"], 3)
    if df['Investment Type'].any() == 'Crypto':
        df["Quantity"] = round(df["Quantity"], 4)
    else:
        df["Quantity"] = round(df["Quantity"], 2)
    df.drop('Investment Type', axis=1, inplace=True)
    return df


def convert_currency(df, metrics, currency="USD"):
    if currency == "USD":
        df.loc[df.Currency == "Euro", metrics] = (
            df.loc[df.Currency == "Euro", metrics]
                .multiply(df.loc[df.Currency == "Euro", "EUR/USD Exchange Rate"], axis="index")
        )
    else:
        df.loc[df.Currency == "US Dollar", metrics] = (
            df.loc[df.Currency == "Euro", metrics]
                .multiply(df.loc[df.Currency == "Euro", "USD/EUR Exchange Rate"], axis="index")
        )
    df = investment_round(df)
    df["Current Currency"] = currency
    return df