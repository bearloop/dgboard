
# from dash_bootstrap_components._components.Row import Row
# from dash_bootstrap_components._components.Spinner import Spinner
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_table

from dg_connect import dg_get_portfolio, dg_get_product, portfolio_metrics_tables, dg_mod_dietz_ret, _datetime, _pd#, _timedelta
from app import app, dbc
from utils import navbar, format_data_conditional, format_header, format_cell, json#, format_table
import visuals as vs

print('got in L2')

##########################################################################################
card_1 = dbc.Card(
                        [
                            dbc.CardHeader("Portfolio Snapshot"),
                            dbc.CardBody(
                                [ #dbc.Spinner(children=[
                                    html.Div(children=[
                                        dash_table.DataTable(id='portOverview',
                                                            style_table={'maxHeight':'300px'},
                                                            style_data_conditional=format_data_conditional,
                                                            style_header=format_header,
                                                            style_cell=format_cell,
                                                            derived_virtual_row_ids=[],
                                                            cell_selectable=False),
                               
                                        dash_table.DataTable(id='portRisk',
                                                            style_table={'maxHeight':'300px'},
                                                            style_data_conditional=format_data_conditional,
                                                            style_header=format_header,
                                                            style_cell=format_cell,
                                                            derived_virtual_row_ids=[],
                                                            cell_selectable=False),

                                        dash_table.DataTable(id='portPerf',
                                                            style_table={'maxHeight':'300px'},
                                                            style_data_conditional=format_data_conditional,
                                                            style_header=format_header,
                                                            style_cell=format_cell,
                                                            derived_virtual_row_ids=[],
                                                            cell_selectable=False),
                                        ],
                                    style={'overflow':'scroll','maxHeight':'510px'}
                                )
                                #], id='card_spinner_1')
                                ], className="p-2"),
                            dbc.CardFooter()
                        ], className="m-4", style={'minHeight':'600px','maxHeight':'600px'}
                       )

styled = {'minWidth':'500px','maxWidth':'500px','minHeight':'255px','maxHeight':'255px'}
card_2 = dbc.Card(
                        [
                            dbc.CardHeader(
                                dbc.Row([
                                            dbc.Col(["Portfolio Performance"],width=8),
                                            dbc.Col(
                                                [dbc.DropdownMenu(
                                                    children=[
                                                        dbc.DropdownMenuItem("Since Inception", id="btn-inception", n_clicks=0),
                                                        dbc.DropdownMenuItem("Year-to-date", id="btn-ytd", n_clicks=0),
                                                        dbc.DropdownMenuItem("1-Year", id="btn-1year", n_clicks=0),                                               
                                                        dbc.DropdownMenuItem("6-Month", id="btn-6month", n_clicks=0),
                                                        dbc.DropdownMenuItem("3-Month", id="btn-3month", n_clicks=0),
                                                        dbc.DropdownMenuItem("1-Month",  id="btn-1month", n_clicks=0),
                                                        dbc.DropdownMenuItem("1-Week",  id="btn-1week", n_clicks=0)
                                                    ],
                                                    nav=False,
                                                    label="Date Range: 1Y",
                                                    right=True,
                                                    size="sm",
                                                    id='target_date',
                                                    style={'padding-left':'20px'}
                                                ),
                                                    #html.Div(id="srch_results")
                                            ],width=4),
                                            
                                        ])
                                        ),
                            dbc.CardBody(
                                [
                                 #dbc.Spinner(children=[
                                        dbc.CardBody(dcc.Graph(id="fig_test_1"), style=styled),
                                        dbc.CardBody(dcc.Graph(id="fig_test_2"), style=styled)
                                 
                                 #],id='card_spinner_2')
                                ], className="p-2"),
                            dbc.CardFooter()
                        ], className="m-4", style={'minHeight':'600px','maxHeight':'600px'}
                       )


card_3 = dbc.Card(
                        [
                            dbc.CardHeader("Asset Allocation"),
                            dbc.CardBody(
                                [
                                   dbc.Row([
                                        dbc.Col(dcc.Graph(id="fig_test_3"),width=7),#style={'margin-left':'5px'})
                                        dbc.Col(dcc.Graph(id="fig_test_4"),width=5)#style={'margin-right':'5px'}
                                   ]
                                 )
                                ], className="p-2"),
                            dbc.CardFooter()
                        ], className="m-4", style={'minHeight':'280px','maxHeight':'280px'}
                       )

##########################################################################################
def create_layout_2():

    return html.Div([
                    dbc.Row(className="mb-4"),
                    navbar,
                    dbc.Spinner(
                        children=[
                             dbc.Row([
                                 dbc.Col([card_1],width=4),
                                 dbc.Col([card_2],width=8),
                                 dcc.Store(id="dgdata_layout2", storage_type="memory", data='Empty'),
                            ]),
                             dbc.Row([dbc.Col([card_3])])
                        ]
                    )
                    
                    ], className="page",
                )

