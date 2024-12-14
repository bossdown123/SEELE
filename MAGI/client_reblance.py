from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import *
from alpaca.data.timeframe import TimeFrame,TimeFrameUnit
from alpaca.data.enums import Adjustment
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import OrderRequest,MarketOrderRequest 
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType,PositionSide,OrderStatus
API_KEY = os.getenv('APCA_API_KEY_ID')
API_SECRET = os.getenv('APCA_API_SECRET_KEY')

trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
client = StockHistoricalDataClient(API_KEY, API_SECRET)

import asyncio
import pandas as pd
import json
from ably import AblyRealtime
import random
import os
sys_id = str(random.randint(0, 10000000000))
TARGET_VALUE_PER_STOCK = 2500

async def rebalance():
    positions = trading_client.get_all_positions()
    trades = []

    for position in positions:
        symbol = position.symbol
        qty = int(position.qty)
        current_price = float(position.current_price)
        current_value = qty * current_price
        if position.side == PositionSide.LONG:
            needed_value = TARGET_VALUE_PER_STOCK - current_value
        else:  # Handling short positions
            needed_value = -(TARGET_VALUE_PER_STOCK + current_value)  # Target for short is to have negative value

        needed_qty = int(needed_value / current_price)

        if needed_qty > 0:
            side = OrderSide.BUY
        else:
            side = OrderSide.SELL
            needed_qty = abs(needed_qty)

        if needed_qty != 0:
            trade = MarketOrderRequest(
                symbol=symbol,
                qty=needed_qty,
                side=side,
                time_in_force=TimeInForce.DAY
            )
            trades.append(trade)
            print(f"{side} {needed_qty} of {symbol}")

    # Execute trades
    if trades:
        for trade in trades:
            response = trading_client.submit_order(trade)
            print(response)

async def main():
    await rebalance()


        
asyncio.run(main())