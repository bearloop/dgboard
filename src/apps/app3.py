
from dash_bootstrap_components._components import RadioItems
from dash_bootstrap_components._components.InputGroup import InputGroup
from dash_bootstrap_components._components.Label import Label
from dash_bootstrap_components._components.RadioButton import RadioButton
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from numpy.lib.function_base import select

from dg_connect import dg_get_portfolio, dg_get_product, calc_basics, calc_correl, calc_ddown, calc_value_at_risk, _datetime, _pd#, _timedelta
from app import app, dbc
from utils import navbar, json
import visuals as vs

print('got in L3')

##########################################################################################

styled = {'minWidth':'800px','maxWidth':'800px','minHeight':'230px','maxHeight':'230px','margin-bottom':'-15px'}
styled_2 = {'minWidth':'800px','maxWidth':'800px','minHeight':'460px','maxHeight':'460px','margin-bottom':'-15px'}

card_1 = dbc.Card(
                        [
                            dbc.CardHeader(
                                dbc.Row([
                                            dbc.Col(["Price Performance"],width=10, id='header_performance'),
                                            dbc.Col(
                                                [dbc.DropdownMenu(
                                                    children=[
                                                        dbc.DropdownMenuItem("Since Inception", id="btn-inception", n_clicks=0),
                                                        dbc.DropdownMenuItem("Year-to-date", id="btn-ytd", n_clicks=0),
                                                        dbc.DropdownMenuItem("1-Year", id="btn-1year", n_clicks=0),                                               
                                                        dbc.DropdownMenuItem("6-Month", id="btn-6month", n_clicks=0),
                                                        dbc.DropdownMenuItem("3-Month", id="btn-3month", n_clicks=0)
                                                    ],
                                                    nav=False,
                                                    label="Date Range",
                                                    right=True,
                                                    size="sm",
                                                    id='target_date_2',
                                                    style={'padding-left':'5px'}
                                                ),
                                            ],width=2),
                                            
                                        ])
                                        ),
                            dbc.CardBody(
                                [
                                    dbc.CardBody(dcc.Graph(id="fig_assets_1",style={}), style=styled),

                                ], className="p-2"),
                            dbc.CardFooter()
                        ], className="m-4", style={'minHeight':'300px','maxHeight':'300px'}
                       )

assets_checklist = html.Div(
    [
        dbc.Label("Choose a bunch"),
        dbc.Checklist(
            options=[{"label": "Placeholder", "value": 1}],
            id="checklist-input",
            value=[1]
        ),
    ],style={'maxHeight':'200px','margin-left':'20px','padding-left':'8px','overflowY': 'scroll', 'font-weight':'200'}
)

card_2 = dbc.Card(
                        [
                            dbc.CardHeader(
                                            dbc.Row([
                                                dbc.Col(["Risk Metrics"],width=10, id='header_risk'),
                                                dbc.Col(
                                                    [dbc.DropdownMenu(
                                                    children=[
                                                        # dbc.DropdownMenuItem([dbc.Checkbox(style={'margin-right':'5pt'},className='custom_cb',id='cb_x3'),'X3_ajhsbx'],id="text_x3",toggle=False),
                                                        # dbc.DropdownMenuItem([dbc.Checkbox(style={'margin-right':'5pt'},className='custom_cb',id='cb_x4'),'X4_ajhsbx'],id="text_x4",toggle=False),
                                                        # dbc.DropdownMenuItem([dbc.Checkbox(style={'margin-right':'5pt'},className='custom_cb',id='cb_x5'),'X5_ajhsbx'],id="text_x5",toggle=False),
                                                        #dbc.DropdownMenuItem([rr],id="text_x6",toggle=False)
                                                        assets_checklist
                                                    ],
                                                    label="Holdings",
                                                    right=True,
                                                    size="sm",
                                                    id='select_assets',
                                                    style={'padding-left':'5px'}
                                                ),
                                                ]
                                                ,width=2),
                                                
                                            ])
                                        ),
                            dbc.CardBody(
                                [
                                   dbc.CardBody(
                                        
                                            dbc.Row([
                                                 dbc.Col(
                                                    [dcc.Graph(id="fig_assets_2"),dcc.Graph(id="fig_assets_4")],width=6),
                                                dbc.Col(
                                                    [dcc.Graph(id="fig_assets_3"),dcc.Graph(id="fig_assets_5")],width=6),
                                             ]),
                                            
                                        style=styled_2),

                                ], className="p-2"),
                            dbc.CardFooter()
                        ], className="m-4", style={'minHeight':'560px','maxHeight':'560px'}
                       )

