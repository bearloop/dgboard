from datetime import datetime as _datetime
from datetime import date as _date
from datetime import timedelta as _timedelta
from numpy.core.fromnumeric import var
import pandas as _pd
import requests as _requests
import numpy as _np
import json as _json
import textwrap

_BASE_TRADER_URL = 'https://trader.degiro.nl'

################################################################################################################

################################################################################################################
def _get_session_id(user, psw):
    
    url = _BASE_TRADER_URL+'/login/secure/login'

    my_json = {'username': user,
                'password': psw}

    my_headers = {'Content-Type': 'application/json'}

    try:
        de_giro = _requests.post(url, headers = my_headers, json=my_json)
        secID = de_giro.headers['Set-Cookie'].split('JSESSIONID=')[1].split(';')[0]
        
        return secID
        
    except:
        
        print('Session id fetch failed')

################################################################################################################

################################################################################################################
def _get_config_data(user, psw):
    
    url_config = _BASE_TRADER_URL+'/login/secure/config'
    
    try:
        secID = _get_session_id(user, psw)
        
        if secID is not None:
            updConfig =  _requests.get(_BASE_TRADER_URL+'/login/secure/config', 
                                  headers = {'Cookie':'JSESSIONID='+secID+';'})
            
            if updConfig.status_code ==  200:
                config_data = _json.loads(updConfig.content.decode("utf-8"))
                
                return config_data, secID
            else:
                print('Config data fetch failed')
    
    except: ''

################################################################################################################

################################################################################################################
def _get_client_info(user, psw):
    
    try:
        config_data, secID = _get_config_data(user, psw)
        
        pa_url = config_data['data']['paUrl']
        
        url_client = pa_url+'client?sessionId='+secID
        
        product_search_url = config_data['data']['productSearchUrl']
        
        try:
            client_info = _requests.get(url_client)

            client_data =  _json.loads(client_info.content.decode("utf-8"))
            
            if client_info.status_code == 200:

                account = str(client_data['data']['intAccount'])
                userToken = str(client_data['data']['id'])
                
                return product_search_url, account, userToken, config_data, secID
            
            else:
                print('Client data fetch failed')
        
        except: print('Config data or session id fetch failed')

    except: ''

################################################################################################################

################################################################################################################
def dg_get_data(user, psw):
    
    product_search_url, account, userToken, config_data, secID = _get_client_info(user, psw)
    
    data_dct = {'product_search_url': product_search_url,
                'account_id': account,
                'user_token': userToken,
                'config_data': config_data,
                'session_id': secID}
    
    return data_dct

################################################################################################################

################################################################################################################
def dg_get_product(searchTerm, data_dct, search_limit=10, product_type='All'):
    
    try:
        product_search_url = data_dct['product_search_url']
        account = data_dct['account_id']
        secID = data_dct['session_id']

        if product_type == 'All':
            search_url = product_search_url+'v5/products/lookup?intAccount='+account+\
                        '&sessionId='+secID+'&limit='+str(search_limit)+'&searchText='+searchTerm

        else:
            product_mapping = {'ETFs':'131','Stocks':'1'}
        
            search_url = product_search_url+'v5/products/lookup?intAccount='+account+\
                        '&sessionId='+secID+'&productTypeId='+\
                        product_mapping[product_type]+'&limit='+str(search_limit)+'&searchText='+searchTerm

        
        search_results = _requests.get(search_url)
        return _json.loads(search_results.content)
        
    except: print('Product search failed')
        
################################################################################################################

################################################################################################################

