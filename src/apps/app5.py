
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app, dbc
from utils import navbar

print('got in L5')

##########################################################################################

card_1 = dbc.Card(
                        [
                            dbc.CardHeader("Holdings Summary"),
                            dbc.CardBody(
                                [
                                   dbc.Row([
                                        
                                   ]
                                 )
                                ], className="p-2"),
                            dbc.CardFooter()
                        ], className="m-4", style={'minHeight':'300px','maxHeight':'300px'}
                       )

card_3 = dbc.Card(
                        [
                            dbc.CardHeader("Historical Transactions"),
                            dbc.CardBody(
                                [
                                   dbc.Row([
                                        
                                   ]
                                 )
                                ], className="p-2"),
                            dbc.CardFooter()
                        ], className="m-4", style={'minHeight':'560px','maxHeight':'560px'}
                       )

##########################################################################################

def create_layout_5():

    return html.Div([
                    dbc.Row(className="mb-4"),
                    navbar,
                    dbc.Spinner(
                        children=[
                             dbc.Row([dbc.Col([card_1])]),
                             dbc.Row([dbc.Col([card_3])]),
                        ]
                    )
                    ], className="page",
                )

layout5 = create_layout_5()
# @app.callback(
#     Output('app-2-display-value', 'children'),
#     Input('app-2-dropdown', 'value'))
# def display_value(value):
#     return 'You have selected "{}"'.format(value)