import numpy as np
import pandas as pd
<<<<<<< HEAD
=======
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from forex_python.converter import CurrencyRates
>>>>>>> dev
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
<<<<<<< HEAD

pd.set_option('display.float_format', lambda x: '%.4f' % x)

def get_net_spend(df):
    df = (
        df.groupby(["Company", "Ticker", "Investment Type"])["Net Spend"]
            .sum()
            .reset_index()
    )
    return df

def get_daily_spend(df):
    df = (
        df.groupby(["Transaction Date", "Transaction", "Investment Type"])["Total Price"]
            .sum()
            .reset_index()
    )
    df["Net Spend"] = df["Total Price"].apply(lambda x: round(abs(x), 2))
    return df

def get_p_and_l(df):
    df = (
        df.groupby(["Company", "Ticker", "Investment Type"])
            .filter(lambda x: x["Quantity"].sum().round(3) == 0)
            .groupby(["Company", "Investment Type"])
            .agg({"Quantity": np.sum, "Total Price": np.sum})
            .reset_index()
    )
    return df

def avg_cost_per_asset(df):
    df = (
        df.groupby(["Company", "Ticker", "Investment Type"])
            .filter(lambda x: x["Quantity"].sum().round(3) > 0)
            .groupby(["Company", "Ticker", "Investment Type"])
            .agg({"Quantity": np.sum, "Total Price": np.sum})
            .reset_index()
    )
    df["Avg Cost"] = round(abs(df["Total Price"]) / df["Quantity"], 2)
    df["Total Price"] = df["Total Price"].apply(lambda x: round(x, 2))
    df.drop('Investment Type', axis=1, inplace=True)
    return df


def stonk_split(df, company, date, ratio):
    co_filter = (df["Company"] == company) | (df["Ticker"] == company)
    date_filter = (df["Transaction Date"] <= date)

    if ratio == "4:1":
        df.loc[(co_filter & date_filter), "Quantity"] *= 4
        df.loc[(co_filter & date_filter), "Price Per"] /= 4
    return df

def investment_round(df):
    df["Total Price"] = round(df["Total Price"], 2)
    if df['Investment Type'] == 'Crypto':
        df["Quantity"] = round(df["Quantity"], 2)
    else:
        df["Quantity"] = round(df["Quantity"], 4)
    return df



# ETL
crypto_df = pd.read_excel('Investments Tracker.xlsx', sheet_name="Crypto", date_parser="Transaction Date")
crypto_df["Investment Type"] = "Crypto"
stonks_df = pd.read_excel('Investments Tracker.xlsx', sheet_name="Stonks", date_parser="Transaction Date")
stonks_df["Investment Type"] = "Stonks"
stonks_df = stonk_split(stonks_df, "AAPL", "2020-08-28", "4:1")
df = pd.concat([crypto_df, stonks_df])
df = df.apply(lambda x: investment_round(x), axis=1)
df["Net Spend"] = df['Total Price'] * -1
avg_cost_cols = ['Company', 'Ticker', 'Quantity', 'Total Price', 'Avg Cost']
=======
from utils.utils import *


# Google Service Account
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(
         'credentials/service_account.json', scope
)
gc = gspread.authorize(credentials)

# ETL
c = CurrencyRates()
usd_to_euro = c.get_rate('USD', 'EUR')
euro_to_usd = c.get_rate('EUR', 'USD')

metrics = ["Quantity", "Total Cost", "Net Margin", "Net Earnings", "Fees"]
currency_metrics = ["Price Per", "Total Cost", "Fees", "Net Cost",
                    "Total Earnings", "Net Earnings", "Margin", "Net Margin"]
dt_cols = ["Transaction Date"]
numeric_cols = ['Total Earnings', 'Quantity', 'Net Earnings', 'Net Cost', 'Price Per', 'Total Cost', 'Fees']

