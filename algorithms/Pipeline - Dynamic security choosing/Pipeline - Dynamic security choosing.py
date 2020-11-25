from quantopian.algorithm import attach_pipeline, pipeline_output
from quantopian.pipeline import Pipeline
from quantopian.pipeline.data.builtin import USEquityPricing
from quantopian.pipeline.factors import SimpleMovingAverage

"""
Many trading algorithms are variations on the following structure:

(1)For each asset in a known (large) universe, compute N scalar values for the asset based on a trailing window of data.

(2) Select a smaller “tradeable universe” of assets based on the values computed in (1).

(3) Calculate desired portfolio weights on the trading universe computed in (2).

(4) Place orders to move the algorithm’s current portfolio allocations to the desired weights computed in (3).

The Pipeline API module provides a framework for expressing this style of algorithm.
"""

def initialize(context):

    # Create and attach an empty Pipeline.
    pipe = Pipeline()
    pipe = attach_pipeline(pipe, name='my_pipeline')

    # Construct Factors.
    sma_10 = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=10)
    sma_30 = SimpleMovingAverage(inputs=[USEquityPricing.close], window_length=30)

    # Construct a Filter.
    prices_under_5 = (sma_10 < 5)

    # Register outputs.
    pipe.add(sma_10, 'sma_10')
    pipe.add(sma_30, 'sma_30')

    # Remove rows for which the Filter returns False.
    pipe.set_screen(prices_under_5)

def before_trading_start(context, data):
    # Access results using the name passed to `attach_pipeline`.
    results = pipeline_output('my_pipeline')
    print results.head(5)

    # Define a universe with the results of a Pipeline.
    # Take the first ten assets by 30-day SMA.
    update_universe(results.sort('sma_30').index[:10])