##########################################################################################

def create_layout_3():

    return html.Div([
                    dbc.Row(className="mb-4"),
                    navbar,
                    dbc.Spinner(
                        children=[
                             dbc.Row([dbc.Col([card_1])]),
                             dbc.Row([dbc.Col([card_2])]),
                             dcc.Store(id="dgdata_layout3", storage_type="memory", data='Empty'),
                        ]
                    )
                    ], className="page",
                )

layout3 = create_layout_3()


@app.callback(
    [Output('fig_assets_1',   'figure'),
     Output('fig_assets_2',   'figure'),
     Output('fig_assets_3',   'figure'),
     Output('fig_assets_4',   'figure'),
     Output('fig_assets_5',   'figure'),
     #Output('target_date_2',  'label'),
     Output('header_performance',  'children'),
     Output('checklist-input', 'options'),
     Output('checklist-input', 'value'),
     Output('dgdata_layout3',  'data')
     ],
    [Input('fetched_data',  'data'),
     Input("btn-inception", 'n_clicks_timestamp'),
     Input("btn-ytd",       'n_clicks_timestamp'),
     Input("btn-1year",     'n_clicks_timestamp'),
     Input("btn-6month",    'n_clicks_timestamp'),
     Input("btn-3month",    'n_clicks_timestamp'),
     Input('checklist-input', 'value')],
    [
     State('checklist-input', 'options'),
     State('dgdata_layout3',  'data')],
     )
