import tensorflow as tf
import numpy as np
from tensorflow import keras
from keras.models import *
import asyncio
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
from utils import MultiScalerOld
import pickle as pkl


from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import *
from alpaca.data.timeframe import TimeFrame,TimeFrameUnit
from alpaca.data.enums import Adjustment
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import OrderRequest,MarketOrderRequest 
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType,PositionSide,OrderStatus
trading_client = TradingClient('PKODZGQ3BIWGQJ6A3HJ4', 'WRCojP9T9ZnV2KZeru9GRbXb41zu7bj2GjRC17XJ', paper=True)
client = StockHistoricalDataClient('PKODZGQ3BIWGQJ6A3HJ4', 'WRCojP9T9ZnV2KZeru9GRbXb41zu7bj2GjRC17XJ')


with open('multi_scaler.pickle','rb') as f:
    multi_scaler=pkl.load(f)
    
model=load_model('model.keras')

stocks=['AAPL','AMZN','GOOGL','MSFT','TSLA']

async def target_rebalance(side, symbol):
    trades = []
    shortable = (trading_client.get_asset(symbol_or_asset_id=symbol)).shortable
    positions = trading_client.get_all_positions()
    pos = {i.symbol: i for i in positions}
    
    if symbol in pos:
        position = pos[symbol]
        if position.side != side:
            trade = MarketOrderRequest(
                symbol=symbol,
                qty=abs(float(position.qty)),
                time_in_force=TimeInForce.DAY,
                side=OrderSide.BUY if side == PositionSide.LONG else OrderSide.SELL
            )
            trades = [trade, trade] if shortable else [trade]
            print(f'TRADE {symbol} {side}')
            return trades
        else:
            return []

    else:
        print(f'{symbol}: Not Found. Opening position at 5k')
        price_info = client.get_stock_latest_quote(StockLatestQuoteRequest(symbol_or_symbols=symbol, feed='sip'))
        price = price_info[symbol].ask_price
        trade = MarketOrderRequest(
            symbol=symbol,
            qty=int(5000 / price),
            time_in_force=TimeInForce.DAY,
            side=OrderSide.BUY if side == PositionSide.LONG else OrderSide.SELL
        )
        if (side == PositionSide.LONG) or ((side == PositionSide.SHORT) and shortable):
            trades = [trade]
            print(f'TRADE {symbol} {side}')
            return trades
        else:
            return []

async def execute(trades):
    if not (trading_client.get_clock()).is_open:
        print('Market not open')
        #return

    for trade in trades:
        await submit_and_check_order(trade)

async def submit_and_check_order(trade):
    symbol = trade.symbol
    active_trade = trading_client.submit_order(trade)
    status = active_trade.status
    checks = 0

    while status != OrderStatus.FILLED:
        order = trading_client.get_order_by_id(active_trade.id)
        status = order.status
        checks += 1
        await asyncio.sleep(1)  # Sleep asynchronously
        print(f'Check {checks} for {symbol}')

        if checks >= 15:
            print(f'Order failed for {symbol}')
            trading_client.cancel_order_by_id(active_trade.id)
            break



async def get_stock_bars(stock):
    bars=yf.Ticker(stock).history(period='1d',interval='1m')
    return bars
async def preprocess_bars(bars):
    bars=bars.loc[:,['Open','High','Low','Close']]
    bars.columns=['open','high','low','close']
    bars=bars.diff().rolling(3).mean().dropna()
    return multi_scaler.transform(bars.tail(26)).values.reshape(1,26,4)
async def predict(x):
    return float(model.predict(x).argmax(1))
    
async def trade_stock(stock, side):
    bars = await get_stock_bars(stock)
    if bars.empty:
        print(f"No data for {stock}")
        return
    preprocessed_bars = await preprocess_bars(bars)
    side_predicted = await predict(preprocessed_bars)
    trades = await target_rebalance(side_predicted, stock)
    if trades:
        await execute(trades)
import datetime

async def main():
    tasks = [trade_stock(stock, 'LONG') for stock in stocks]  # Initial position assumed as 'LONG' for example
    await asyncio.gather(*tasks)

# Run the main function
if __name__ == "__main__":
    first_time = True
    while True:
        if datetime.datetime.now().minute in [00, 15, 30, 45] or first_time:
            asyncio.run(main())
            first_time = False