def dg_get_transactions(data_dct):
    
    TRANSACTIONS_URL = 'https://trader.degiro.nl/reporting/secure/v4/transactions/'
    
    to_date = _datetime.today().strftime('%d/%m/%Y')

    payload = {
                'fromDate':'01/01/2000',# arbitrary date
                'toDate': to_date, # to today
                'group_transactions_by_order': False,
                'intAccount': data_dct['account_id'],
                'sessionId': data_dct['session_id']}

    try:
        ##########################################################################################
        positions = _requests.get(TRANSACTIONS_URL, params = payload)
        
        pos_data = _pd.DataFrame(_json.loads(positions.content)['data'])

        pos_data['date'] = pos_data['date'].str.split("T", expand = True)[0]
        
        ##########################################################################################
        # Positions: Units
        positions = pos_data[['date','productId','quantity']].groupby(['date','productId']).sum()['quantity'].unstack()
        positions['unitsTotal'] = positions.sum(axis=1) # total units doesn't make any intuitive sense but let's provide it nevertheless
        positions.index = _pd.to_datetime(positions.index)
        
        ##########################################################################################
        # Positions: Nominal cost
        dollar_cost = pos_data[['date','productId','totalInBaseCurrency']].groupby(['date','productId']).sum()['totalInBaseCurrency'].unstack()    
        dollar_cost['costTotal'] = dollar_cost.sum(axis=1)
        dollar_cost.index = _pd.to_datetime(dollar_cost.index)
        
        ##########################################################################################
        # Fees paid
        fees = pos_data[['date','productId','feeInBaseCurrency']].groupby(['date','productId']).sum()['feeInBaseCurrency'].unstack()
        fees['feesTotal'] = fees.sum(axis=1)
        fees.index = _pd.to_datetime(fees.index)
        
        ##########################################################################################
        # Change to string
        positions.columns = positions.columns.astype(str)
        dollar_cost.columns = dollar_cost.columns.astype(str)
        fees.columns = fees.columns.astype(str)
        
        ##########################################################################################
        # Return vwd IDs that correspond to Degiro ID
        r = dg_post_product_info(data_dct, list(fees.columns[:-1]))
        
        ##########################################################################################
        # Return dictionary {productId:vwdId} and {productId:symbol}
        # let me tell you what the heck the below does: it supposedly keeps two dictionaries 
        # vwdMap and symbolsDict. Both have as their keys DeGiro asset ids. The first dict's values
        # are the respective vwd asset ids while the second's are the asset symbols.
        # Now there are cases where you might not be able to retrieve neither so you have to control
        # for that.

        vwdMap = {}
        symbolsDict = {}
        int_null = 0

        for index_dict, key in enumerate(r):

            try:
                symSup = r[key]['symbol'] # pass the asset symbol
            except:
                try:
                    symSup = r[key]['isin'] # pass the isin if there's no symbol available
                except:
                    symSup = 'Undefined '+index_dict

            try:
                sup = r[key]['vwdId']
                if sup.isnumeric():
                    value = sup
                else:
                    value = r[key]['vwdIdSecondary']
                
            except:
                value = '--'+str(int_null)
                int_null += 1

            vwdMap[key] = value
            if symSup in symbolsDict.values():
                symbolsDict[key] = symSup+'_'+index_dict
            else:
                symbolsDict[key] = symSup

        # What you should be returning is a dictionary with vwdId as keys and symbols as values
        if vwdMap.keys() == symbolsDict.keys():
            dct_vwdIDs_names = {}
            for k in vwdMap:
                dct_vwdIDs_names[vwdMap[k]] = symbolsDict[k]
        else:
            print('Symbols do not match DG IDs')
            dct_vwdIDs_names = vwdMap

        ##########################################################################################
        # Create a new index
        new_positions_index = _pd.date_range(start=positions.index[0],end=positions.index[-1])
        new_dollar_cost_index = _pd.date_range(start=dollar_cost.index[0],end=dollar_cost.index[-1])
        new_fees_index = _pd.date_range(start=fees.index[0],end=fees.index[-1])

        # Check if the diminshed expanded = old index then replace 
        if positions.reindex(new_positions_index).loc[positions.index].fillna(0).equals(positions.fillna(0)):
            positions = positions.reindex(new_positions_index)
            
        if dollar_cost.reindex(new_dollar_cost_index).loc[dollar_cost.index].fillna(0).equals(dollar_cost.fillna(0)):
            dollar_cost = dollar_cost.reindex(new_dollar_cost_index)
        
        if fees.reindex(new_fees_index).loc[fees.index].fillna(0).equals(fees.fillna(0)):
            fees = fees.reindex(new_fees_index)
            
        return positions, dollar_cost, fees, vwdMap, dct_vwdIDs_names
    
    except Exception as e:
        print(e)
        #raise(e)