df = pd.DataFrame()
for sheet in gc.open("Investments Tracker").worksheets():
    data = sheet.get_all_values()
    headers = data.pop(0)
    temp_df = pd.DataFrame(data, columns=headers)
    temp_df = transform_dtypes(temp_df, dt_cols, numeric_cols, obj_cols=None)
    temp_df = clean_table(temp_df, sheet.title, [usd_to_euro, euro_to_usd])
    df = df.append(temp_df)

df = stonk_split(df, "AAPL", "2020-08-28", "4:1")
>>>>>>> dev

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "My Investments Profile"
server = app.server

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H1(
<<<<<<< HEAD
                    children='My Investments Portfolio',
                    className="header-title",
                ),
                html.P(
                    children='''Including both my CRYPTO and STONKS assets.''',
=======
                    children='Investments Portfolio',
                    className="header-title",
                ),
                html.P(
                    children='''Both my CRYPTO and STONKS assets.''',
>>>>>>> dev
                    className="header-description",
                ),
            ],
            className='header',
        ),

<<<<<<< HEAD
        # Net Spend Bar Chart
        html.Div(
            children=[

                # net spend
                html.Div(
                    children=[
                        html.Div(children="Investment Type", className="menu-title"),
=======
        # filters
        html.Div(
            children=[

                # investment type filter
                html.Div(
                    children=[
                        html.Div(
                            children="Investment Type",
                            className="menu-title"
                        ),
>>>>>>> dev
                        dcc.Dropdown(
                            id="investment-type-filter",
                            options=[
                                {"label": inv_type, "value": inv_type}
                                for inv_type in np.sort(df["Investment Type"].unique())
                            ],
                            value="Stonks",
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
<<<<<<< HEAD
=======

                # currency filter
                html.Div(
                    children=[
                        html.Div(
                            children="Currency",
                            className="menu-title"
                        ),
                        dcc.Dropdown(
                            id="currency-filter",
                            options=[
                                {"label": c, "value": c}
                                for c in np.sort(df["Currency"].unique())
                            ],
                            value="USD",
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),

                # date range filter
>>>>>>> dev
                html.Div(
                    children=[
                        html.Div(
                            children="Date Range",
                            className="menu-title"
<<<<<<< HEAD
                            ),
=======
                        ),
>>>>>>> dev
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=df["Transaction Date"].min().date(),
                            max_date_allowed=df["Transaction Date"].max().date(),
                            start_date=df["Transaction Date"].min().date(),
                            end_date=df["Transaction Date"].max().date(),
                        ),
                    ]
                ),
<<<<<<< HEAD
=======

                # aggregation filter
                html.Div(
                    children=[
                        html.Div(
                            children="Aggregation",
                            className="menu-title"
                        ),
                        dcc.Dropdown(
                            id="aggregation-filter",
                            options=[{"label": value, "value": value} for value in ["daily", "monthly", "yearly"]],
                            value="daily",
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
>>>>>>> dev
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    dcc.Graph(
                        id='net-spend',
                        config={"displayModeBar": False},
                    ),
                    className="card"
                ),

                # Spend Line Chart
                html.Div(
                    dcc.Graph(
                        id='spend-over-time',
                        config={"displayModeBar": False},
                    ),
                    className="card"
                ),

                # Sell Line Chart
                html.Div(
                    dcc.Graph(
                        id='sell-over-time',
                        config={"displayModeBar": False},
                    ),
                    className="card"
                ),

                # Avg Cost Table
                html.Div(
                    [
                        html.Label("Average Cost per Asset"),
                        dash_table.DataTable(
                            id='avg-asset-cost',
<<<<<<< HEAD
                            columns=[{"id": i, "name": i} for i in avg_cost_cols],
=======
                            columns=[{"id": i, "name": i} for i in
                                     ['Company', 'Ticker', 'Quantity', 'Net Cost', 'Avg Cost']],
>>>>>>> dev
                            #data=investments_total.to_dict('records'),
                            style_data={
                                'whiteSpace': 'normal',
                                'height': 'auto',
                            },
                            # style_table={
                            #     'minHeight': '600px', 'height': '600px', 'maxHeight': '600px',
                            #     'minWidth': '700px', 'width': '700px', 'maxWidth': '700px',
                            #
                            # },
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold'
                            },
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'rgb(248, 248, 248)'
                                }
                            ],
                            style_as_list_view=True,
                        ),
                    ],
                    className="center"
                ),

                # Profit and Loss
                html.Div(
                    dcc.Graph(
<<<<<<< HEAD
                        id='stonks-net-spend',
=======
                        id='profit-loss',
                        config={"displayModeBar": False},
                    ),
                    className="card"
                ),

                # Capital Gains Tax
                html.Div(
                    dcc.Graph(
                        id='capital-gains',
>>>>>>> dev
                        config={"displayModeBar": False},
                    ),
                    className="card"
                ),
            ],
            className="wrapper"
        )
    ]
)


@app.callback(
    [
        Output("net-spend", "figure"),
        Output("spend-over-time", "figure"),
        Output("sell-over-time", "figure"),
<<<<<<< HEAD
        Output("stonks-net-spend", "figure")
=======
        Output("profit-loss", "figure"),
        Output("capital-gains", "figure"),
>>>>>>> dev
    ],
    [
        Input("investment-type-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
<<<<<<< HEAD
    ],
)
def update_charts(investment_type, start_date, end_date):
=======
        Input("currency-filter", "value"),
        Input("aggregation-filter", "value")
    ],
)
def update_charts(investment_type, start_date, end_date, currency, aggregation):
>>>>>>> dev
    mask = (
        (df["Investment Type"] == investment_type)
        & (df["Transaction Date"] >= start_date)
        & (df["Transaction Date"] <= end_date)
    )
<<<<<<< HEAD
    filtered_data = df.loc[mask, :]
    net_spend = get_net_spend(filtered_data)
    investments_daily = get_daily_spend(filtered_data)
    p_and_l = get_p_and_l(filtered_data)

    # net spend chart
    net_spend_chart = {
        'data': [
            {
                'x': net_spend['Company'],
                'y': net_spend['Net Spend'],
=======

    # etl
    filtered_data = df.loc[mask, :]
    filtered_data = convert_currency(filtered_data, currency_metrics, currency)
    net_margin = get_totals_per_asset(filtered_data, metrics)
    filtered_data = aggregate_date(filtered_data, aggregation=aggregation)
    investments_daily = get_daily_totals(filtered_data, metrics)

    # profit loss - needs to take into account historical buy-sell
    mask_pl = (
            (df["Investment Type"] == investment_type)
            & (df["Transaction Date"] <= end_date)
    )
    filtered_data_pl = df.loc[mask_pl, :]
    filtered_data_pl = convert_currency(filtered_data_pl, currency_metrics, currency)
    profit_loss = get_profit_and_loss(filtered_data_pl)

    taxes_df = get_capital_gains(filtered_data_pl)

    currency_marker = "$" if currency == "USD" else "€"

    # net margin chart
    net_margin_chart = {
        'data': [
            {
                'x': net_margin['Company'],
                'y': net_margin['Net Margin'],
>>>>>>> dev
                'type': 'bar',
            },
        ],
        'layout': {
            'title': {
<<<<<<< HEAD
                'text': 'Investments Net Spend by Company',
=======
                'text': 'Investments Net Margin by Company',
>>>>>>> dev
                "x": 0.05,
                "xanchor": "left",
            },
            "yaxis": {
<<<<<<< HEAD
           #     "tickprefix": "€",
=======
                "tickprefix": currency_marker,
>>>>>>> dev
                "fixedrange": True
            },
            "xaxis": {
                "fixedrange": True
            }
        }
    }

    # spend line chart
    spend_line_chart = {
        'data': [
            {
<<<<<<< HEAD
                'x': investments_daily.loc[investments_daily.Transaction == 'Buy', 'Transaction Date'],
                'y': investments_daily.loc[investments_daily.Transaction == 'Buy', 'Net Spend'],
=======
                'x': investments_daily.loc[investments_daily["Total Cost"] > 0, 'Transaction Date'],
                'y': investments_daily.loc[investments_daily["Total Cost"] > 0, 'Total Cost'],
>>>>>>> dev
                'type': 'line',
            },
        ],
        'layout': {
            'title': {
                'text': 'Buy Over Time',
                "x": 0.05,
                "xanchor": "left",
            },
            "yaxis": {
<<<<<<< HEAD
                #  "tickprefix": "€",
=======
                "tickprefix": currency_marker,
>>>>>>> dev
                "fixedrange": True
            },
            "xaxis": {
                "fixedrange": True
            }
        }
    }

    # sell line chart
    sell_line_chart = {
        'data': [
            {
<<<<<<< HEAD
                'x': investments_daily.loc[investments_daily.Transaction == 'Sell', 'Transaction Date'],
                'y': investments_daily.loc[investments_daily.Transaction == 'Sell', 'Net Spend'],
=======
                'x': investments_daily.loc[investments_daily['Net Earnings'] > 0, 'Transaction Date'],
                'y': investments_daily.loc[investments_daily['Net Earnings'] > 0, 'Net Earnings'],
>>>>>>> dev
                'type': 'line',
            },
        ],
        'layout': {
            'title': {
                'text': 'Sell Over Time',
                "x": 0.05,
                "xanchor": "left",
            },
            "yaxis": {
<<<<<<< HEAD
                #  "tickprefix": "€",
=======
                "tickprefix": currency_marker,
>>>>>>> dev
                "fixedrange": True
            },
            "xaxis": {
                "fixedrange": True
            }
        }
    }

<<<<<<< HEAD
    # p and l
    p_and_l_chart = {
        'data': [
            {
                'x': p_and_l['Company'],
                'y': p_and_l['Total Price'],
=======
    # profit and loss
    profit_loss_chart = {
        'data': [
            {
                'x': profit_loss['Company'],
                'y': profit_loss['Profit/Loss'],
>>>>>>> dev
                'type': 'bar',
            },
        ],
        'layout': {
            'title': {
<<<<<<< HEAD
                'text': 'Profit and Loss (Completely Sold Assets)',
=======
                'text': 'Profit and Loss',
>>>>>>> dev
                "x": 0.05,
                "xanchor": "left",
            },
            "yaxis": {
<<<<<<< HEAD
                #     "tickprefix": "$",
=======
                "tickprefix": currency_marker,
>>>>>>> dev
                "fixedrange": True
            },
            "xaxis": {
                "fixedrange": True
            }
        }
    }
<<<<<<< HEAD
    return net_spend_chart, spend_line_chart, sell_line_chart, p_and_l_chart
=======

    # capital gains tax
    capital_gains_tax_chart = {
        'data': [
            {
                'x': taxes_df['Year'],
                'y': taxes_df['Capital Gains Tax'],
                'type': 'bar',
            },
        ],
        'layout': {
            'title': {
                'text': 'Capital Gains Tax',
                "x": 0.05,
                "xanchor": "left",
            },
            "yaxis": {
                "tickprefix": currency_marker,
                "fixedrange": True
            },
            "xaxis": {
                "fixedrange": True,
                "type": "category"
            }
        }
    }
    return net_margin_chart, spend_line_chart, sell_line_chart, profit_loss_chart, capital_gains_tax_chart
>>>>>>> dev

@app.callback(
    [
        Output("avg-asset-cost", "data"),
    ],
    [
        Input("investment-type-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
<<<<<<< HEAD
    ],
)
def update_table(investment_type, start_date, end_date):
=======
        Input("currency-filter", "value")
    ],
)
def update_table(investment_type, start_date, end_date, currency):
>>>>>>> dev
    mask = (
            (df["Investment Type"] == investment_type)
            & (df["Transaction Date"] >= start_date)
            & (df["Transaction Date"] <= end_date)
    )
    filtered_data = df.loc[mask, :]
<<<<<<< HEAD
=======
    filtered_data = convert_currency(filtered_data, currency_metrics, currency)
>>>>>>> dev
    avg_cost = avg_cost_per_asset(filtered_data)
    return [avg_cost.to_dict('records')]


if __name__ == "__main__":
    app.run_server(debug=True, host='127.0.0.1')
