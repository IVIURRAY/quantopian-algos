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
    # schedule_function(rebalance, date_rules.every_day(), time_rules.market_open())
     
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
    sma_short = 35
    sma_long = 45
    
    short_sma = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=sma_short) 
    long_sma = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=sma_long)
    
    symbol = SidInList(sid_list=(8554)) # Only show values for the S&P500
    
    return Pipeline(
        columns={
            'SMA_short': short_sma,
            'SMA_long': long_sma,
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
    Execute orders according to our schedule_function() timing. 
    """
    pass
 
def record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    pass
 
def cal_vwap(context, data):
    """
    Calculate VWAP
    """
    d = data.history(context.output.index[0], ['high', 'low', 'close', 'volume'], 390, '1m')
    todays_data = d.filter(like=str(get_datetime().date()), axis=0)
    
    h = todays_data.get('high')
    l = todays_data.get('low')
    c = todays_data.get('close')
    v = todays_data.get('volume')
    
    # I THINK I MIGHT BE WORKING OUT THE VWAP FOR JUST THE FIRST BAR OF DATA AND NOT THE WHOLE DAY?
    
    return ((v * (h+l+c)/3 ).cumsum() / v.cumsum())[-1]
    
def handle_data(context,data):
    """
    Called every minute.
    """
    spy = context.output.index[0]
    short_sma = context.output['SMA_short'][0]
    long_sma = context.output['SMA_long'][0]
    
    vwap = cal_vwap(context, data)
    upper_vwap = vwap*1.01
    lower_vwap = vwap*0.99
    price = data.history(spy, 'price', 1, '1m')[-1]
    
    long_pos =  True if context.portfolio.positions[spy.sid].amount > 0 else False
    short_pos = True if context.portfolio.positions[spy.sid].amount < 0 else False
    
    if (lower_vwap < price < upper_vwap) and (not long_pos and not short_pos):
        if short_sma > long_sma:
            order_target_percent(spy, 1)
        if short_sma < long_sma:
            order_target_percent(spy, -1)
            
    if long_pos and short_sma < long_sma:
        order_target_percent(spy, 0)
    if short_pos and short_sma > long_sma:
        order_target_percent(spy, 0)
        
        
        
    
    
    
        
    
    
    
    
    
