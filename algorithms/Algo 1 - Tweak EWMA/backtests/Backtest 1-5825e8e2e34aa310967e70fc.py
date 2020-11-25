"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume
import pandas as pd
 
def initialize(context):
    """
    Called once at the start of the algorithm.
    """   
    # Rebalance every day, at market open.
    schedule_function(rebalance, date_rules.every_day(), time_rules.market_open())
     
    # Record tracking variables at the end of each day.
    schedule_function(record_vars, date_rules.every_day(), time_rules.market_close())
    
    # Get the 'S&P 500' ticker
    context.security_list = [sid(8554)]

 
def rebalance(context,data):
    """
    Calculate the SMA strategy and generate orders based on their values.
    """
    SP500 = context.security_list[0]
    hist = data.history(context.security_list, 'close', 200, '1d')
    #  Hist returns the current price for today so get the previous
    yesterday_close = hist[-2:-1].sum()[0]
    ewma = pd.ewma(hist, span=200)[-1:].sum()[0]
    
    open_orders = get_open_orders()
    open_pos = context.portfolio.positions[SP500].amount
    pos_none = True if open_pos == 0 else False
    pos_long = True if open_pos > 0 else False
    pos_short = True if open_pos < 0 else False
    downtrend = True if yesterday_close < ewma else False
    uptrend = True if yesterday_close > ewma else False
    
    
    if not data.can_trade(SP500):
        log.warn('Cannot trade security (%s) on this exchange!' % SP500)
        return
    
    
    # If we have a position, was it long/short and sell depending on market conditions.
    if open_pos:
        if downtrend and pos_long:
            order_target_percent(SP500, 0)
        if uptrend and pos_short:
            order_target_percent(SP500, 0) 
            
    # If we have no positions, order based on trend.
    if pos_none and not open_orders:
        if uptrend:
            order_target_percent(SP500, 1)
        elif downtrend:
            order_target_percent(SP500, -1)

 
def record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    longs = shorts = 0
    for pos in context.portfolio.positions.itervalues():
        if pos.amount > 0:
            longs += 1
        elif pos.amount < 0:
            shorts += 1
    
    record(
        long_pos=longs,
        short_pos=shorts,
        pnl=context.portfolio.pnl,
        capital_used=context.portfolio.capital_used,
        cash=context.portfolio.cash,
    )
