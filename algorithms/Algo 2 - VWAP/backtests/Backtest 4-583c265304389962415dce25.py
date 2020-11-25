"""
This is a template algorithm on Quantopian for you to adapt and fill in.
"""
from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import AverageDollarVolume
from quantopian.pipeline.filters.morningstar import Q500US
import pandas as pd


def initialize(context):
    """
    Called once at the start of the algorithm.
    """   
    # Rebalance every day, at market open.
    schedule_function(rebalance, date_rules.every_day(), time_rules.market_open())
     
    # Record tracking variables at the end of each day.
    schedule_function(record_vars, date_rules.every_day(), time_rules.market_close())
    
    # Close Positon at the end of each day.
    schedule_function(close_all, date_rules.every_day(), time_rules.market_close(minutes=2))
    
    # Create our dynamic stock selector.
    #attach_pipeline(make_pipeline(), 'my_pipeline')
    #################### TODO ######################
    # MAKE A PIPELINE THAT RETURNS THE TOP 5 STOCKS WITH HIGH VOLUME TODAY
    ################################################
    context.security_list = [sid(8554)]
    context.still_open_orders = []
         
def make_pipeline():
    """
    A function to create our dynamic stock selector (pipeline). Documentation on
    pipeline can be found here: https://www.quantopian.com/help#pipeline-title
    """
    
    # Base universe set to the Q500US
    base_universe = Q500US()

    # Factor of yesterday's close price.
    yesterday_close = USEquityPricing.close.latest
     
    pipe = Pipeline(
        screen = base_universe,
        columns = {
            'close': yesterday_close,
        }
    )
    return pipe
 
def before_trading_start(context, data):
    """
    Called every day before market open.
    """
    opens = get_open_orders()
    for order in opens:
        log.info('Still order open for %s' % order)
        context.still_open_orders.append(order)

     
def close_all(context, data):
    """
    Close all positions at the end of the day.
    """
    for sec in context.security_list:
        log.info('Closing trade for %s as its EOD' % sec.symbol)
        order_target_percent(sec, 0)
 
def rebalance(context,data):
    """
    Execute orders according to our schedule_function() timing. 
    """
    for order in context.still_open_orders:
        log.info('WARNING WARING NEED TO CLOSE THIS POSTIONS! %s' % order)
    
    pass
 
def record_vars(context, data):
    """
    Plot variables at the end of each day.
    """
    pass
 
def handle_data(context,data):
    """
    Called every minute.
    """
    
    # Get only todays pricing data.
    today = get_datetime()
                                                  # 60mins * 6.5hrs market open = ~400
    hist = data.history(context.security_list, ['price', 'high', 'low', 'volume'], 400, '1m')
    
    todays_data = hist.filter(like=str(today.date()), axis=1)
  
    p = todays_data.get('price')
    v = todays_data.get('volume')
    h = todays_data.get('high')
    l = todays_data.get('low')

    vwap = (v * (h+l)/2 ).cumsum() / v.cumsum()
    ma = pd.ewma(p, span=15)
    todays_ma = ma.values[-1][0]
    previous_ma = ma.values[-2][0] if len(ma) > 1 else todays_ma
    current_vwap  = vwap[-1:].iloc[0][0]
    current_price = p[-1:].iloc[0][0]
    
    downtrend = True if previous_ma > todays_ma else False
    uptrend = True if previous_ma < todays_ma else False
    long_pos =  True if context.portfolio.positions[context.security_list[0].sid].amount > 0 else False
    short_pos = True if context.portfolio.positions[context.security_list[0].sid].amount < 0 else False
    
    if abs(current_vwap - current_price) < 0.01:
        log.info('VWAP is close to the actual price at %s' % today)
        if not long_pos and not short_pos:
            if uptrend: 
                log.info('Uptrend I will long')
                order_target_percent(context.security_list[0], 1)
            if downtrend: 
                log.info('Downtrend I will short')
                order_target_percent(context.security_list[0], -1)    
        if (long_pos and downtrend) or (short_pos and uptrend):
            log.info('Close')
            order_target_percent(context.security_list[0], 0)