layout2 = create_layout_2()

@app.callback(
    [Output('portOverview', 'data'),
     Output('portOverview', 'columns'),
     Output('portRisk',     'data'),
     Output('portRisk',     'columns'),
     Output('portPerf',     'data'),
     Output('portPerf',     'columns'),
     Output('fig_test_1',   'figure'),
     Output('fig_test_2',   'figure'),
     Output('fig_test_3',   'figure'),
     Output('fig_test_4',   'figure'),
     Output('target_date',  'label'),
     Output('dgdata_layout2',  'data')
     ],
    [Input('fetched_data',  'data'),
     Input("btn-inception", 'n_clicks_timestamp'),
     Input("btn-ytd",       'n_clicks_timestamp'),
     Input("btn-1year",     'n_clicks_timestamp'),
     Input("btn-6month",    'n_clicks_timestamp'),
     Input("btn-3month",    'n_clicks_timestamp'),
     Input("btn-1month",    'n_clicks_timestamp'),
     Input("btn-1week",     'n_clicks_timestamp')
     ],
     [State('dgdata_layout2', 'data')]
     )
def display_value(input_d, btn_inception, btn_ytd, btn_1yr, 
                           btn_6mo, btn_3mo, btn_1mo, btn_1wk, dgdata_l2):

    trad_days_in_a_month = 21

    ove_cols = [{"name": ' ', "id": ' '},{"name": 'Overview', "id": 'Overview'}]
    rsk_cols = [{"name": ' ', "id": ' '},{"name": 'Risk Metrics', "id": 'Risk Metrics'}]
    prf_cols = [{"name": ' ', "id": ' '},{"name": 'Performance', "id": 'Performance'}]

    listedTimestamps = [btn_inception, btn_ytd, btn_1yr, btn_6mo, btn_3mo, btn_1mo, btn_1wk]
    listedTimestamps = [0 if v is None else v for v in listedTimestamps]
    sortedTimestamps = sorted(listedTimestamps)

    try:
        res = dg_get_product('SWDA', input_d, search_limit=2, product_type='ETFs')
        print(res)
    except:
        print('updating input')
        input_d = {}

    if (input_d is None) or (len(input_d)<1):

        if (input_d is None): input_d = {}

        ove_dt = [  {' ': 'Period Start', 'Overview': 'N/A'},
                    {' ': 'Period End', 'Overview': 'N/A'},
                    {' ': 'Period Length', 'Overview': 'N/A'},
                    {' ': 'Start Value', 'Overview': 'N/A'},
                    {' ': 'Invested Capital', 'Overview': 'N/A'},
                    {' ': 'Weighted Flows', 'Overview': 'N/A'},
                    {' ': 'Last Value', 'Overview': 'N/A'},
                    {' ': 'Ret/Vol Ratio', 'Overview': 'N/A'} ]

        rsk_dt = [  {' ': 'Stand Dev (Ann)', 'Risk Metrics': 'N/A'},
                    {' ': 'Stand Dev', 'Risk Metrics': 'N/A'},
                    {' ': 'Skewness', 'Risk Metrics': 'N/A'},
                    {' ': 'Kurtosis', 'Risk Metrics': 'N/A'},
                    {' ': 'VaR 1-month', 'Risk Metrics': 'N/A'},
                    {' ': 'Max Drawdown', 'Risk Metrics': 'N/A'},
                    {' ': 'Last Drawdown', 'Risk Metrics': 'N/A'} ]
        
        prf_dt = [  {' ': '1-week Ret', 'Performance': 'N/A'},
                    {' ': '1-month Ret', 'Performance': 'N/A'},
                    {' ': '3-month Ret', 'Performance': 'N/A'},
                    {' ': 'Mean Ret', 'Performance': 'N/A'},
                    {' ': 'Best Ret', 'Performance': 'N/A'},
                    {' ': 'Worst Ret', 'Performance': 'N/A'},
                    {' ': 'Mean Ret (Ann)', 'Performance': 'N/A'},
                    {' ': 'Total Ret', 'Performance': 'N/A'},
                    {' ': 'CAGR', 'Performance': 'N/A'},
                    {' ': 'Mod Dietz Ret', 'Performance': 'N/A'} ]
        
        fig_1 = vs.graph_index('line', None, 'Portfolio Performance Index')
        fig_2 = vs.graph_index('bar', None, 'Portfolio Returns (%)')
        fig_3 = vs.graph_weights('area', None, 'Historical Holdings Weights (%)')
        fig_4 = vs.graph_weights('pie', None, 'Current Holdings Weights (%)')

        dgdata_l2 = 'Empty'

        date_range = 'Date Range'
        print('Not logged in')

    else:
        print('LOGGED IN ')
        
        if dgdata_l2 == 'Empty':
            pVal, weights, units, cost, fees, symbols, current_hold_prices =  dg_get_portfolio(input_d, dates_auto= 'P4Y', dates_start=None, dates_end=None)
            
            datasets = {
                'pVal': pVal.to_json(orient='split', date_format='iso'),  # pd
                'weights': weights.to_json(orient='split', date_format='iso'),
                'symbols': json.dumps(symbols)# dict
                }
            dgdata_l2 = json.dumps(datasets) 
        else:
            # Read data - assumes dgdata_l2 is a seriealised json
            datasets = json.loads(dgdata_l2)
            pVal = _pd.read_json(datasets['pVal'], orient='split')
            weights = _pd.read_json(datasets['weights'], orient='split')
            symbols = json.loads(datasets['symbols'])
        
        # Drop first N rows where index = 1 -> essentially, start from inception date
        pVal_ind = pVal.Index.iloc[(pVal.Index!=1).argmax()-1:]

        if btn_ytd == sortedTimestamps[-1]:
            last_year_end = _datetime.now().date().replace(year=_datetime.now().year-1, month=12, day=31)
            today_date =_datetime.now().date()
            period = (today_date-last_year_end).days #'YTD'
            date_range = 'Date Range: YTD'
            pVal_ind = pVal_ind.loc[last_year_end:]
            
        else:
            if btn_inception == sortedTimestamps[-1]:
                period = len(pVal_ind) # all other cases portfolio since inception
                date_range = 'Date Range: SI'

            elif btn_6mo == sortedTimestamps[-1]: 
                period = 6 * trad_days_in_a_month + 1 # period = 'P6M'   
                date_range = 'Date Range: 6M'

            elif btn_3mo == sortedTimestamps[-1]:
                period = 3 * trad_days_in_a_month + 1 # period = 'P3M'
                date_range = 'Date Range: 3M'

            elif btn_1mo == sortedTimestamps[-1]:
                period = 1 * trad_days_in_a_month + 1# period = 'P1M'
                date_range = 'Date Range: 1M'

            elif btn_1wk == sortedTimestamps[-1]:
                period = 5 + 1# period = 'P1W' - 5 trading days
                date_range = 'Date Range: 1W'
            else:
                period = 12 * trad_days_in_a_month + 1 # period = 'P1Y'
                date_range = 'Date Range: 1Y'

            # Select period
            if len(pVal_ind)>=period: pVal_ind = pVal_ind.iloc[-period:]

        # Normalise index
        pVal_ind = pVal_ind.pct_change().add(1).cumprod().fillna(1)

        # Table metrics
        capital = dg_mod_dietz_ret(pVal.loc[pVal_ind.index])
        ove, risk, perf  = portfolio_metrics_tables(ts_df=pVal_ind,
                                                    capital_df=capital,
                                                    trading_days=trad_days_in_a_month)
        
        ove_dt, rsk_dt, prf_dt = [],[],[]

        for i in ove.index:  ove_dt.append({' ':i, ove_cols[1]['name']: ove.loc[i][0]})
        for i in risk.index: rsk_dt.append({' ':i, rsk_cols[1]['name']: risk.loc[i][0]})
        for i in perf.index: prf_dt.append({' ':i, prf_cols[1]['name']: perf.loc[i][0]})

        # Charts prep
        if period > 70:
            rs = 5 # weekly portfolio returns
            if period > 250:
                rs = trad_days_in_a_month # monthly portfolio returns
            data_pct = pVal_ind.pct_change(rs).dropna().iloc[::-1][::rs][::-1]
        
        else: data_pct = pVal_ind.pct_change().dropna() # daily portfolio returns

        weights = weights.rename(columns=symbols) # rename columns
        weights = weights.iloc[-3 * trad_days_in_a_month:,:].drop(['valueTotal','netFlows','valueAdjusted','indexRet','Index'],axis=1)
        weights = weights.T[(weights.sum()!=0)].T  # drops non-asset columns and non-current holdings
        curr_weights = _pd.DataFrame(weights.iloc[-1])
        curr_weights.columns = [curr_weights.columns[0].strftime("%d-%m-%Y")] #Transform datetime

        # print(date_range)
        # print(data_pct)
        
        # Charts
        fig_1 = vs.graph_index('line', pVal_ind, 'Portfolio Performance Index')
        fig_2 = vs.graph_index('bar', data_pct, 'Portfolio Returns (%)')
        fig_3 = vs.graph_weights('area', weights, 'Historical Holdings Weights (%)')
        fig_4 = vs.graph_weights('pie', curr_weights, 'Current Holdings Weights (%)')

    return ove_dt, ove_cols, rsk_dt, rsk_cols, prf_dt, prf_cols, fig_1, fig_2, fig_3, fig_4, date_range, dgdata_l2