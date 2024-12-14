from datetime import datetime, timedelta
from IPython.display import display, clear_output
from keras.models import load_model
from time import sleep
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import *
from alpaca.data.timeframe import TimeFrame,TimeFrameUnit
from alpaca.data.enums import Adjustment
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import OrderRequest,MarketOrderRequest 
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType,PositionSide,OrderStatus
trading_client = TradingClient(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'), paper=True)
client = StockHistoricalDataClient(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'))
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
                    qty = int(2000/price),
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
def executeA(trades):
    if trading_client.get_clock().is_open == False:
        print('Not open')
    else:     
        for trade in trades:
            print("TO EXCHANGE\n"+str(trade))
            submit_and_check_order(trade)
    
def submit_and_check_orderA(trade):
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
        
        
import asyncio 
import os
        
async def execute(trades, trading_client):
    clock = trading_client.get_clock()
    if not clock.is_open:
        print('Market is not open.')
    else:
        tasks = [submit_and_check_order(trade, trading_client) for trade in trades]
        results = await asyncio.gather(*tasks)
        for result in results:
            print("Order Result:", result)

async def submit_and_check_order(trade, trading_client):
    symbol = trade.symbol
    activetrade = trading_client.submit_order(trade)
    status = activetrade['status']
    checks = 0

    while status != 'FILLED':  # Assuming 'FILLED' is the status 
        order = trading_client.get_order_by_id(activetrade['id'])
        status = order['status']
        checks += 1
        await asyncio.sleep(1)  # Non-blocking sleep
        print(checks)

        if checks == 15:
            print('failed', symbol)
            trading_client.cancel_order_by_id(activetrade['id'])
            return 
        if status == 'FILLED':
            print(f"Order for {symbol} SUCCESS")
            return 