################################################################################################################

################################################################################################################
def dg_post_product_info(data_dct, productIDs_list):
    
    #print(productIDs_list)
    
    header = {'content-type': 'application/json'}
    params = {   
              'intAccount': data_dct['account_id'],
              'sessionId': data_dct['session_id']
             }
    data_obj = _json.dumps([str(i) for i in productIDs_list])
    
    try:
        r = _requests.post(url=data_dct['product_search_url']+'v5/products/info',
                           headers=header, params=params,
                           data=data_obj)

        r = _json.loads(r.content.decode('utf-8'))['data']
    
        return r
    
    except Exception as e:
        print(e)
        #raise(e)
        
################################################################################################################

################################################################################################################

def dg_vwd_retrieve(data_dct, list_vwdIDs, per_auto='YTD', per_start=None, per_end=None, series='price'):
    '''
    list_vwdIDs: a list of vwd securities
    per_auto: 'ALL' | 'YTD' | 'P1D' | 'P1W' | 'P1M' | 'P3M' | 'P6M' | 'P1Y' | 'P3Y' | 'P5Y' | 'P50Y'
    per_start: e.g. '2019-01-01'
    per_end: e.g. '2020-12-31'
    series: 'price' | 'volume'
    '''

    str_token = data_dct['user_token']

    if per_start is not None:
        if per_end is not None:
            date_periods = 'start='+per_start+'&end='+per_end
        else:
            per_end = _date.today().strftime('%Y-%m-%d')
            date_periods = 'start='+per_start+'&end='+per_end
    
    elif per_end is not None:
        if per_start is None:
            # Default to a year ago from end date
            per_start = (_datetime.strptime(per_end, '%Y-%m-%d') - _timedelta(days=1*365)).strftime('%Y-%m-%d')
            date_periods = 'start='+per_start+'&end='+per_end
    else:
        date_periods = 'period='+per_auto
    
    # output dataframe: initialise
    output = _pd.DataFrame()
    
    dct_vwdIDs_names = {}
    
    for security_id in list_vwdIDs:
        str_vwid = security_id
        url = 'https://charting.vwdservices.com/hchart/v1/deGiro/data.js?'+\
            'resolution=P1D&culture=en-US&'+date_periods+'&series=issueid%3A'+str_vwid+\
            '&series='+series+'%3Aissueid%3A'+str_vwid+'&format=json&userToken='+str_token
        if '--' in str_vwid:
            data_df = _pd.DataFrame(columns=[str_vwid])
            output = _pd.concat([output, data_df], axis=1)
            dct_vwdIDs_names[security_id] = 'NOT_AVAILABLE'        
        
        else:
            try:
                # request data
                res = _requests.get(url) # print(res.url)
                ts_results = _json.loads(res.content)['series']

                # name
                name = ts_results[0]['data']['name']
                dct_vwdIDs_names[security_id] = name
                
                # start, end index
                start_ind = ts_results[1]['data'][0][0]
                end_ind = ts_results[1]['data'][-1][0]

                # start, end dates
                start_date = _datetime.strptime(ts_results[0]['data']['windowFirst'][:10],'%Y-%m-%d')
                end_date = _datetime.strptime(ts_results[0]['data']['windowLast'][:10],'%Y-%m-%d')
                dates = _pd.date_range(start_date, end_date, freq='1D')

                # price and dates vessels
                price_df = _pd.DataFrame(ts_results[1]['data'], columns = ['Index_Num',name]).set_index('Index_Num')
                dates_df = _pd.DataFrame(index = [i for i in range(start_ind, end_ind+1)], data = dates, columns=['Dates'])
                data_df = _pd.concat([price_df, dates_df], axis=1).set_index('Dates')
                output = _pd.concat([output, data_df], axis=1)
                
            except Exception as e:
                data_df = _pd.DataFrame(columns=[str_vwid])
                output = _pd.concat([output, data_df], axis=1)
                print(e)
                ''
    
    # Drop all rows where all values are null
    output = output[(output.T.notnull()).any()]
    
    # Replace ffill missing data
    output = output.fillna(method='ffill')
    
    return output, dct_vwdIDs_names

