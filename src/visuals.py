from datetime import date as _date
from enum import auto
from numpy.lib.shape_base import tile
import pandas as _pd
import plotly.express as _px
#import plotly.graph_objects as go
#from plotly.subplots import make_subplots

color_neutral = ['#ECF0F1']
color_main = ['#2C3E50']
color_10 = ['#233140'] + color_main  + ['#415161','#566472', '#6b7784', '#808b96', 
                                        '#959ea7', '#aab1b9', '#bfc5ca', '#d4d8dc']


#########################################################################################################

#########################################################################################################

def graph_index(chart_type='bar', data_df=None, chart_title=None):
    
    if data_df is None:
        data_df = _pd.DataFrame()
        data_df.loc[_date.today().strftime("%d-%m-%Y"), "data"] = 0

    else:
        data_df = _pd.DataFrame(data_df)

    if chart_type == 'bar':
        fig = _px.bar(
            data_df,
            template = 'seaborn',
            color_discrete_sequence = color_main
        )
        ht_text = "Date: %{x|%Y-%m-%d}<br>Return: %{y:.2%}"
        

    elif chart_type == 'line':
        fig = _px.line(
            data_df,
            template = 'seaborn',
            color_discrete_sequence = color_main
        )
        ht_text = "Date: %{x|%Y-%m-%d}<br>Index Value: %{y:.1%}"
    
    fig = fig.update_layout(
            font = dict(color="#505050", size=10, family='sans-serif'),
            xaxis = {"gridcolor": "#E1E5ED"},
            yaxis = {"gridcolor": "#E1E5ED"},
            plot_bgcolor='#ecf0f1',
            showlegend = False,
            autosize=False,
            width = 490,
            height = 240,
            margin = {'l':0, 't':25, 'r':0, 'b':0, 'pad':0},
            title={'text':chart_title,
                   'xref':'paper', 'x':1, 'xanchor': 'right',
                   'font':{'size':15, 'family':'sans-serif'}
                   }
        ).update_yaxes(tickformat = "%.0f%%", title_text = ''
        ).update_xaxes(title_text = '', rangebreaks=[dict(bounds=["sat", "mon"])], tickformat="%b %y"
        ).update_traces(hovertemplate=ht_text)

        # update_xaxes( tickmode='array', title_text = '', tickformat="%b %y", dtick='M1', tick0=data_df.index[0],  
        #                 )]
        # ).
    if chart_type=='bar':
        fig = fig.update_layout(barmode='group',
                                bargap=0, # gap between bars of adjacent location coordinates.
                                bargroupgap=0.25 # gap between bars of the same location coordinate.
                                )

    return fig

#########################################################################################################

#########################################################################################################

def graph_weights(chart_type='area', data_df=None, chart_title=None):
    
    if data_df is None:
        if chart_type=='area':
            data_df = _pd.DataFrame()
            data_df.loc[_date.today().strftime("%d-%m-%Y"), "data"] = 0

        elif chart_type=='pie':
            data_df = _pd.DataFrame(columns=[_date.today().strftime("%d-%m-%Y")],index=['Placeholder'],data=1)

    else:
        data_df = _pd.DataFrame(data_df)

    if chart_type == 'area':
        fig = _px.area(
            data_df,
            template = 'seaborn',
            color_discrete_sequence=color_10
        )
    
        fig = fig.update_layout(
                font = dict(color="#505050", size=10, family='sans-serif'),
                xaxis = {"gridcolor": "#E1E5ED"},
                yaxis = {"gridcolor": "#E1E5ED"},
                plot_bgcolor='#ecf0f1',
                showlegend = False,
                autosize=False,
                width = 450,
                height = 210,
                margin = {'l':0, 't':25, 'r':0, 'b':0, 'pad':0},
                title={'text':chart_title,
                       'xref':'paper', 'x':1, 'xanchor': 'right',
                       'font':{'size':14, 'family':'sans-serif'}
                       },
                legend_title={'text':''}
            ).update_xaxes( tickmode='array', title_text = '', tickformat="%b %d", tick0=data_df.index[0],  
                            rangebreaks=[dict(bounds=["sat", "mon"])]
            ).update_yaxes( tickformat = "%.0f%%", title_text = '', tickvals=[0.2,0.4,0.6,0.8,1], rangemode='nonnegative'
            ).update_traces(hovertemplate="Date: %{x|%Y-%m-%d}<br>Weight: %{y:0%}")
        
    elif chart_type == 'pie':
        if 'Placeholder' == data_df.index[0]: color_coding = color_neutral
        else: color_coding = color_10

        fig = _px.pie(data_df,
                values=data_df.columns[0],
                names=data_df.index,
                template='seaborn',
                color_discrete_sequence=color_coding,
                hole=0.3,
                ).update_traces(
                    pull=0.03,
                    domain={'x':[0,0.7],'y':[0.2,1]},
                    texttemplate="%{percent:0%}",
                    hovertemplate="Asset: %{label}<br>Weight: %{percent:0%}"
                ).update_layout(
                    font = dict(color="#505050", size=10, family='sans-serif'),
                    xaxis = {"gridcolor": "#E1E5ED"},
                    yaxis = {"gridcolor": "#E1E5ED"},
                    plot_bgcolor='#ecf0f1',
                    showlegend = True,
                    autosize=False,
                    width = 325,
                    height = 210,
                    margin = {'l':0, 't':25, 'r':5, 'b':0, 'pad':0},
                    title={'text':chart_title,
                           'xref':'container', 'x':1, 'xanchor': 'right',
                           'font':{'size':14, 'family':'sans-serif'}
                           },
                    legend_title={'text':'Date: '+str(data_df.columns[0])},
                    legend={'yanchor':'top', 'xanchor':'right', 'x':1.01,'y':1,'font':{'size':9}},
                    #legend_itemsizing='constant',
                    legend_bgcolor=color_neutral[0]
                )

    return fig

#########################################################################################################

#########################################################################################################

def graph_small_index(data_df=None, chart_title=None, width=800,show_legend=True):
    
    if data_df is None:
        data_df = _pd.DataFrame()
        data_df.loc[_date.today().strftime("%d-%m-%Y"), "data"] = 0

    else:
        data_df = _pd.DataFrame(data_df)

    ht_text = "Date: %{x|%Y-%m-%d}<br>Index Value: %{y:.1%}"

    fig = _px.line(
            data_df,
            template = 'seaborn',
            color_discrete_sequence = ['#2C3E50']+_px.colors.qualitative.G10,
            render_mode="svg"
        )
    
    fig = fig.update_layout(
            font = dict(color="#505050", size=10, family='sans-serif'),
            xaxis = {"gridcolor": "#E1E5ED"},
            yaxis = {"gridcolor": "#E1E5ED"},
            plot_bgcolor='#ecf0f1',
            showlegend = show_legend,
            legend_title={'text':''},
            autosize=False,
            legend_bgcolor=color_neutral[0],
            width = width,
            height = 220,
            margin = {'l':0, 't':25, 'r':0, 'b':0, 'pad':0},
            title={'text':chart_title,
                   'xref':'paper', 'x':1, 'xanchor': 'right',
                   'font':{'size':15, 'family':'sans-serif'}
                   }
        ).update_yaxes(tickformat = "%.0f%%", title_text = ''
        ).update_xaxes(title_text = '', #rangebreaks=[dict(bounds=["sat", "mon"])], tickformat="%b %y"
        ).update_traces(hovertemplate=ht_text,line=dict(width=0.9))

    return fig
