# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 11:11:28 2022

@author: Jack Vance
"""
####
# Stock Overview Dashboard
####

# Runs on plotly.dash

# input ticker (dropdown) and year(s)/TTM (multiselector - averaging) to view (IMO) most relevant info

# imports
import datetime
# dash components
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

# pandas, yfinance to grab stock data
#import pandas as pd
from pandas_datareader import data as pdr
import yfinance as yf

#plot templates to change style for all, including html
template_base = 'plotly_dark'
pio.templates['buffalo_stone'] = pio.templates[template_base]

pio.templates['buffalo_stone'].layout['paper_bgcolor'] = '#696969'
pio.templates['buffalo_stone'].layout['plot_bgcolor'] = '#696969'
pio.templates['buffalo_stone'].layout['xaxis']['gridcolor'] = '#696969'
pio.templates['buffalo_stone'].layout['yaxis']['gridcolor'] = '#696969'
pio.templates['buffalo_stone'].layout['yaxis']['zerolinecolor'] = '#ffffff'

template = 'buffalo_stone' 

pio.templates.default = template

#pio.templates['buffalo_stone'].layout
#pio.templates['buffalo_stone'].layout
#pio.templates['buffalo_stone'].layout

#pio.templates.default['paper_bgcolor'] = "#696969"

text_color = pio.templates[template].layout['font']['color']
bg_color = pio.templates[template].layout['paper_bgcolor']
#bg_color = "#696969"

#define functions for later use - simplifies calls later, might speed reruns slightly
def getData(ticker, year_range): #all data pulling functions
    # price chart from pdr
    year_range[0] = str(year_range[0])+'/1/1'
    
    if year_range[1] == datetime.date.today().year:
        year_range[1] = 'today'
    else:
        year_range[1] = str(year_range[1])+'/12/31'
    prices = pdr.DataReader(ticker,'yahoo', year_range[0], year_range[1])
    
    # everything else from yf
    tick = yf.Ticker(ticker)
    
    #general stock info
    info = tick.info
    
    #tick.financials
    reduced_financials_keys = ['Total Revenue',
                              'Total Operating Expenses',
                              'Cost Of Revenue',
                              'Operating Income',
                              'Net Income',
                              'Research Development'                       
                              ]
    reduced_financials = tick.financials.transpose()[reduced_financials_keys]
    
    #tick.major_holders 
    
    #tick.balance_sheet
    balance_sheet = tick.balance_sheet.transpose()
    #add Non Current Assets/Liabilities (necessary for bar and sunburst charts)
    balance_sheet['Non Current Assets'] = balance_sheet['Total Assets'] - balance_sheet['Total Current Assets']
    balance_sheet['Non Current Liabilities'] = balance_sheet['Total Liab'] - balance_sheet['Total Current Liabilities']
    
    #tick.cashflow #not used, could be
    
    #tick.earnings #not used, could be
    
    return prices, info, reduced_financials, balance_sheet
    

def priceChart(info, prices): #price chart function - top dead center
    ma50 = prices['Close'].rolling(50).mean()
    ma200 = prices['Close'].rolling(200).mean()

    price_chart = go.Figure(data=[
        go.Scatter(
            x=prices.index,
            y=prices['Close'],
            name='Close Price',
            marker={'color':'#ffffff', 'size':2},
            mode='markers'),
        go.Scatter(
            x=prices.index,
            y=ma50,
            name='50-day Moving Average'),
        go.Scatter(
            x=prices.index,
            y=ma200,
            name='200-day Moving Average')
        ])
    
    price_chart.update_layout(
        xaxis_title='Date',
        yaxis_title='Close Price (USD)',
        title='%s Price per Share (%s)'%(info['shortName'], info['symbol']))

    return price_chart

def financialsTimeline(reduced_financials): #row 2, left side
    fin_plot = px.line(
        reduced_financials, 
        x=reduced_financials.index, 
        y=reduced_financials.columns,
        title = 'Recent Annual Cashflows',
        color_discrete_sequence = ['#ffffff', '#DE3B3E', '#EC6C5B', '#B2C7AD', '#00CC96', '#83B0D6']
    )
    fin_plot.update_traces(hovertemplate='%{y} <br> %{x}')
    fin_plot.update_layout(xaxis_title='Date', 
                           yaxis_title='USD',
                           legend_title="")
    return fin_plot

def printInfo(info): #row two, right side
    # lots of info to pick from, what do you want?
    name = info['longName']
    snam = info['shortName']
    summ = info['longBusinessSummary']
    web = info['website']
    ind = info['industry']
    sect = info['sector']
    price = info['currentPrice']
    fpe = info['forwardPE']
    tpe = info['trailingPE']
    #fte = into['fullTimeEmployees']
    cap = info['marketCap']
    rec = info['recommendationKey']
    tplow = info['targetLowPrice']
    tpavg = info['targetMeanPrice']
    tpmid = info['targetMedianPrice']
    tphigh = info['targetHighPrice']
    #peg = 
    ebitda = info['ebitda'] #earnings before interest, tax, depreciation, amoritization
    dte = info['debtToEquity']
    #spe = #shiller pe (standardized w/ inflation)
    try:
        debitda = info['totalDebt'] / ebitda #debt to ebitda
    except:
        debitda = "N/A"
    
    text = (f'{name}    {web}'+'\n',
            f'Sector: {sect};    Industry: {ind}'+'\n',
            f'Current Price per Share: ${price};    Market Capitalization: ${cap:,.0f}'+'\n',
            f'Trailing P/E: {tpe:.2f};    Forward P/E: {fpe:.2f}'+'\n',
            f'Debt to EBITDA Ratio: {debitda:.3}'+'\n',
            f'{summ}')
    return text
    
    
def balanceSheetPlots(balance_sheet): # could be two separate functions
    #Assets v Liab bar chart - 3rd row, left
    x = ['Total Assets', 'Total Liabilities']
    #y's to seperate btwn current/non
    y_cur = balance_sheet[['Total Current Assets', 'Total Current Liabilities']].iloc[0]
    y_nc = balance_sheet[['Non Current Assets', 'Non Current Liabilities']].iloc[0]
    colors = ['#1f77b4', '#ff7f0e'] # considering using custom color scheme here 

    bs_bar = go.Figure(data=[
        go.Bar( #remove for total
            name='Non-Current',
            x=x,
            y=y_nc,
            marker_color=['#83B0D6','#EC6C5B'],
            #marker_color=colors[0], #
            hovertemplate = '<b>Non-Current:</b> $%{y:,.0f},<extra></extra>'),
        go.Bar(
            name ='Current',
            x=x, 
            y=y_cur, 
            marker_color=['#4A85BE','#DE3B3E'], #
            hovertemplate= '<b>Current:</b> $%{y:,.0f},<extra></extra>')
        ])
    bs_bar.update_layout(
        barmode='group', # remove for total
        title='Assets vs Liabilities',
        yaxis={'title': 'USD'},
        showlegend=False
        )
    
    # sunburst: Balance Sheet Breakdown - row 3 right
    # yf doesn't return same set for every ticker. Need to account for missing outputs.
    labels = []
    parents = []
    parent_dict={'Total Assets':'', 
                     'Total Current Assets':'Total Assets', 
                         'Inventory':'Total Current Assets', 
                         'Net Receivables':'Total Current Assets', 
                         'Cash':'Total Current Assets',
                         'Short Term Investments':'Total Current Assets',
                         'Other Current Assets':'Total Current Assets',
                     'Non Current Assets':'Total Assets',
                         'Property Plant Equipment':'Non Current Assets',
                         'Long Term Investments':'Non Current Assets',
                         'Other Assets':'Non Current Assets',
                 'Total Liab':'',
                     'Total Current Liabilities':'Total Liab',
                         'Accounts Payable':'Total Current Liabilities',
                         'Short Long Term Debt':'Total Current Liabilities',
                         'Other Current Liab':'Total Current Liabilities',
                     'Non Current Liabilities':'Total Liab',
                         'Long Term Debt':'Non Current Liabilities',
                         'Other Liab':'Non Current Liabilities'}
    
    #create labels/parents according to dict and data
    for key in parent_dict.keys():
        if key in balance_sheet.columns:  
            labels.append(key)
            parents.append(parent_dict[key])
    
    #build color chart based on label values 
    colors=[]
    for label in labels:
        if label=='Total Current Assets':
            colors.append('#4A85BE')
        elif label=='Non Current Assets':
            colors.append('#83B0D6')
        elif label=='Total Current Liabilities':
            colors.append('#DE3B3E')
        elif label=='Non Current Liabilities':
            colors.append('#EC6C5B')
        elif label=='Total Assets':
            colors.append('#669aca ')
        elif label=='Total Liab':
            colors.append('#e5544c')
        else:
            colors.append('#ffffff')
            
    #finish color chart based on parent values (less typing this way)
    for i, parent in enumerate(parents):
        if parent=='Total Current Assets':
            colors[i]=('#4A85BE')
        elif parent=='Non Current Assets':
            colors[i]=('#83B0D6')
        elif parent=='Total Current Liabilities':
            colors[i]=('#DE3B3E')
        elif parent=='Non Current Liabilities':
            colors[i]=('#EC6C5B')
            
    #create sunburst
    bs_sunburst = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=balance_sheet[labels].iloc[0],
        branchvalues='total',
        hovertemplate='%{label} <br> $%{value:,.0f}<extra></extra>',
        marker={'colors':colors}
        #color_discrete_map={'(?)':'black', 'Total Assets':'gold', 'Total Liab':'darkblue'}
    ))

    bs_sunburst.update_layout(
        title='Balance Sheet Breakdown',
        margin = dict(r=0, b=10, t=50, l=50)
        )
    return bs_bar, bs_sunburst

#create dash app
app = dash.Dash(__name__, title='Buy-Son Stock Evaluator')

#create html layout
app.layout = html.Div(children=[html.Div(children=[html.A("Big Ol' Buffalo Detector",
                                                          href='http://bigolbuffalo.com/'),
                                                   html.A('Enter the Bison',
                                                          href='http://bigolbuffalo.com/EnterTheBison.html'),
                                                   html.A('Buffalo Bark Machine',
                                                          href='http://bigolbuffalo.com/BuffaloBarkMachine.html'),
                                                   html.A('Buy-Son',
                                                          href='http://54.89.208.102:8050/')],
                                         className='topnav'),
                      
                                html.Div(children=[html.H1('Buy-Son (Stock Evaluation Dashboard)',
                                                  style={'textAlign': 'center',
                                                         'font-size': 32}),
                                          html.H2('~10s to retrieve new data',
                                                  style={'textAlign': 'center',
                                                         'font-size': 16}),
                                          
                                          html.P('Select a company from the dropdown list, or enter your own ticker symbol.'),
                                          html.P('The year range slider only applies to the price chart. Data from financial reports is always for the past 3 years (the maximum provided by Yahoo Finance).'),
                                          
                                          html.H3('Company:'),
                                          
                                          dcc.Dropdown(id='company-dropdown', 
                                                       options=[
                                                          {'label': 'Apple : AAPL', 'value': 'AAPL'},
                                                          {'label': 'Microsoft : MSFT', 'value': 'MSFT'},
                                                          {'label': 'Alphabet (CLass A) : GOOGL', 'value': 'GOOGL'},
                                                          {'label': 'Alphabet (Class C) : GOOG', 'value': 'GOOG'},
                                                          {'label': 'Amazon : AMZN', 'value': 'AMZN'},
                                                          {'label': 'Tesla : TSLA', 'value': 'TSLA'},
                                                          {'label': 'Berkshire Hathaway (Class B) : BRK-B', 'value': 'BRK-B'},
                                                          {'label': 'NVIDIA : NVDA', 'value': 'NVDA'},
                                                          {'label': 'Meta (Class A) : META', 'value': 'META'},
                                                          {'label': 'UnitedHealth : UNH', 'value': 'UNH'},
                                                          {'label': 'Visa : V', 'value': 'V'},
                                                          {'label': 'Johnson & Johnson : JNJ', 'value': 'JNJ'},
                                                          {'label': 'Walmart : WMT', 'value': 'WMT'},
                                                          {'label': 'JPMorgan Chase & Co. : JPM', 'value': 'JPM'},
                                                          {'label': 'The Procter & Gamble Company : PG', 'value': 'PG'},
                                                          {'label': 'Mastercard Incorporated : MA', 'value': 'MA'},
                                                          {'label': 'Bank of America Corporation : BAC', 'value': 'BAC'},
                                                          {'label': 'Exxon Mobil Corporation : XOM', 'value': 'XOM'},
                                                          {'label': 'The Home Depot : HD', 'value': 'HD'},
                                                          {'label': 'Chevron Corporation : CVX', 'value': 'CVX'}
                                                          ],
                                                       value='AAPL',
                                                       placeholder='no selection',
                                                       searchable=True,
                                                       style={'width': '50%', 'color':'#111111'}
                                                       ),     
                                          
                                          #custom ticker input/button
                                          dcc.Input(id='custom-ticker',
                                                    value='',
                                                    style={'width':'5%'}),
                                          html.Button('Add Symbol & Run', id='button', n_clicks=0),
                                          ###
                                          
                                          html.Br(),
                                          
                                          html.H3('Year(s):'),
                                          
                                          dcc.RangeSlider(id='year-slider', 
                                                          min=1993, max=2022, step=1,
                                                          marks={int(n) : {'label' : str(n), 'style':{'color':'#ffffff'}} for n in range(1993, 2023)},
                                                          value=[2018, 2022]
                                                          ),
                                          
                                          html.Br(),
                                          
                                          html.Div(dcc.Graph(id='historical-close-price-chart')),
                                          
                                          html.Div(children=(
                                              html.Div(dcc.Graph(id='historical-financials-chart'),
                                                       style={'height':50}),
                                              dcc.Markdown(id='info-text', 
                                                           style={'break-inside':'avoid-column'})
                                              ),
                                              style={'columnCount':2,
                                                     'column-gap':'0px',
                                                     'min-height':500}
                                              ),
                                              
                                          html.Div(children=(
                                              html.Div(dcc.Graph(id='balance-sheet-bar-chart')),
                                              html.Div(dcc.Graph(id='balance-sheet-sunburst-chart'))
                                              ),
                                              style={'columnCount':2, 'column-gap':'0px', 'margin-bottom':25}
                                          ),
                                          
                                          html.Br(),
                                          
                                          html.Hr(),
                                          
                                          html.Br(),
                                          
                                          html.Div(children=(
                                              html.P('This dashboard is designed around a "value investing" strategy. How does the price relate to the current and anticipated future earnings of a company?'),
                                              html.P('Looking at these charts, you should be able to get some idea of the recent earnings trajectory of a company, its potential for financial improvement and stability, and the relative price.'),
                                              html.P('Central to this analysis is the "price-to-earnings" ratio, or P/E, which is the price per dollar of annual earnings currently offered by the stock. A PE of 1 means that your share would "earn" (though not paid to YOU) its value each year. A PE of 10 means it would earn a 100% ROI in 10 years, and so on. Of course, this must be weighed against future expectations for the company. A PE of 100 may be justified if the company can be expected to dramatically increase (~10x) earnings in the near future.'),
                                              ),
                                              style={'textAlign':'center'}
                                              ),
                                          
                                          html.Br(),
                                          
                                          html.H3('Notable Terms and Definitions:'),
                                          dcc.Markdown('***Trailing P/E:*** The price-to-earnings ratio calculated based on actual earnings over the past 12 months reported by the company.'),
                                          dcc.Markdown('***Forward P/E:*** The price-to-earnings ratio calculated based on anticipated future earnings reported by the company.'),
                                          dcc.Markdown('***EBITDA:*** Earnings before interest, taxes, depreciation, and amortization'),
                                          dcc.Markdown('***Cost of Revenue:*** Total cost of manufacturing and delivering a product or service to consumers. Used as a theoretical minimum for Total Operating expenses.'),
                                          dcc.Markdown('***Operating Income:*** Equivalent to Total Revenue minus Total Operating Expenses. Does NOT account for interest, taxes, or non-recurring expenses (e.g., lawsuits).'),
                                          
                                          html.Br(),
                                          
                                          html.A('Source Code', href='http://bigolbuffalo.com/Buy-Son-Source.txt', style={'font-style':'italic'})
                                          ],
                                          style={'color':f'{text_color}',
                                                 'backgroundColor':f'{bg_color}',
                                                 'padding':10,
                                                 'padding-top':50})
                                ])

#callback function for getting data and building plots
@app.callback([Output(component_id='historical-close-price-chart', component_property='figure'),
              Output(component_id='historical-financials-chart', component_property='figure'),
              Output(component_id='info-text', component_property='children'),
              Output(component_id='balance-sheet-bar-chart', component_property='figure'),
              Output(component_id='balance-sheet-sunburst-chart', component_property='figure')],
              [Input(component_id='company-dropdown', component_property='value'),
               Input(component_id='year-slider', component_property='value')])

def everything(ticker, year_range):
    prices, info, reduced_financials, balance_sheet = getData(ticker, year_range)
    price_chart = priceChart(info, prices)
    financials_chart = financialsTimeline(reduced_financials)
    text = printInfo(info)
    bs_bar, bs_sunburst = balanceSheetPlots(balance_sheet)
    return price_chart, financials_chart, text, bs_bar, bs_sunburst

#callback function to add new ticker to list (consequently runs plots)
@app.callback(
    [Output(component_id='company-dropdown', component_property='value'),
    Output(component_id='company-dropdown', component_property='options')],
    [Input(component_id='button', component_property='n_clicks'),
     Input(component_id='company-dropdown', component_property='options')],
    State(component_id='custom-ticker', component_property='value')
    )

def altTick(click, pick, tick): # too. much. fun.
#click=n_clicks, pick='options' picklist, tick=new ticker symbol
    if tick == '':
        tick='AAPL'
    if click > 0:
        if tick not in [dic['value'] for dic in pick]:
            #name = yf.Ticker(tick).info['shortName'] #cool idea but takes too long
            pick.append({'label': tick, 'value': tick})
    return tick, pick

#run
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050)