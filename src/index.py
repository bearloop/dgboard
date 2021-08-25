import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from app import app
from apps import app1, app2, app3, app4, app5

app.layout = html.Div([ dcc.Location(id='url', refresh=False), 
                        html.Div(id='page-content'),
                        dcc.Store(id="fetched_data", storage_type="session", data={}),
                        dcc.Store(id="log_button_data", storage_type="session", data="Login"),
                        dcc.Store(id="fav_table_data", storage_type="session", data={})
                    ])


@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):

    if pathname == "" or pathname == "/" or pathname == "/page-1":
         print('going in')
         return app1.layout1

    elif pathname == "/page-2":
         return app2.layout2

    elif pathname == "/page-3":
        return app3.layout3

    elif pathname == "/page-4":
        return app4.layout4

    elif pathname == "/page-5":
        return app5.layout5

    else:
        return app1.layout1

# dcc.Interval(id='interval-component', interval=5*1000, n_intervals=0)  
# @app.callback([Output('fetched_data', 'data'),
#                Output('interval-component','n_intervals')],
#                Input('interval-component', 'n_intervals'),
#                State('fetched_data','data'))
# def update_metrics(n, fdt):
    
#     # if n=5 minutes have elapsed since
#     if (n == 1000 * 60 * 5) or (fdt is None):
#         fdt = {}
#         return fdt, 0
#     else:
#         return fdt, n

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False, threaded=False, port=8072)