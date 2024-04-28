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


import requests


def get_all_positions():
    url = "https://paper-api.alpaca.markets/v2/positions"

    headers = {
    "accept": "application/json",
    "APCA-API-KEY-ID": "PKG5MOE0VTWFQK9PBHPR",
    "APCA-API-SECRET-KEY": "6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD"
    }

    response = requests.get(url, headers=headers)
    return response.json()
def target_rebalance(side, symbol, pos):
    #sleep(.00001)
    trades = []
    #try:
        #shortable=get_asset_info(symbol).shortable
    #except Exception as e:
    #    print(e)
    shortable=trading_client.get_asset(symbol_or_asset_id=symbol).shortable

    if symbol in list(pos.keys()):
        position=pos[symbol]

        if position['side'] == side:
            #sys.stdout.write(f'{symbol}: Already in position\n')
            return []
        else:
            pass
            #print(f'''
            #found:{symbol}
            #{position.side}
            #{side}
            #''')
        if position['side'] != side:
            
            trade = MarketOrderRequest(
                symbol=symbol,
                qty=np.abs(float(pos[symbol]['qty'])),
                time_in_force=TimeInForce.DAY,
                side=OrderSide.BUY if side == PositionSide.LONG else OrderSide.SELL
            )
            if shortable:
                trades = [trade, trade]
             #   print(f'TRADE {symbol} {side}')

            elif not shortable:
                trades=[trade]

              #  print(f'TRADE {symbol} {side}, not shortable')
            return trades
        else:
            return []
            
    elif symbol not in list(pos.keys()):
        #price = float(pos['symbol'].current_price)#
        price = client.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols=symbol,feed='sip'))[symbol].ask_price
        price=float(price)
        qty = int(2500//price) if int(3000//2500)!=0 else 1
     #   print(f'{symbol}: Not Found opening position at val: {price*qty} {qty} {price} {side}')


        trade = MarketOrderRequest(
                    symbol=symbol,
                    qty = qty,
                    time_in_force=TimeInForce.DAY,
                    side=OrderSide.BUY if side == PositionSide.LONG else OrderSide.SELL
                )
        if (side == PositionSide.LONG) or ((side == PositionSide.SHORT) and (shortable == True)):

            trades = [trade]
           # print(f'TRADE {symbol} {side}')
            return trades
        else:
            return []
            
    else:
        return []
def executea(trades):

    sleep(.1)
    #if trading_client.get_clock().is_open == True:
    if False:
        print('Not open')
    else:     
        
        for trade in trades:
            print(trade)
            submit_and_check_order(trade)

    return trades
from datetime import datetime, timezone
def executae(trades):
    dt=datetime.now(timezone.utc)
    if not (dt>dt.replace(hour=13,minute=30) and dt<dt.replace(hour=20) and dt.weekday()<5 and dt.weekday()>0):
        print('Not trading hours')
    else:     
        for trade in trades:
            print(trade)
            max_tries=10
            for i in range(max_tries):
                try:
                    submit_and_check_order(trade)
                except Exception as e:
                    print(f"Failed to execute trade: {trade.symbol} {trade.side} {trade.qty} {trade.time_in_force} {trade.type}: {e}")
                    sleep(1)
                    
                    
    return trades

 
def submit_and_check_order(trade):
    symbol = trade.symbol
    try:
        activetrade = trading_client.submit_order(trade)
    except Exception as e:
        print(f"Failed to get order: {e}")
        sleep(1)    
        activetrade = trading_client.submit_order(trade)

    for check in range(checks):
        try:
            order = trading_client.get_order_by_id(activetrade.id)
        except Exception as e:
            print(f"Failed to get order: {e}")
            sleep(1)
            order = trading_client.get_order_by_id(activetrade.id)
        
        if order.status == OrderStatus.CANCELED:
            print('canceled',symbol)
            return
        if order.status == OrderStatus.FILLED:
            print(f"{trade} \n SUCCESS\n")
            return trade
        sleep(1)
        print(f"Check {check+1}: {order.status} for {symbol}")
    print('failed',symbol," ateempting to cancel")
    try:
        trading_client.cancel_order_by_id(activetrade.id)
    except Exception as e:
        print("Failed to cancel order: ", e)
    return None

import sys
from datetime import datetime, timezone
import time

class TradeStateMachine:
    def __init__(self, trades, trading_client):
        self.trades = trades
        self.trading_client = trading_client

    def run(self):
        if not self.check_trading_hours():
            print('Not trading hours')
            return []

        executed_trades = []
        for trade in self.trades:
            if self.process_trade(trade):
                executed_trades.append(trade)
            #time.sleep(1)
        return executed_trades

    def check_trading_hours(self):
        dt = datetime.now(timezone.utc)
        return dt.replace(hour=13, minute=30) <= dt < dt.replace(hour=20) and 0 < dt.weekday() < 5

    def process_trade(self, trade):
        max_tries = 10
        for try_count in range(max_tries):
            if self.submit_order(trade):
                return self.check_order_status(trade)
            #time.sleep(1)
        return False

    def submit_order(self, trade):
        try:
            self.activetrade = self.trading_client.submit_order(trade)
            return True
        except Exception as e:
            #print(f"Attempt to submit order failed: {e}")
            return False

    def check_order_status(self, trade):
        checks = 5
        for check_count in range(checks):
            try:
                order = self.trading_client.get_order_by_id(self.activetrade.id)
                #print(f"Check {check_count + 1}: {order.status} for {trade.symbol}")
                if order.status == OrderStatus.CANCELED:
                    #print('Canceled', trade.symbol)
                    return False
                if order.status == OrderStatus.FILLED:
                    
                    #sys.stdout.write(f"{trade} \n SUCCESS\n")
                    return True
            except Exception as e:
                #print(f"Attempt to check order status failed: {e}")
                if check_count == checks - 1:  # Last check attempt
                    self.cancel_order(trade)
            time.sleep(.5)
        return False

    def cancel_order(self, trade):
        try:
            self.trading_client.cancel_order_by_id(self.activetrade.id)
        except Exception as e:
            #print(f"Failed to cancel order: {e}")
            pass

def execute(trades):
    machine = TradeStateMachine(trades, trading_client)
    return machine.run()