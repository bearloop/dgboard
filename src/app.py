import dash
import dash_bootstrap_components as dbc
import pandas as pd


app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.FLATLY],
                suppress_callback_exceptions=True
                )

#app.css.append_css({'external_url': 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css'})

app.title = "Portfolio Reporting"

server = app.server

print('server is up')


