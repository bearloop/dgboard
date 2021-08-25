import dash_core_components as dcc
import dash_table
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from app import app, dbc, dash
# from ast import literal_eval
from utils import navbar, readFav, format_table, format_data_conditional, format_header, format_cell
from dg_connect import dg_get_data, dg_get_product
import pandas as pd
import json

print('got in L1:')

##########################################################################################
# Log in card

email_input = dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Username", addon_type="prepend"),
                            dbc.Input(type="text", id="input_usr", placeholder="Enter username",disabled=False)
                        ], size='sm',className="mt-2"
                    )

password_input = dbc.InputGroup(
                        [
                            dbc.InputGroupAddon("Password", addon_type="prepend"),
                            dbc.Input(type="password",id="input_psw", placeholder="Enter password",disabled=False)
                        ], size='sm',className="mt-2"
                    )

login_card = dbc.Card(
                            [
                                dbc.CardHeader("Degiro Login"),
                                dbc.CardBody(
                                    [dbc.Row([
                                        dbc.Col(email_input),
                                        dbc.Col(password_input),
                                        dbc.Col(dbc.Button(
                                            "Login",
                                            id="login_button",
                                            n_clicks=0,
                                            outline=True,
                                            className="mt-2 mb-2",
                                            block=True,
                                            size='sm',
                                            color="primary"
                                        ))])
                                         
                                    ], className="p-2"
                                ),
                                dbc.CardFooter()
                            ], className="m-4"
                    )

##########################################################################################
# Search card

search_card = dbc.Card(
                        [
                            dbc.CardHeader(
                                  dbc.Row([
                                            dbc.Col(["Favourites List"],width=8),
                                            dbc.Col(
                                                [
                                                    dbc.Input(id="input_srch", placeholder="Product search", type="text"),
                                                    html.Div(id="srch_results")
                                            ],width=4),
                                            
                                        ])),
                            dbc.CardBody(
                                [
                                    dash_table.DataTable(id='favTable',
                                                         style_table=format_table,
                                                         style_data_conditional=format_data_conditional,
                                                         style_header=format_header,
                                                         style_cell=format_cell,
                                                         editable=True,
                                                         row_deletable=True,
                                                         derived_virtual_row_ids=[],
                                                         cell_selectable=False,
                                                         sort_action='native'),
                                    dcc.Store(id="srch_dict", clear_data=True),
                                    dcc.Interval(
                                              id='interval-component',
                                              interval=1*1000, # in milliseconds
                                              n_intervals=0,
                                              max_intervals=1
                                        )
                                ], className="p-2"),
                            dbc.CardFooter()
                        ], className="m-4"
                       )
##########################################################################################
# Generate Layout 1

def create_layout_1():

    return html.Div([dbc.Row(className="mb-4"),
                    navbar,
                    dbc.Row([dbc.Col([login_card])]),
                    dbc.Row([dbc.Col([search_card])])

    ], className="page",
    )

layout1 = create_layout_1()

##########################################################################################
# User log in

@app.callback(
    [Output("fetched_data", "data"),
     Output("log_button_data", "data"),
     Output("login_button", "children"),
     Output("input_usr","disabled"),
     Output("input_psw","disabled")],
    [Input("login_button", "n_clicks")],
    state=[State("input_usr", "value"),
           State("input_psw", "value"),
           State("fetched_data", "data"),
           State("log_button_data", "data"),
           State("input_usr", "disabled"),
           State("input_psw", "disabled"),]
)
def update_output_div(n_clicks, input_usr, input_psw, fetched_data, login_button_name, usr_dis, psw_dis):

    # modified_timestamp (number; default -1): The last time the storage was modified.
    print('-------- Entered: update_output_div --------')
    if fetched_data is None:
        fetched_data = {}

    if login_button_name is None:
        login_button_name = "Login"

    print('User login - Length of fetched_data: ' + str(fetched_data)[:10])
    if n_clicks > 0:
        try:
            if login_button_name == "Login":
                fetched_data = dg_get_data(input_usr, input_psw)
                print('Type of fetched data: ' + str(type(fetched_data)))
                return fetched_data, "Logout", "Logout", True, True
            
            else:
                print("You just logged out.")
                return {}, "Login", "Login", False, False
        except:
            print("Unclear - returning what was passed")
            return fetched_data, login_button_name, login_button_name, usr_dis, psw_dis
    else:
        try:
            if len(fetched_data['session_id'])>5: # arbitrary threshold "session_id": "0C7B7263CAD83Y0D3F17424TE5B91184.prod_b_112_4"
                print("You are logged in")
                return fetched_data, "Logout", "Logout", True, True
        except:
            print("You are not logged in. You should login again.")
            return {}, "Login", "Login", False, False

##########################################################################################
# Product search

