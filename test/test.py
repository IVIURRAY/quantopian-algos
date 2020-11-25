from quantopian.pipeline import Pipeline  
from quantopian.algorithm import attach_pipeline, pipeline_output  
from quantopian.pipeline.data.builtin import USEquityPricing  
from quantopian.pipeline.factors import SimpleMovingAverage  
from quantopian.pipeline.filters.morningstar import Q1500US  
from quantopian.pipeline.factors import VWAP

def initialize(context):  
    # Schedule our rebalance function to run at the start of each week.  
    schedule_function(my_rebalance, date_rules.week_start(), time_rules.market_open(hours=1))

    # Record variables at the end of each day.  
    schedule_function(my_record_vars, date_rules.every_day(), time_rules.market_close())

    # Create our pipeline and attach it to our algorithm.  
    my_pipe = make_pipeline()  
    attach_pipeline(my_pipe, 'my_pipeline')

def make_pipeline():  
    """  
    Create our pipeline.  
    """

    # Base universe set to the Q1500US.  
    base_universe = Q1500US()

    # 10-day close price average.  
    mean_10 = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=10, mask=base_universe)

    # 30-day close price average.  
    mean_30 = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=30, mask=base_universe)

    percent_difference = (mean_10 - mean_30) / mean_30  
   # Filter to select securities to long.  
    longs = percent_difference.bottom(25)

    # Filter for all securities that we want to trade.  
    securities_to_trade = (longs)

    return Pipeline(  
        columns={  
            'longs': longs,  
           },  
        screen=(securities_to_trade),  
    )

def my_compute_weights(context):  
    """  
    Compute ordering weights.  
    """  
    # Compute even target weights for our long positions and short positions.  
    long_weight = 0.5 / len(context.longs)  
    return long_weight

def before_trading_start(context, data):  
    # Gets our pipeline output every day.  
    context.output = pipeline_output('my_pipeline')

    # Go long in securities for which the 'longs' value is True.  
    context.longs = context.output[context.output['longs']].index.tolist()

    context.long_weight = my_compute_weights(context)  
    
    
def handle_data(context, data):

    # Get only todays pricing data.  
    today = get_datetime()  
                                                  # 60mins * 6.5hrs market open = ~400  
    hist = data.history(['price', 'high', 'low', 'volume'], 400, '1m')  
    todays_data = hist.filter(like=str(today.date()), axis=1)  
    p = todays_data.get('price')  
    v = todays_data.get('volume')  
    h = todays_data.get('high')  
    l = todays_data.get('low')

    vwap = (v * (h+l)/2 ).cumsum() / v.cumsum()  


def my_rebalance(context, data):  
    """  
    Rebalance weekly.  
    """  
    for security in context.portfolio.positions:  
        if security not in context.longs and security and data.can_trade(security):  
            order_target_percent(security, 0)

    for security in context.longs:  
        if data.can_trade(security):  
            order_target_percent(security, context.long_weight)  


def my_record_vars(context, data):  
    """  
    Record variables at the end of each day.  
    """  
    longs = shorts = 0  
    for position in context.portfolio.positions.itervalues():  
        if position.amount > 0:  
            longs += 1  
        elif position.amount < 0:  
            shorts += 1

    # Record our variables.  
    record(leverage=context.account.leverage, long_count=longs, short_count=shorts) 
