import numpy as np
import pandas as pd
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input

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
                    children='My Investments Portfolio',
                    className="header-title",
                ),
                html.P(
                    children='''Including both my CRYPTO and STONKS assets.''',
                    className="header-description",
                ),
            ],
            className='header',
        ),

        # Net Spend Bar Chart
        html.Div(
            children=[

                # net spend
                html.Div(
                    children=[
                        html.Div(children="Investment Type", className="menu-title"),
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
                html.Div(
                    children=[
                        html.Div(
                            children="Date Range",
                            className="menu-title"
                            ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=df["Transaction Date"].min().date(),
                            max_date_allowed=df["Transaction Date"].max().date(),
                            start_date=df["Transaction Date"].min().date(),
                            end_date=df["Transaction Date"].max().date(),
                        ),
                    ]
                ),
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
                            columns=[{"id": i, "name": i} for i in avg_cost_cols],
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
                        id='stonks-net-spend',
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
        Output("stonks-net-spend", "figure")
    ],
    [
        Input("investment-type-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(investment_type, start_date, end_date):
    mask = (
        (df["Investment Type"] == investment_type)
        & (df["Transaction Date"] >= start_date)
        & (df["Transaction Date"] <= end_date)
    )
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
                'type': 'bar',
            },
        ],
        'layout': {
            'title': {
                'text': 'Investments Net Spend by Company',
                "x": 0.05,
                "xanchor": "left",
            },
            "yaxis": {
           #     "tickprefix": "€",
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
                'x': investments_daily.loc[investments_daily.Transaction == 'Buy', 'Transaction Date'],
                'y': investments_daily.loc[investments_daily.Transaction == 'Buy', 'Net Spend'],
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
                #  "tickprefix": "€",
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
                'x': investments_daily.loc[investments_daily.Transaction == 'Sell', 'Transaction Date'],
                'y': investments_daily.loc[investments_daily.Transaction == 'Sell', 'Net Spend'],
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
                #  "tickprefix": "€",
                "fixedrange": True
            },
            "xaxis": {
                "fixedrange": True
            }
        }
    }

    # p and l
    p_and_l_chart = {
        'data': [
            {
                'x': p_and_l['Company'],
                'y': p_and_l['Total Price'],
                'type': 'bar',
            },
        ],
        'layout': {
            'title': {
                'text': 'Profit and Loss (Completely Sold Assets)',
                "x": 0.05,
                "xanchor": "left",
            },
            "yaxis": {
                #     "tickprefix": "$",
                "fixedrange": True
            },
            "xaxis": {
                "fixedrange": True
            }
        }
    }
    return net_spend_chart, spend_line_chart, sell_line_chart, p_and_l_chart

@app.callback(
    [
        Output("avg-asset-cost", "data"),
    ],
    [
        Input("investment-type-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_table(investment_type, start_date, end_date):
    mask = (
            (df["Investment Type"] == investment_type)
            & (df["Transaction Date"] >= start_date)
            & (df["Transaction Date"] <= end_date)
    )
    filtered_data = df.loc[mask, :]
    avg_cost = avg_cost_per_asset(filtered_data)
    return [avg_cost.to_dict('records')]


if __name__ == "__main__":
    app.run_server(debug=True, host='127.0.0.1')