def display_value(input_d, btn_inception, btn_ytd, btn_1yr, 
                           btn_6mo, btn_3mo, chlist_input, chlist_options, dgdata_l3):

    trad_days_in_a_month = 21

    listedTimestamps = [btn_inception, btn_ytd, btn_1yr, btn_6mo, btn_3mo]
    listedTimestamps = [0 if v is None else v for v in listedTimestamps]
    sortedTimestamps = sorted(listedTimestamps)

    try:
        res = dg_get_product('SWDA', input_d, search_limit=2, product_type='ETFs')
        print(res)
    except:
        print('updating input')
        input_d = {}

    if (input_d is None) or (len(input_d)<=1):

        if (input_d is None): input_d = {}
        
        fig_1 = vs.graph_small_index(data_df=None, chart_title='Cumulative Return', show_legend=False)
        fig_2 = vs.graph_small_index(data_df=None, chart_title='Annualised Volatility (%)', width=395, show_legend=False)
        fig_3 = vs.graph_small_index(data_df=None, chart_title='Drawdown (%)', width=395, show_legend=False)
        fig_4 = vs.graph_small_index(data_df=None, chart_title='Value-at-risk (%)',  width=395, show_legend=False)
        fig_5 = vs.graph_small_index(data_df=None, chart_title='Mean Pairwise Correlation', width=395, show_legend=False)
        
        dgdata_l3 = 'Empty'
        # print(dgdata_l3)
        # Do not update chlist_options and chlist_input
        # chlist_options = [{"label": "Placeholder", "value": 1}]
        # chlist_input = [1]
        
        #date_range = 'Date Range'
        header_performance = ['Price Performance']
        
        print('Not logged in')

    else:
        print('LOGGED IN ')
        
        if dgdata_l3 == 'Empty':
            #print(dgdata_l3)
            pVal, weights, units, cost, fees, symbols, current_hold_prices =  dg_get_portfolio(input_d, dates_auto= 'P4Y', dates_start=None, dates_end=None)

            datasets = {
                'pVal': pVal.to_json(orient='split', date_format='iso'),
                'current_hold_prices': current_hold_prices.to_json(orient='split', date_format='iso')
                }
            dgdata_l3 = json.dumps(datasets) 
            #print(dgdata_l3)       
        else:
            # Read data - assumes dgdata_l3 is a seriealised json
            datasets = json.loads(dgdata_l3)
            pVal = _pd.read_json(datasets['pVal'], orient='split')
            current_hold_prices = _pd.read_json(datasets['current_hold_prices'], orient='split')

        # Drop first N rows where index = 1 -> essentially, start from inception date
        pVal_ind = pVal.Index.iloc[(pVal.Index!=1).argmax()-1:]

        if btn_ytd == sortedTimestamps[-1]:
            last_year_end = _datetime.now().date().replace(year=_datetime.now().year-1, month=12, day=31)
            today_date =_datetime.now().date()
            period = (today_date-last_year_end).days #'YTD'
            date_range = 'YTD'
            pVal_ind = pVal_ind.loc[last_year_end:]
            
        else:
            if btn_inception == sortedTimestamps[-1]:
                period = len(pVal_ind) # all other cases portfolio since inception
                date_range = 'SI'

            elif btn_6mo == sortedTimestamps[-1]: 
                period = 6 * trad_days_in_a_month + 1 # period = 'P6M'   
                date_range = '6M'

            elif btn_3mo == sortedTimestamps[-1]:
                period = 3 * trad_days_in_a_month + 1 # period = 'P3M'
                date_range = '3M'

            # elif btn_1mo == sortedTimestamps[-1]:
            #     period = 1 * trad_days_in_a_month + 1# period = 'P1M'
            #     date_range = 'Date Range: 1M'

            # elif btn_1wk == sortedTimestamps[-1]:
            #     period = 5 + 1# period = 'P1W' - 5 trading days
            #     date_range = 'Date Range: 1W'
            else:
                period = 12 * trad_days_in_a_month + 1 # period = 'P1Y'
                date_range = '1Yr'

            # Select period
            if len(pVal_ind)>=period: pVal_ind = pVal_ind.iloc[-period:]

        # Normalise index
        # pVal_ind = pVal_ind.pct_change().add(1).cumprod().fillna(1)

        # Prices
        pVal_ind = pVal_ind.rename('Portfolio')
        current_hold_prices = _pd.concat([pVal_ind, current_hold_prices],axis=1).loc[pVal_ind.index]

        # Figure out selected input and options
        if len(chlist_input)==1:
            if chlist_options[0]['label'] == 'Placeholder':
                chlist_options = []
                chlist_input = []
                val = 1
                for asset_label in current_hold_prices.columns:
                    chlist_options.append({"label": asset_label, "value": val})
                    chlist_input.append(val)
                    val += 1
                print(chlist_options)
                print(chlist_input)
        
        selected_assets_values = []
        for i in chlist_input:
            selected_assets_values.append(i-1)
        # for i in chlist_input:
        #     for j in chlist_options:
        #         if j['value'] == i:
        #                 selected_assets_values.append(j['label'])
        # print('Pass')
        #print(chlist_options)
        #print(chlist_input)
        current_hold_prices = current_hold_prices.iloc[-period:,selected_assets_values]

        # Charts
        if len(current_hold_prices.columns) >= 1:
            # Calculations
            ret   = calc_basics(current_hold_prices)
            vol   = calc_basics(current_hold_prices, how='vol')
            var   = calc_value_at_risk(current_hold_prices,drop_nulls=False,lookback=21)
            ddown = calc_ddown(current_hold_prices)

            fig_1 = vs.graph_small_index(data_df=ret, chart_title='Cumulative Return')
            fig_2 = vs.graph_small_index(data_df=vol, chart_title='Annualised Volatility (%)', width=395, show_legend=False)
            fig_3 = vs.graph_small_index(data_df=ddown, chart_title='Drawdown (%)', width=395, show_legend=False)
            fig_4 = vs.graph_small_index(data_df=var, chart_title='Value-at-risk (%)', width=395, show_legend=False)
        else:
            fig_1 = vs.graph_small_index(data_df=None, chart_title='Cumulative Return', show_legend=False)
            fig_2 = vs.graph_small_index(data_df=None, chart_title='Annualised Volatility (%)', width=395, show_legend=False)
            fig_3 = vs.graph_small_index(data_df=None, chart_title='Drawdown (%)', width=395, show_legend=False)
            fig_4 = vs.graph_small_index(data_df=None, chart_title='Value-at-risk (%)',  width=395, show_legend=False)
        
        # Exclude Portfolio Index from pairwise correlation
        if 'Portfolio' in current_hold_prices.columns:
                current_hold_prices  = current_hold_prices.drop(['Portfolio'],axis=1)

        if len(current_hold_prices.columns) >= 2:
            corr  = calc_correl(current_hold_prices, how='corr') 
            fig_5 = vs.graph_small_index(data_df=corr, chart_title='Mean Pairwise Correlation', width=395, show_legend=False)
        else:
            fig_5 = vs.graph_small_index(data_df=None, chart_title='Mean Pairwise Correlation', width=395, show_legend=False)


        header_performance = ['Price Performance - ' + date_range]

    return fig_1, fig_2, fig_3, fig_4, fig_5, header_performance, chlist_options, chlist_input, dgdata_l3