################################################################################################################

################################################################################################################

def dg_get_portfolio(data_dct, dates_auto='YTD', dates_start=None, dates_end=None):
    '''
    per_auto: 'ALL' | 'YTD' | 'P1D' | 'P1W' | 'P1M' | 'P3M' | 'P6M' | 'P1Y' | 'P3Y' | 'P5Y' | 'P50Y'
    per_start: e.g. '2019-01-01'
    per_end: e.g. '2020-12-31'
    '''
    # Get data time series
    units, cost, fees, vwdMap, symbolMap = dg_get_transactions(data_dct)
    
    prices_time_series, assets_map = dg_vwd_retrieve(data_dct,
                                                     list_vwdIDs=list(vwdMap.values()),
                                                     per_auto=dates_auto,
                                                     per_start=dates_start, per_end=dates_end,
                                                     series='price')

    # Map time series to vwd IDs
    assets_map_reversed = {}
    for k in assets_map.keys():
        assets_map_reversed[assets_map[k]] = k

    prices_time_series = prices_time_series.rename(columns=assets_map_reversed)


    # Drop column Total and map to vwd IDs
    units = units.rename(columns=vwdMap).drop('unitsTotal',axis=1)[prices_time_series.columns].fillna(0).cumsum()
    units = units.reindex(index=prices_time_series.index).fillna(method='ffill').fillna(0)

    cost = cost.rename(columns=vwdMap).drop('costTotal',axis=1)[prices_time_series.columns].fillna(0).cumsum()
    fees = fees.rename(columns=vwdMap).drop('feesTotal',axis=1)[prices_time_series.columns].fillna(0).cumsum()

    # Cost basis
    cost = -cost.reindex(index=prices_time_series.index).fillna(method='ffill').fillna(0)
    cost['costTotal'] = cost.sum(axis=1)

    # Fees paid
    fees = -fees.reindex(index=prices_time_series.index).fillna(method='ffill').fillna(0)
    fees['feesTotal'] = fees.sum(axis=1)

    # Portfolio and assets value
    p_value = (prices_time_series*units)
    p_value['valueTotal'] = p_value.sum(axis=1)

    # Index returns - netflows - adjusted value
    p_value['netFlows'] = cost['costTotal'].diff()
    p_value['valueAdjusted']  = p_value['valueTotal'] - p_value['netFlows']
    p_value['indexRet'] = (p_value['valueTotal'] - p_value['valueTotal'].shift(1) - p_value['netFlows']
                               ) / (p_value['valueTotal'].shift(1) + p_value['netFlows'])
    p_value['indexRet'][p_value['valueTotal']==0] = _np.NaN
    p_value['Index'] = p_value['indexRet'].fillna(0).add(1).cumprod().fillna(1)
    
    # p_value, results = dg_calculate_port_stats(p_value)

    # Weights
    weights = p_value.div(p_value['valueTotal'],axis='rows').fillna(0)#.dropna()

    # Current assets prices
    current_hold = list(units[units>0].iloc[-1,:].dropna().index)
    current_hold_prices = prices_time_series[current_hold].rename(columns=symbolMap)

    # Upper case -> tries to break long strings to sets of 10
    # for i in assets_map:
    #      #assets_map[i] = assets_map[i].upper()
    #      assets_map[i] = '<br>'.join(textwrap.wrap(assets_map[i].upper(), width=10))
    
    return p_value, weights, units, cost, fees, symbolMap, current_hold_prices#, assets_map, assets_map_reversed, vwdMap

