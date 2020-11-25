"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import RSI
from quantopian.pipeline import CustomFilter
import numpy as np
 

class SidInList(CustomFilter):  
    """  
    Filter on given SID.
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
    # Rebalance every day at market close.
    schedule_function(my_rebalance, date_rules.every_day(), time_rules.market_close())
     
    # Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'my_pipeline')
         
def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation on
    pipeline can be found here: https://www.quantopian.com/help#pipeline-title
    """
    
    rsi = RSI(inputs=[USEquityPricing.close], window_length=10)
    symbol = SidInList(sid_list=(8554))
    
    return Pipeline(
        columns={
            'RSI': rsi,
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
     
 
def my_rebalance(context,data):
    """
    Execute orders according to our schedule_function() timing. 
    """
    rsi = context.output['RSI'][0]
    spy = context.output.index[0]
    overbought = 55
    oversold = 45
    
    long_pos =  True if context.portfolio.positions[spy.sid].amount > 0 else False
    short_pos = True if context.portfolio.positions[spy.sid].amount < 0 else False
    
    if not long_pos and not short_pos:
        if rsi >= overbought:
            order_target_percent(spy, -1)
        if rsi <= oversold:
            order_target_percent(spy, 1)
            
    if long_pos and rsi > overbought:
        order_target_percent(spy, 0)
    
    if short_pos and rsi < oversold:
        order_target_percent(spy, 0)

    # maybe if rsi is between 45 and 55 then we should close the position
