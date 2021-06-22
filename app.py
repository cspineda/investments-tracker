import numpy as np
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from forex_python.converter import CurrencyRates
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output, Input
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
                    children='Investments Portfolio',
                    className="header-title",
                ),
                html.P(
                    children='''Both my CRYPTO and STONKS assets.''',
                    className="header-description",
                ),
            ],
            className='header',
        ),

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
                            columns=[{"id": i, "name": i} for i in
                                     ['Company', 'Ticker', 'Quantity', 'Net Cost', 'Avg Cost']],
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
                        id='profit-loss',
                        config={"displayModeBar": False},
                    ),
                    className="card"
                ),

                # Capital Gains Tax
                html.Div(
                    dcc.Graph(
                        id='capital-gains',
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
        Output("profit-loss", "figure"),
        Output("capital-gains", "figure"),
    ],
    [
        Input("investment-type-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("currency-filter", "value"),
        Input("aggregation-filter", "value")
    ],
)
def update_charts(investment_type, start_date, end_date, currency, aggregation):
    mask = (
        (df["Investment Type"] == investment_type)
        & (df["Transaction Date"] >= start_date)
        & (df["Transaction Date"] <= end_date)
    )

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
                'type': 'bar',
            },
        ],
        'layout': {
            'title': {
                'text': 'Investments Net Margin by Company',
                "x": 0.05,
                "xanchor": "left",
            },
            "yaxis": {
                "tickprefix": currency_marker,
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
                'x': investments_daily.loc[investments_daily["Total Cost"] > 0, 'Transaction Date'],
                'y': investments_daily.loc[investments_daily["Total Cost"] > 0, 'Total Cost'],
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
                "tickprefix": currency_marker,
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
                'x': investments_daily.loc[investments_daily['Net Earnings'] > 0, 'Transaction Date'],
                'y': investments_daily.loc[investments_daily['Net Earnings'] > 0, 'Net Earnings'],
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
                "tickprefix": currency_marker,
                "fixedrange": True
            },
            "xaxis": {
                "fixedrange": True
            }
        }
    }

    # profit and loss
    profit_loss_chart = {
        'data': [
            {
                'x': profit_loss['Company'],
                'y': profit_loss['Profit/Loss'],
                'type': 'bar',
            },
        ],
        'layout': {
            'title': {
                'text': 'Profit and Loss',
                "x": 0.05,
                "xanchor": "left",
            },
            "yaxis": {
                "tickprefix": currency_marker,
                "fixedrange": True
            },
            "xaxis": {
                "fixedrange": True
            }
        }
    }

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

@app.callback(
    [
        Output("avg-asset-cost", "data"),
    ],
    [
        Input("investment-type-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("currency-filter", "value")
    ],
)
def update_table(investment_type, start_date, end_date, currency):
    mask = (
            (df["Investment Type"] == investment_type)
            & (df["Transaction Date"] >= start_date)
            & (df["Transaction Date"] <= end_date)
    )
    filtered_data = df.loc[mask, :]
    filtered_data = convert_currency(filtered_data, currency_metrics, currency)
    avg_cost = avg_cost_per_asset(filtered_data)
    return [avg_cost.to_dict('records')]


if __name__ == "__main__":
    app.run_server(debug=True, host='127.0.0.1')