################################################################################################################

################################################################################################################

def dg_mod_dietz_ret(p_value):
    
    # Modified dietz return calculation
    p_value = p_value.iloc[0:,:]
    p_value['Days'] = p_value.index.to_series().diff().astype('timedelta64[D]').fillna(0).cumsum()
    p_value['Weight'] = (p_value['Days'][-1] - p_value['Days'])/p_value['Days'][-1]

    last_value = p_value['valueTotal'][-1]
    start_value = p_value['valueTotal'][0]
    invested_cap = p_value['netFlows'].sum()
    weighted_flows = p_value['netFlows'].mul(p_value['Weight']).sum()

    mod_dietz_ret = (last_value - start_value - invested_cap) / (start_value + weighted_flows)
    
    results = _pd.DataFrame(columns=['Portfolio'],index=['Invested Capital','Weighted Flows','Last Value','Mod Dietz Ret'])
    results.loc['Start Value'] = 'EUR ' + start_value.round(0).astype(int).astype(str)
    results.loc['Invested Capital'] = 'EUR ' + invested_cap.round(0).astype(int).astype(str)
    results.loc['Weighted Flows'] = 'EUR ' + weighted_flows.round(0).astype(int).astype(str)
    results.loc['Last Value'] = 'EUR ' + last_value.round(0).astype(int).astype(str)
    results.loc['Mod Dietz Ret'] = (mod_dietz_ret*100).round(2).astype(str) + '%'
    
    return results

################################################################################################################

################################################################################################################