@app.callback(
    [Output("srch_results", "children"),
     Output("srch_dict", "data")],
    [Input("input_srch", "value")],
    [State("fetched_data", "data")]
)
def update_product_list(input_srch, fetched_data):
    
    print('-------- Entered: update_product_list --------')
    print('Product search - Length of fetched_data: ' + str(fetched_data)[:10])

    try:
        if len(fetched_data['session_id'])>5:
            try:       
                if input_srch is not None:

                    if  len(input_srch)<2:
                        print('Search input less than 2 chars')
                        return html.Div(hidden=True), ''

                    else:
                        try:

                            products_res = dg_get_product(
                                searchTerm=input_srch,
                                data_dct=fetched_data,#literal_eval(fetched_data),
                                search_limit=7,
                                product_type="All" #{'ETFs':'131','Stocks':'1'}
                            )
                            print(products_res)

                            if products_res["products"] is not None:

                                ddown_list = []
                                ind = 0
                                sup_dct = {}
                                for p in products_res["products"]:
                                    print(p)
                                    isin_val =p['isin']

                                    try: name_val = p["name"]
                                    except: name_val = ""

                                    try: sym_val = p["symbol"]
                                    except: sym_val = ""

                                    try: dg_id = p['id']
                                    except: dg_id = ""

                                    try: vw_id = p['vwdId']
                                    except: vw_id = ""

                                    try: vw_id_2 = p['vwdIdSecondary']
                                    except: vw_id_2 = ""

                                    try: int(vw_id) #check whether vwid is not a character
                                    except: 
                                        try:
                                            if vw_id_2 != "":
                                                vw_id = vw_id_2
                                        except:
                                            'Do not replace original vwid'

                                    try: exchange = p["exchangeId"]
                                    except: exchange = ""

                                    try: expRatio = p["totalExpenseRatio"]
                                    except: expRatio = ""

                                    try: prodType = p["productType"]
                                    except: prodType = ""

                                    try: currency = p["currency"]
                                    except: currency = ""

                                    sup_dct[ind] = {'id': dg_id, 'name': name_val,
                                                    'isin': isin_val,'symbol': sym_val,
                                                    'productType': prodType, 'currency': currency,
                                                    'exchangeId': exchange, 'vwdId': vw_id,'totalExpenseRatio': expRatio}
                                    print(' ')
                                    print(sup_dct[ind])
                                    print(' ')
                                    heading = dbc.ListGroupItemHeading(str(name_val))
                                    txt = dbc.ListGroupItemText("ISIN: " + str(isin_val) + ' | ' + str(sym_val) + ' | EXCH:' + str(exchange))
                                    
                                    ddown_list.append(dbc.ListGroupItem([heading, txt], id="button-item-"+str(ind), n_clicks=0, action=True))
                                    #print(ind)
                                    ind+=1
                                    
                                ddown_group = dbc.ListGroup(ddown_list)

                                return ddown_group, sup_dct

                            else:
                                print('Logged in but search results = None')
                                return html.Div([],hidden=True), ''

                        except:
                            print('Logged in but an error occured during search so input data = 0')
                            return html.Div([],hidden=True), ''
                else:
                    print('Logged in but input data = 0 #1')
                    return html.Div([],hidden=True), ''

            except:
                print('Logged in but input data = 0 #2')
                return html.Div([],hidden=True), ''
    except:
        print('You are not logged in yet. Try logging in.')
        return html.Div([],hidden=True), ''

##########################################################################################
# Update dcc.Store - fav_table_data

@app.callback(Output("favTable", "derived_virtual_row_ids"),
             [Input("button-item-0","n_clicks")],
            #   Input("button-item-1","n_clicks"),
            #   Input("button-item-2","n_clicks")],
             [State("srch_dict","data"),
              State("favTable", "derived_virtual_row_ids")]
)
def update_row_ids(n_clicks0,srch_dict, row_ids):#n_clicks1,n_clicks2, 

    print('-------- Entered: update_row_ids --------')
    # print(srch_dict)
    # try:
    #     if n_clicks0 > 0: new_id = srch_dict['0']['id']
    #     if n_clicks1 > 0: new_id = srch_dict['1']['id']
    #     if n_clicks2 > 0: new_id = srch_dict['2']['id']
    #     else: new_id = -1234

    #     if new_id != -1234:
    #         if new_id not in row_ids:

    #             row_ids.append(new_id)

    #         print('Returning Row IDs: ' +str(row_ids))
    #         return row_ids
    #     else:
    #         raise PreventUpdate

    # except:
    #     raise PreventUpdate

    if n_clicks0 > 0:

        new_id = srch_dict['0']['id']

        if new_id not in row_ids:

            row_ids.append(new_id)

        print('Returning Row IDs: ' +str(row_ids))
        return row_ids

    else:
        raise PreventUpdate


