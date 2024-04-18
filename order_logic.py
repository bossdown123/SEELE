from datetime import datetime, timedelta
from keras.models import load_model
from time import sleep
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import *
from alpaca.data.timeframe import TimeFrame,TimeFrameUnit
from alpaca.data.enums import Adjustment
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import OrderRequest,MarketOrderRequest 
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType,PositionSide,OrderStatus
trading_client = TradingClient('PKODZGQ3BIWGQJ6A3HJ4', 'WRCojP9T9ZnV2KZeru9GRbXb41zu7bj2GjRC17XJ', paper=True)
client = StockHistoricalDataClient('PKODZGQ3BIWGQJ6A3HJ4', 'WRCojP9T9ZnV2KZeru9GRbXb41zu7bj2GjRC17XJ')
import numpy as np


def target_rebalance(side, symbol):
    trades = []
    shortable=trading_client.get_asset(symbol_or_asset_id=symbol).shortable
    pos={i.symbol:i for i in trading_client.get_all_positions()}
    
    if symbol in list(pos.keys()):
        position=pos[symbol]
    #    print(f'''
    #    found:{symbol}
    #    {position.side}
    #    {side}
       # ''')
        if position.side != side:
            
            trade = MarketOrderRequest(
                symbol=symbol,
                qty=np.abs(float(pos[symbol].qty)),
                time_in_force=TimeInForce.DAY,
                side=OrderSide.BUY if side == PositionSide.LONG else OrderSide.SELL
            )
            if shortable:
                trades = [trade, trade]
            elif not shortable:
                trades=[trade]
            print(f'TRADE {symbol} {side}')
            return trades
        else:
            return []
        
    elif symbol not in list(pos.keys()):
        print(f'{symbol}: Not Found opening position at 5k')
        price = client.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols=symbol,feed='sip'))[symbol].ask_price
        trade = MarketOrderRequest(
                    symbol=symbol,
                    qty = int(5000/price),
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
    if trading_client.get_clock().is_open == False:
        print('Not open')
    else:     
        for trade in trades:
            print(trade)
            submit_and_check_order(trade)
    
def submit_and_check_order(trade):
    symbol = trade.symbol
    activetrade = trading_client.submit_order(trade)
    status = activetrade.status
    checks=0
    while status != OrderStatus.FILLED:
        order = trading_client.get_order_by_id(activetrade.id)
        status = order.status
        checks=checks+1
        #clear_output()
        #print(checks)
        sleep(1)
        print(checks)

        if checks == 15:
            print('failed',symbol)
            trading_client.cancel_order_by_id(activetrade.id)
            break
        print(f"{trade} \n SUCCESS")