def portfolio_metrics_tables(ts_df, capital_df, trading_days):
    '''
    ts_df: Pandas.Dataframe with dates as its index and total return or price value as data
    '''
    ts_df = _pd.DataFrame(ts_df)
    ts_df.columns = ['Portfolio']
    
    ###############################################################################################################
    # Calculate stats
    mean_ret = ts_df.pct_change().dropna().mean()[0]
    best_ret = ts_df.pct_change().dropna().max()[0]
    worst_ret = ts_df.pct_change().dropna().min()[0]

    std_ret  = ts_df.pct_change().dropna().std()[0]
    skew_ret = ts_df.pct_change().dropna().skew()[0]
    kurt_ret = ts_df.pct_change().dropna().kurt()[0]

    ddown    = drawdown_val(ts_df)
    max_dd   = min(ddown)
    last_dd  = ddown[-1]
    
    days_yr  = 12*trading_days
    days_3mo = 3*trading_days
    days_mo  = 1*trading_days

    varisk = -ts_df.pct_change().dropna().rolling(window=days_3mo,
                                                  min_periods=5).quantile(1-0.05)*_np.sqrt(days_mo)
    varisk = varisk.iloc[-1][0]
    ###############################################################################################################
    # Overview table
    overview_df =  _pd.DataFrame(columns=['Overview'], index = ['Period Start'])
    
    overview_df.loc['Period Start']     = ts_df.dropna().index[0].strftime('%Y-%m-%d')
    overview_df.loc['Period End']       = ts_df.dropna().index[-1].strftime('%Y-%m-%d')
    overview_df.loc['Period Length']    = str( ts_df.dropna().count().values[0] ) + ' days'
    overview_df.loc['Start Value']      = capital_df.loc['Start Value'][0]
    overview_df.loc['Invested Capital'] = capital_df.loc['Invested Capital'][0]
    overview_df.loc['Weighted Flows']   = capital_df.loc['Weighted Flows'][0]
    overview_df.loc['Last Value']       = capital_df.loc['Last Value'][0]
    overview_df.loc['Ret/Vol Ratio']    = str( round ( (mean_ret*days_yr) / (std_ret*_np.sqrt(days_yr)), 3 ) )
    
    ###############################################################################################################
    # Risk table
    risk_df =  _pd.DataFrame(columns=['Risk Metrics'], index = ['Stand Dev (Ann)'])
    
    risk_df.loc['Stand Dev (Ann)']      = str( round ( std_ret * _np.sqrt(days_yr) * 100, 2 ) ) + '%'
    risk_df.loc['Stand Dev']            = str( round ( std_ret                     * 100, 2 ) ) + '%'
    risk_df.loc['Skewness']             = str( round ( skew_ret                         , 2 ) )
    risk_df.loc['Kurtosis']             = str( round ( kurt_ret                         , 2 ) )
    risk_df.loc['VaR 1-month']          = str( round ( varisk                      * 100, 2 ) ) + '%'
    risk_df.loc['Max Drawdown']         = str( round ( max_dd                      * 100, 2 ) ) + '%'
    risk_df.loc['Last Drawdown']        = str( round ( last_dd                     * 100, 2 ) ) + '%'
    
    ###############################################################################################################
    # Performance table
    perf_metrics_ind = ['1-week Ret', '1-month Ret', '3-month Ret', 'Mean Ret',
                    'Best Ret', 'Worst Ret', 'Mean Ret (Ann)',  'Total Ret', 'CAGR', 'Mod Dietz Ret']
    perf_df =  _pd.DataFrame(columns=['Performance'], index = perf_metrics_ind)
    
    # 1-w return
    try:
        find_ret = ts_df.pct_change(5).iloc[-1][0]
        if _np.isnan(find_ret): oneW_ret = 'N/A'
        else: oneW_ret = str( round ( find_ret * 100, 2 ) ) + '%'

    except:
        oneW_ret = 'N/A'

    # 1-m return  
    try: 
        find_ret = ts_df.pct_change(days_mo).iloc[-1][0] 
        if _np.isnan(find_ret): oneM_ret = 'N/A'
        else: oneM_ret = str( round ( find_ret * 100, 2 ) ) + '%'

    except:
        oneM_ret = 'N/A'

    # 3-m return
    try:
        find_ret = ts_df.pct_change(days_3mo).iloc[-1][0] 
        if _np.isnan(find_ret): threeM_ret = 'N/A'
        else: threeM_ret = str( round ( find_ret * 100, 2 ) ) + '%'

    except:
        threeM_ret = 'N/A'

    # Total return - CAGR
    try:
        firstP = ts_df.dropna().iloc[0][0]
        lastP = ts_df.dropna().iloc[-1][0]
        find_ret = (lastP / firstP) - 1

        if _np.isnan(find_ret):
            tot_ret  = 'N/A'
            cagr_ret = 'N/A'
        else:
            tot_ret  = str( round ( find_ret * 100, 2 ) ) + '%'
            years = (ts_df.dropna().index[-1] - ts_df.dropna().index[0]).days/365
            cagr_ret = str( round ( ( (lastP/firstP)**(1/years)-1) * 100, 2 ) ) + '%'
    except:
        tot_ret  = 'N/A'
        cagr_ret = 'N/A'

    
    perf_df.loc['1-week Ret']           = oneW_ret
    perf_df.loc['1-month Ret']          = oneM_ret
    perf_df.loc['3-month Ret']          = threeM_ret
    perf_df.loc['Mean Ret']             = str( round ( mean_ret                  * 100, 2 ) ) + '%'
    perf_df.loc['Best Ret']             = str( round ( best_ret                  * 100, 2 ) ) + '%'
    perf_df.loc['Worst Ret']            = str( round ( worst_ret                 * 100, 2 ) ) + '%'
    perf_df.loc['Mean Ret (Ann)']       = str( round ( mean_ret * days_yr        * 100, 2 ) ) + '%'
    perf_df.loc['Total Ret']            = tot_ret
    perf_df.loc['CAGR']                 = cagr_ret
    perf_df.loc['Mod Dietz Ret']        = capital_df.loc['Mod Dietz Ret'][0]

    # desc.loc['Q1:25%'][asset] = str(round(ret[asset].dropna().quantile(q=0.25),numFloat))+'%'
    # desc.loc['Q2:50%'][asset] = str(round(ret[asset].dropna().quantile(q=0.50),numFloat))+'%'
    # desc.loc['Q3:75%'][asset] = str(round(ret[asset].dropna().quantile(q=0.75),numFloat))+'%'
    
    return overview_df, risk_df, perf_df

