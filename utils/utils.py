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
        df.groupby("Transaction Date")
            .agg({metric: np.sum for metric in metrics})
            .reset_index()
            .sort_values("Transaction Date")
    )
    return df


def get_profit_and_loss(df):
    cols = ["Company", "Quantity", "Net Cost", "Net Earnings", "Price Per", "Profit/Loss"]
    profit_loss_df = pd.DataFrame(columns=cols)

    assets_sold = df.loc[df.Transaction == "Sell", "Company"].unique()
    assets_sold_df = df.loc[df.Company.isin(assets_sold)].sort_values(['Company', 'Transaction Date'])

    for asset in assets_sold:
        a = asset
        q = 0
        nc = 0
        m = 0
        ne = 0
        pp = 0
        profit_loss = 0

        for i, row in df.iterrows():
            if row.Company == asset:
                if row.Transaction == "Buy":
                    q += row["Quantity"]
                    nc += row["Net Cost"]
                    m += row["Net Cost"]
                    pp = m / q
                elif row.Transaction == "Sell":
                    ne += row["Net Earnings"]
                    p_l = row["Net Earnings"] - (abs(row.Quantity) * pp)
                    profit_loss += p_l
                    q += row.Quantity
                    m -= row["Net Earnings"]
                    pp = m / q if q > 0 else 0
        profit_loss_df = profit_loss_df.append(pd.DataFrame([[asset, q, nc, ne, pp, profit_loss]], columns=cols))

    return profit_loss_df.sort_values('Profit/Loss', ascending=False)


def avg_cost_per_asset(df):
    df = (
        df.groupby(["Company", "Ticker", "Investment Type"])
            .filter(lambda x: x["Quantity"].sum().round(3) > 0)
            .groupby(["Company", "Ticker", "Investment Type"])
            .agg({"Quantity": np.sum, "Net Cost": np.sum, "Net Earnings": np.sum})
            .reset_index()
    )
    df["Profit"] = df["Net Earnings"] - df["Net Cost"]
    df["Avg Cost"] = round(df["Profit"] / df["Quantity"], 3)
    if df['Investment Type'].any() == 'Crypto':
        df["Quantity"] = round(df["Quantity"], 4)
    else:
        df["Quantity"] = round(df["Quantity"], 2)
    df.drop(['Investment Type'], axis=1, inplace=True)
    df["Net Cost"] = round(df["Net Cost"], 2)
    return df


def convert_currency(df, metrics, currency="USD"):
    if currency == "USD":
        df.loc[df.Currency == "EUR", metrics] = (
            df.loc[df.Currency == "EUR", metrics]
                .multiply(df.loc[df.Currency == "EUR", "EUR/USD Exchange Rate"], axis="index")
        )
    else:
        df.loc[df.Currency == "USD", metrics] = (
            df.loc[df.Currency == "USD", metrics]
                .multiply(df.loc[df.Currency == "USD", "USD/EUR Exchange Rate"], axis="index")
        )
    df = investment_round(df)
    df["Current Currency"] = currency
    return df


def aggregate_date(df, aggregation='daily'):
    if aggregation == 'daily':
        pass
    elif aggregation == 'monthly':
        df.loc[:, "Transaction Date"] = df['Transaction Date'].apply(lambda x: str(x)[:7] + "-01")
    else:
        df.loc[:, "Transaction Date"] = df['Transaction Date'].apply(lambda x: str(x).split("-")[0] + "-01-01")
    df.loc[:, "Transaction Date"] = pd.to_datetime(df["Transaction Date"])
    return df


def get_capital_gains(df, tax_rate=.35, verbose=False):
    df["Transaction Year"] = df['Transaction Date'].apply(lambda x: str(x).split("-")[0]).astype(str)

    assets_sold = df.loc[df.Transaction == "Sell", "Company"].unique()
    years = df.loc[df.Transaction == "Sell", "Transaction Year"].unique()
    profit_loss_dict = {k: {year: 0 for year in years} for k in assets_sold}

    for asset in assets_sold:
        q = 0
        m = 0
        pp = 0

        for i, row in df.iterrows():
            if row.Company == asset:
                if row.Transaction == "Buy":
                    q += row["Quantity"]
                    m += row["Net Cost"]
                    pp = m / q
                    if verbose:
                        print("Bought {} of {} for {}".format(row["Quantity"], asset, row["Net Cost"]))
                elif row.Transaction == "Sell":
                    p_l = row["Net Earnings"] - (abs(row.Quantity) * pp)
                    q += row.Quantity
                    m -= row["Net Earnings"]
                    pp = m / q if q > 0 else 0
                    year = row["Transaction Year"]
                    if verbose:
                        print("Sold {} of {} for {} on {}".format(
                            row["Quantity"], asset, row["Net Earnings"], row["Transaction Year"]
                        ))

                    profit_loss_dict[asset][year] += p_l

    years_dict = {year: 0 for year in years}

    for key, value in profit_loss_dict.items():
        for year in years:
            years_dict[year] += value[year]

    capital_gains_df = (
        pd.DataFrame.from_dict(years_dict, orient='index', columns=['Profit/Loss'])
            .reset_index()
            .rename(columns={"index": "Year"})
    )
    capital_gains_df["Capital Gains Tax"] = capital_gains_df["Profit/Loss"] * tax_rate

    return capital_gains_df


def transform_dtypes(df, dt_cols, numeric_cols, obj_cols=None):
    df = df.replace("", np.nan)
    df = df.replace(",", "")
    for col in dt_cols:
        df[col] = pd.to_datetime(df[col])
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col])
    if obj_cols:
        for col in obj_cols:
            df[col] = df[col].astype(str)
    return df