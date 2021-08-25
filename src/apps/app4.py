
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table
from dash_table import FormatTemplate

from app import app, dbc
from utils import navbar, format_markets_table, format_data_conditional, format_header, format_cell, readFav
from dg_connect import dg_vwd_retrieve, _pd

print('got in L4')

percentage = FormatTemplate.percentage(2)
##########################################################################################

card_1 = dbc.Card([
                      dbc.CardHeader("Equities & ETFs List"),
                        
                            dbc.CardBody(
                                [
                                   dbc.Row([
                                        dash_table.DataTable(id='markets',
                                                            style_table=format_markets_table,
                                                            style_data_conditional=format_data_conditional,
                                                            style_header=format_header,
                                                            style_cell=format_cell,
                                                            derived_virtual_row_ids=[],
                                                            cell_selectable=False,
                                                            sort_action='native')
                                   ]
                                 )
                                ], className="p-2"),
                            dbc.CardFooter()
                        ], className="m-4", style={'minHeight':'900px','maxHeight':'900px'}
                       )

##########################################################################################

def create_layout_4():

    return html.Div([
                    dbc.Row(className="mb-4"),
                    navbar,
                    dbc.Spinner(
                        children=[
                             dbc.Row([dbc.Col([card_1])])
                        ]
                    )
                    ], className="page",
                )

layout4 = create_layout_4()


@app.callback(
    [Output("markets", "data"),
     Output("markets", "columns"),
     Output("markets", "style_data_conditional")],
    [Input("fetched_data","data"),
     Input("fav_table_data","data")]
)
def show_markets(input_d, fav_table_data):
    table_col_names_a = ['Symbol','Description','Last Price','FX']
    table_col_names_b = ['Ret 1w','Ret 1m','Ret 3m','Ret 1Yr','SD 1m','SD 1Yr','VaR 1m']
    
    # table_fixed_rows={'headers': True, 'data':0}

    # Show an empty markets table if:
    # a) you're not logged in
    # b) you're logged in but the fav table is empty

    if (input_d is None) or (len(input_d)<=1) or (fav_table_data is None) or (len(fav_table_data)<1):
        table_columns = [dict(id=i, name=i) for i in table_col_names_a+table_col_names_b]
        table_data = [{'Symbol':'','Description':'','Last Price':'','FX':'',
                       'Ret 1w':'','Ret 1m':'','Ret 3m':'','Ret 1Yr':'','SD 1m':'','SD 1Yr':'','VaR 1m':''} for row in range(30)]
        
        return table_data, table_columns, format_data_conditional

    # Otherwise, you must be logged in and have some fav assets
    else:
        
        table_columns = [dict(id=i, name=i) for i in table_col_names_a] + [dict(id=i, name=i, type='numeric', format=percentage) for i in table_col_names_b]

        df, curr_dct, desc_dct = return_assets_ts(input_d)

        table_data = []
        for asset in df.columns:
            table_data.append({
                    'Symbol':asset,
                    'Description':desc_dct[asset],
                    'Last Price': df[asset][-1],
                    'FX': curr_dct[asset],
                    'Ret 1w':value_rt_vol(df[asset],periods=5,op_type='rt'),
                    'Ret 1m':value_rt_vol(df[asset],periods=21,op_type='rt'),
                    'Ret 3m':value_rt_vol(df[asset],periods=63,op_type='rt'),
                    'Ret 1Yr':value_rt_vol(df[asset],periods=252,op_type='rt'),
                    'SD 1m':value_rt_vol(df[asset],periods=21,op_type='vol'),
                    'SD 1Yr':value_rt_vol(df[asset],periods=252,op_type='vol'),
                    'VaR 1m':value_rt_vol(df[asset],periods=21,op_type='var')
                })

        cells_style = return_conditional_styles(table_data)
        return table_data, table_columns, cells_style


def return_assets_ts(input_d):
    '''
    returns a dataframe with price time series data
    '''
    fav_assets = readFav()
    df, df_names = dg_vwd_retrieve(input_d,list(fav_assets.vwdId.values), per_auto='13M')
    
    df_names_reverse = {}
    for asset in df_names: df_names_reverse[df_names[asset]] = asset

    rep = {}
    for i,j in zip(fav_assets.symbol,fav_assets.vwdId): rep[j]=i

    df = df.rename(columns = df_names_reverse).rename(columns = rep)

    # FX
    fx_dct = {}
    for sym, fx in zip(fav_assets.symbol,fav_assets.currency): fx_dct[sym] = fx

    # Product description
    name_dct = {}
    for sym, prodName in zip(fav_assets.symbol,fav_assets.name): name_dct[sym] = prodName[:26]

    return df, fx_dct, name_dct




def value_rt_vol(df,periods,op_type='rt'):

    if op_type=='rt':
        return df.pct_change(periods)[-1]
    elif op_type=='vol':
        return df.pct_change()[-periods:].std()*(252**(1/2))
    elif op_type=='var':
        conf = 0.05
        forward_per = 21
        return df.pct_change()[-periods:].dropna().quantile(1-conf)*(forward_per**(1/2))




def return_conditional_styles(table_data):

    cols = ['Ret 1w','Ret 1m','Ret 3m','Ret 1Yr']
    cols_sd = ['SD 1m','SD 1Yr','VaR 1m']
    cond_style = (
            [
                {
                    'if': {'column_id': c},
                    'textAlign': 'center'
                } for c in cols+cols_sd
            ]+
            [   
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#ffffff',
                    'border': '1px solid rgb(255, 255, 255)'
                }
            ] +
            [
                {
                    'if': {
                        'filter_query': '{{{}}} <= {}'.format(col, value),
                        'column_id': col
                    },
                    'backgroundColor': '#ffe1a8', # color: orange
                    'borderLeft': '1px solid rgb(255, 255, 255)',
                    'borderRight': '1px solid rgb(255, 255, 255)'
                } for (col, value) in _pd.DataFrame(table_data)[cols].quantile(0.5).iteritems()
            ] +
            [
                {
                    'if': {
                        'filter_query': '{{{}}} <= {}'.format(col, value),
                        'column_id': col
                    },
                    'backgroundColor': '#f1a782', # color: red
                    'borderLeft': '1px solid rgb(255, 255, 255)',
                    'borderRight': '1px solid rgb(255, 255, 255)'
                } for (col, value) in _pd.DataFrame(table_data)[cols].quantile(0.25).iteritems()
            ] +
            [
                {
                    'if': {
                        'filter_query': '{{{}}} > {}'.format(col, value),
                        'column_id': col
                    },
                    'backgroundColor': '#b1d4d5', # color: light green
                    'borderLeft': '1px solid rgb(255, 255, 255)',
                    'borderRight': '1px solid rgb(255, 255, 255)'
                } for (col, value) in _pd.DataFrame(table_data)[cols].quantile(0.5).iteritems()
            ] +
            [
                {
                    'if': {
                        'filter_query': '{{{}}} > {}'.format(col, value),
                        'column_id': col
                    },
                    'backgroundColor': '#86bbbd', # color: green
                    'borderLeft': '1px solid rgb(255, 255, 255)',
                    'borderRight': '1px solid rgb(255, 255, 255)'
                    #'color': 'white'
                } for (col, value) in _pd.DataFrame(table_data)[cols].quantile(0.75).iteritems()
            ]
        )

    return cond_style