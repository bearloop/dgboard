from app import dbc
import pandas as pd
import json

print('got in utils')
# Menu
navmenu = dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Pages:", header=True),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem("Admin", href="/"),
                dbc.DropdownMenuItem(divider=True),
                dbc.DropdownMenuItem("Overview", href="/page-2"),
                dbc.DropdownMenuItem("Risk Analysis", href="/page-3"),
                dbc.DropdownMenuItem("Market Watch", href="/page-4"),
                dbc.DropdownMenuItem("Transactions", href="/page-5")
                
            ],
            nav=True,
            label="Menu",
            right=True
        )

# Navbar
navbar = dbc.NavbarSimple(
    children=[navmenu],
    brand="Portfolio Reporting",
    brand_style={"font-size": "26px"},
    color="primary",
    dark=True,
    className="m-4")

# Read from JSON

def readFav():
    ''' Returns the JSON file data as a DataFrame'''

    try:
        #print('Tying to read from file')
        with open('assets/favlist.json','r') as f:
            data = json.load(f)
            print(data)
            print(type(data))
        f.close()


        df = pd.DataFrame(dict(data))

        if df.empty or (df.notnull().any(axis=1).sum()==0):
            dat = {'id': {'':''}, 'name': {'':''},'isin': {'':''},'symbol': {'':''}, 'productType': {'':''}, 'currency': {'':''}, 'exchangeId': {'':''}, 'vwdId': {'':''},'totalExpenseRatio': {'':''}}
            df = pd.DataFrame(dat)
        
        print('Returning dataframe')
        return df
    
    except:
        data = {'id': {'':''}, 'name': {'':''},'isin': {'':''},'symbol': {'':''}, 'productType': {'':''}, 'currency': {'':''}, 'exchangeId': {'':''}, 'vwdId': {'':''},'totalExpenseRatio': {'':''}}
        df = pd.DataFrame(data)

        print('Returning dataframe without any data')
        return df


# Constants: table formatting
format_table={'overflowX': 'scroll',
              'overflowY': 'scroll',
              'overflow': 'auto',
              'minWidth': '100%',
              'maxHeight':'600px'
              }

format_data_conditional=[
        {
        'if': {'row_index': 'odd'},
        'backgroundColor': '#ffffff'
        }
    ]

format_header={
        'backgroundColor': '#ffffff',
        'fontWeight': 'bold',
        'font_family': 'sans-serif',
        'font_size': '9pt',
        'text_align': 'left',
        'border': '0.0px solid #e8e8e8',
        #'border-bottom': '1px solid #e8e8e8'
    }

format_cell = {
        'font_family': 'sans-serif',
        'backgroundColor': '#ecf0f1',
        'font_size': '9pt',
        'text_align': 'left',
        'border': '0.0px solid #e8e8e8',
        #'border-bottom': '0.5px dashed #e8e8e8'
    }


# Constants: markets table formatting

format_markets_table={
                     'overflowY': 'scroll',
                     #'overflowX': 'scroll',
                     #'overflow': 'auto',
                     'width':'100%',
                     'minWidth': '790px',
                     'maxHeight':'800px',
                     'margin_left':'15px'
                    }