"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import RSI, SimpleMovingAverage
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
    # Rebalance every day, 1 hour after market open.
    # schedule_function(rebalance, date_rules.every_day(), time_rules.market_open(hours=1))
     
    # Create our dynamic stock selector.
    attach_pipeline(make_pipeline(), 'my_pipeline')
         
def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation on
    pipeline can be found here: https://www.quantopian.com/help#pipeline-title
    """
    
    sma_short = 35
    sma_long = 50
    
    short_sma = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=sma_short) 
    long_sma = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=sma_long)
    rsi = RSI(inputs=[USEquityPricing.close], window_length=10)
    
    symbol = SidInList(sid_list=(8554))
    
    return Pipeline(
        columns={
            'RSI': rsi,
            'SMA_short': short_sma,
            'SMA_long': long_sma,
            'symbol': symbol,
       },
       screen=symbol,
    )
 
def cal_vwap(context, data):
    """
    Calculate VWAP
    """
                                                  # 60mins x 6.5hrs market open = 390
    d = data.history(context.output.index[0], ['high', 'low', 'close', 'volume'], 390, '1m')
    todays_data = d.filter(like=str(get_datetime().date()), axis=0)
    
    h = todays_data.get('high')
    l = todays_data.get('low')
    c = todays_data.get('close')
    v = todays_data.get('volume')
    
    return ((v * (h+l+c)/3 ).cumsum() / v.cumsum())[-1] 
    
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
 

 
def handle_data(context,data):
    """
    Called every minute to calculate VWAP and work out whether to enter or not.
    """
    spy = context.output.index[0]
    long_pos =  True if context.portfolio.positions[spy.sid].amount > 0 else False
    short_pos = True if context.portfolio.positions[spy.sid].amount < 0 else False 
    # SMA
    short_sma = context.output['SMA_short'][0]
    long_sma = context.output['SMA_long'][0]
    uptrend = short_sma > long_sma
    downtrend = short_sma < long_sma
    # RSI
    rsi = context.output['RSI'][0]
    overbought = 85
    oversold = 15
    # VWAP
    vwap = cal_vwap(context, data)
    upper_vwap = vwap*1.01
    lower_vwap = vwap*0.99
    price = data.history(spy, 'price', 1, '1m')[-1]
    
    if (lower_vwap < price < upper_vwap) and (not long_pos and not short_pos):
        if (rsi > overbought) and downtrend:
            order_target_percent(spy, -1)
        if (rsi < oversold) and uptrend:
            order_target_percent(spy, 1)
      
    # MAYBE THESE SHOULD ALSO TAKE INTO ACCOUNT RSI
    if long_pos and downtrend:
        order_target_percent(spy, 0)
    if short_pos and uptrend:
        order_target_percent(spy, 0)
    