################################################################################################################

################################################################################################################

def drawdown_val(ts_data):

    maxPrice = 0
    ddown = []
    for price in ts_data.iloc[:,0].dropna():
        if price > maxPrice:
            maxPrice = price
        ddown.append((price - maxPrice) / maxPrice)
        
    return ddown

################################################################################################################

################################################################################################################

def calc_basics(df, last_n_periods=None, how='cumret', drop_nulls=False, ann_period=252, lookback=21):
    '''
    how: cumret returns a rebased price chart
         vol returns an annualised vol chart
    drop_nulls: drops all nan values
    last_n_periods: df starting period
    ann_period: annualisation period e.g. 252 days / 1 year
    lookback: number of lookback days/periods e.g. 21 days / 1 month
    '''
    # Select starting point
    if last_n_periods is not None:
        df = df.iloc[-(last_n_periods+1):,:].copy()
    
    # Drop all null
    if drop_nulls:
        df = df.dropna()
    
    # Choose output method
    if how == 'cumret':
        res = df.pct_change().add(1).cumprod()
    
    elif how == 'vol':
        res = df.pct_change().rolling(lookback).std()*(ann_period**(1/2))
        res = res.dropna(how='all')

    return res

################################################################################################################

################################################################################################################

def calc_ddown(df, drop_nulls=False):
    '''
    drop_nulls: drops all nan values
    '''
    # Drop all null
    if drop_nulls:
        df = df.dropna()

    maxPrices = df.cummax()
    ddown = (df/maxPrices)
    
    return ddown

################################################################################################################

################################################################################################################

def calc_value_at_risk(df, drop_nulls=False, lookback=21, forward=21, conf=0.05):
    '''
    drop_nulls: drops all nan values
    lookback: number of days/periods to use as input in VaR e.g. 21 days / 1 month
    forward: number of days/periods that VaR refers to e.g. 21 days / 1 month
    conf: VaR confidence level e.g. 5%, 2.5%
    '''
    
    # Drop all null
    if drop_nulls:
        df = df.dropna()

    var = df.pct_change().rolling(window=lookback, min_periods=lookback).quantile(1-conf)*_np.sqrt(forward)
    
    # This is to remove any rows where all values are nan
    var = var.dropna(how='all')

    return var

################################################################################################################

################################################################################################################

def calc_correl(df, how='cmx', drop_nulls=False, lookback=21, min_periods=21):
    '''
    how: cmx returns a correlation matrix
         corr returns the mean pairwise correlation
    drop_nulls: drops all nan values
    lookback: number of lookback days/periods to calculate correlation e.g. 21 days / 1 month
    min_periods: number of days/periods required 
    '''
    min_periods = min([min_periods,lookback])
    
    # Drop all null
    if drop_nulls:
        df = df.dropna()
    
    # Choose output method
    if how == 'cmx':
        df = df.iloc[-(lookback+1):,:].copy()
        res = df.pct_change().corr()
        
    elif how == 'corr':

        correlData = _pd.DataFrame()
        asset_names = df.columns
        
        for i in asset_names:
            for j in asset_names:
                if i!=j:
                    names = sorted([i,j])
                    pair = names[0]+'_'+names[1]
                    if pair not in correlData.columns:
                        correlData[pair] = df[i].dropna().rolling(window=lookback,
                                                                  min_periods=lookback).corr(df[j].dropna())

        res = correlData.mean(axis=1).dropna()
        res = _pd.DataFrame(res)
        if len(res.columns) == 1: res.columns = ['Pairwise Corr']
    
    return res