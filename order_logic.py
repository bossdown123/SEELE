from datetime import datetime, timedelta
from time import sleep
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import *
from alpaca.data.timeframe import TimeFrame,TimeFrameUnit
from alpaca.data.enums import Adjustment
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import OrderRequest,MarketOrderRequest 
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType,PositionSide,OrderStatus
trading_client = TradingClient('PKG5MOE0VTWFQK9PBHPR', '6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD', paper=True)
client = StockHistoricalDataClient('PKG5MOE0VTWFQK9PBHPR', '6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD')
import numpy as np
from functools import lru_cache, wraps

def cache_info_decorator(func):
    """Decorator to add caching info logging to functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        cache_info = func.cache_info()
        print(f"Cache info for {func.__name__}: {cache_info}")
        return result
    return wrapper

@lru_cache(maxsize=100000)
@cache_info_decorator
def get_asset_info(symbol):
    """Get asset information with cache info logging."""
    print(f"Fetching asset info for {symbol}")
    return trading_client.get_asset(symbol_or_asset_id=symbol)

@lru_cache(maxsize=50000)
@cache_info_decorator
def get_latest_price(symbol):
    """Get latest price with cache info logging."""
    print(f"Fetching latest price for {symbol}")
    return client.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols=symbol, feed='sip'))[symbol].ask_price

def target_rebalance(side, symbol, pos):
    #sleep(.00001)
    trades = []
    #try:
        #shortable=get_asset_info(symbol).shortable
    #except Exception as e:
    #    print(e)
    shortable=True

    if symbol in list(pos.keys()):
        position=pos[symbol]

        if position.side == side:
            print(f'{symbol}: Already in position')
        else:
            print(f'''
            found:{symbol}
            {position.side}
            {side}
            ''')
        if position.side != side:
            
            trade = MarketOrderRequest(
                symbol=symbol,
                qty=np.abs(float(pos[symbol].qty)),
                time_in_force=TimeInForce.DAY,
                side=OrderSide.BUY if side == PositionSide.LONG else OrderSide.SELL
            )
            if shortable:
                trades = [trade, trade]
                print(f'TRADE {symbol} {side}')

            elif not shortable:
                trades=[trade]

                print(f'TRADE {symbol} {side}, not shortable')
            return trades
        else:
            return []
            
    elif symbol not in list(pos.keys()):
        print(f'{symbol}: Not Found opening position at 5k')
        #price = float(pos['symbol'].current_price)#
        #price = client.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols=symbol,feed='sip'))[symbol].ask_price
        try:
            price = get_latest_price(symbol)
        except Exception as e1:
            try:
                price = float(pos['symbol'].current_price)
                print(e1)
            except Exception as e2:
                price = client.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols=symbol,feed='sip'))[symbol].ask_price
                print(e1,e2)
        trade = MarketOrderRequest(
                    symbol=symbol,
                    qty = int(2000//price) if int(2000//price)!=0 else 1,
                    time_in_force=TimeInForce.DAY,
                    side=OrderSide.BUY if side == PositionSide.LONG else OrderSide.SELL
                )
        if (side == PositionSide.LONG) or ((side == PositionSide.SHORT) and (shortable == True)):

            trades = [trade]
            print(f'TRADE {symbol} {side}')
            return trades
        else:
            return []
            
    else:
        return []
def execute(trades):
    sleep(.1)
    #if trading_client.get_clock().is_open == True:
    if False:
        print('Not open')
    else:     
        for trade in trades:
            print(trade)
            submit_and_check_order(trade)
    return trades
import concurrent.futures
 
def submit_and_check_order(trade):
    symbol = trade.symbol
    try:
        activetrade = trading_client.submit_order(trade)
    except Exception as e:
        print('failed',symbol,"reason:",e)
        #if e has message 
        if not hasattr(e, 'message'):
            return
        if 'rate' in e.message:
            sleep(1)
            activetrade = trading_client.submit_order(trade)
        if 'insufficient' in e.message:
            print('insufficient funds')
            return
    status = activetrade.status
    checks=0
    #while not (status == OrderStatus.FILLED or status == OrderStatus.ACCEPTED):
    while status != OrderStatus.FILLED:
        order = trading_client.get_order_by_id(activetrade.id)
        status = order.status
        checks=checks+1
        #clear_output()
        #print(checks)
        sleep(1)
        if order.status == OrderStatus.CANCELED:
            print('failed',symbol)
            return
        print(checks,status,symbol)

        if checks == 15:
            print('failed',symbol)
            try:
                trading_client.cancel_order_by_id(activetrade.id)
            except Exception as e:
                print(e)
            return
    print(f"{trade} \n SUCCESS")
    return trade
