"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import SimpleMovingAverage
from quantopian.pipeline import CustomFilter
import numpy as np
 
class SidInList(CustomFilter):  
    """  
    Filter returns True for any SID included in parameter tuple passed at creation.  
    Usage: my_filter = SidInList(sid_list=(23911, 46631))  
    """  
    inputs = []  
    window_length = 1  
    params = ('sid_list',)

    def compute(self, today, assets, out, sid_list):  
        out[:] = np.in1d(assets, sid_list)
 

def initialize(context):
    """
    Called once at the start of the algorithm.
    """   
    # Rebalance every day, at market open.
    schedule_function(rebalance, date_rules.every_day(), time_rules.market_open())
     
    # Record tracking variables at the end of each day.
    schedule_function(record_vars, date_rules.every_day(), time_rules.market_close())
    
    # Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'my_pipeline')

    
def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Used to calculate
    SMA and latest close price then filter on SID.
    """
    # n = [1, 5, 15, 25, 35, 45, 50, 100, 200]
    moving_average = 200
    
    sma = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=moving_average)
    symbol = SidInList(sid_list=(8554)) # Only show values for the S&P500
    
    return Pipeline(
        columns={
            'SMA': sma,
            'close': USEquityPricing.close.latest,
            'symbol': symbol,
       },
       screen=symbol,
    )


def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    context.output = pipeline_output('my_pipeline')
  
    # These are the securities that we are interested in trading each day.
    context.security_list = context.output.index 

    
def rebalance(context,data):
    """
    Calculate the SMA strategy and generate orders based on their values.
    """
    sma = context.output['SMA'][0]
    previous_close = context.output['close'][0]
    spy = context.output.index[0]
    
    long_pos =  True if context.portfolio.positions[spy.sid].amount > 0 else False
    short_pos = True if context.portfolio.positions[spy.sid].amount < 0 else False      
    
    if not long_pos and not short_pos:
        # No positon is held therefore take a position.
        if sma < previous_close:
            order_target_percent(spy, 1)
        if sma > previous_close:
            order_target_percent(spy, -1)
    
    if long_pos and sma > previous_close:
        # After being in a long position the trend seems to be reversing.
        order_target_percent(spy, 0)
        
    if short_pos and sma < previous_close:
        # After being in a short position the trend seems to be reversing.
        order_target_percent(spy, 0)
    
 
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