@app.callback(
    Output("fav_table_data","data"),
    [Input('interval-component', 'n_intervals'),
     Input("favTable","derived_virtual_row_ids")],
    [State("srch_dict","data"),
     State("fav_table_data","data")]
)
def update_store_fav_table_data(n_intervals, row_ids, srch_dict, fav_table_data):

    print('-------- Entered: update_store_fav_table_data --------')
    print('No of intervals: '+ str(n_intervals+1))
    print(row_ids)

    if (fav_table_data is None) or (len(fav_table_data)<1):
         
         fav_table_data = readFav().to_dict()
         
         return fav_table_data

    else:
        # Add new data to dict
        if srch_dict is not None: # First check: does srch_dict exists ?
            if (type(srch_dict) == dict) & (len(srch_dict)>0): # Second check: is it a dictionary with values ?
                new_isin = srch_dict['0']['isin']

                if new_isin not in fav_table_data['isin']:
                    for k in fav_table_data.keys():
                        fav_table_data[k][new_isin] = srch_dict['0'][k]
                        print(fav_table_data[k][new_isin])


        # That bit makes sure that row_ids is initialised even if the user doesn't make any searches
        if len(row_ids)==0:
            
            for existing_isin  in fav_table_data['id']:
                row_ids.append(fav_table_data['id'][existing_isin])

            if '' not in row_ids:
                row_ids.append('')

        # Now delete all fav_table_data keys whose ids are not inside the list row ids:
        print(fav_table_data)
        keys_to_delete = []
        for k_isin, v_id in fav_table_data['id'].items():
            print('ISIN to check: '+k_isin)
            print('ID to check: '+ v_id)
            print(type(row_ids))
            print(row_ids)
            print(type(v_id))
            if str(v_id) not in row_ids:
                print(v_id + ' not in row_ids, so you must delete it from fav_table_data')
                keys_to_delete.append(k_isin)
                
        
        print(keys_to_delete)
        for it in keys_to_delete:
            for k in fav_table_data:
               
                del fav_table_data[k][it]

        print('Returned store fav_table_data')
        print(fav_table_data)
        return fav_table_data


# @app.callback(
#     Output("fav_table_data", "data"), 
#     [Input("button-item-0", "n_clicks")],
#     [State("srch_dict", "data"),
#      State("fav_table_data","data")]
# )
# def count_clicks(n_clicks, srch_dict, fav_table_data):

#     ctx = dash.callback_context

#     if row_ids is not None:
#        print('Row ids:')
#        print(row_ids)

#     print("Right before entering count_clicks")

#     if (fav_table_data is None) or (len(fav_table_data)<1):
#         fav_table_data = readFav().to_dict()

    
#     if n_clicks > 0:

#         print("Entered count_clicks :" +str(n_clicks))

#         # Add new data to dict
#         new_isin = srch_dict['0']['isin']
        
#         print(type(fav_table_data))
#         print(fav_table_data)

#         if new_isin not in fav_table_data['isin']:
#             for k in fav_table_data.keys():
#                 fav_table_data[k][new_isin] = srch_dict['0'][k]
#                 print(fav_table_data[k][new_isin])
        
#         return fav_table_data


#     else:
#         raise  PreventUpdate

##########################################################################################
# Update table and write to json

@app.callback(
    [Output("favTable", "data"),
     Output("favTable", "columns")],
    [Input("fav_table_data","data")],
    [State("favTable", "derived_virtual_row_ids")],
)
def update_table_favTable(fav_table_data, row_ids):
   
    print('-------- Entered: update_table_favTable --------')
    print(type(fav_table_data))
    print(fav_table_data)

    if (fav_table_data is None) or (len(fav_table_data)<1):
        print('retrieving from json')
        fav_table_data = readFav().to_dict()
        print('retrieving from json end')

    if row_ids is not None:

        # list_to_check_against = []
        # for record in existing_table_data:
        #     list_to_check_against.append(record['id'])

        #if sorted(row_ids) == sorted(list(fav_table_data['id'].values())):
        x =readFav().to_dict()
        if x == fav_table_data:
            print('No need to save now')
        else:
            with open('assets/favlist.json', 'w') as f:
                print('saving to json')
                json.dump(fav_table_data, f)
                print('saving to json end')
        
    # Return all ex row with empty strings
    list_data = pd.DataFrame(fav_table_data).to_dict('records')
        
    print('Before: ')
    print(list_data)

    # Check for missing ids
    table_data = []
    if len(list_data)>1:

        for num in range(len(list_data)):

            if list_data[num]['id'] != '':
                table_data.append(list_data[num])

    elif len(list_data)==1:

        if list_data[0]['id'] == '':
            table_data = list_data

        else:
            table_data.append( {'id': '', 'name': '', 'isin': '', 'symbol': '', 'productType': '', 'currency':'', 'exchangeId': '', 'vwdId': '', 'totalExpenseRatio': ''} )
            table_data.append( list_data[0] )

    else:
        table_data = [{'id': '', 'name': '', 'isin': '', 'symbol': '', 'productType': '', 'currency':'','exchangeId': '', 'vwdId': '', 'totalExpenseRatio': ''} ]

    mapping = {'name':'Security',
               'productType':'Type',
               'isin':'ISIN',
               'symbol':'Ticker',
               'exchangeId':'Exchange ID',
               'currency':'FX'
          }

    table_columns=[{"name": mapping[i], "id": i} for i in table_data[0].keys() if i not in ['vwdId','totalExpenseRatio','id']]
    

    print('After')
    print(table_data)

    return table_data, table_columns
