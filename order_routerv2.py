from datetime import *

from alpaca.data.live.option import *
from alpaca.data.historical.option import *
from alpaca.data.historical import *
from alpaca.data.requests import *
from alpaca.data.timeframe import *
from alpaca.data.enums import *
from alpaca.trading.client import *
from alpaca.trading.stream import *
from alpaca.trading.requests import * 
from alpaca.trading.enums import *

from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor

import requests
import pickle as pkl
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress most warnings
import tensorflow as tf
import numpy as np
#check for assets pkl
assets = None
dir = os.listdir()
import multiprocessing
import logging
from time import sleep
class Trader:
    def __init__(self, model, multi_scaler, encoder, trading_client=None, history_client=None):
        self.model = model
        self.apikey='PKG5MOE0VTWFQK9PBHPR'
        self.secret='6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD'
        self.trading_client = TradingClient('PKG5MOE0VTWFQK9PBHPR', '6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD', paper=True) if trading_client is None else trading_client
        self.client = StockHistoricalDataClient('PKG5MOE0VTWFQK9PBHPR', '6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD') if history_client is None else history_client
        self.options_client=OptionHistoricalDataClient('PKG5MOE0VTWFQK9PBHPR', '6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD')
        self.multi_scaler = multi_scaler
        self.encoder = encoder
        self.assignments = []
        if "assets.pkl" not in dir:
            self.assets = {i.symbol:i for i in self.trading_client.get_all_assets()}
            with open("assets.pkl", "wb") as f:
                pkl.dump(self.assets, f)
        else:
            with open("assets.pkl", "rb") as f:
                self.assets = pkl.load(f)
            
    def get_bars(self,symbol_or_symbols,time):
        start_time=time - timedelta(days=3)
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol_or_symbols,
            timeframe=TimeFrame(15, TimeFrameUnit('Min')),
            start=start_time,
            end=time,
            adjustment=Adjustment.ALL,
            feed='sip'
        )
    
        return self.client.get_stock_bars(request_params).df
    @staticmethod
    def preprocess(bars,stock,start,end,multi_scaler):
        df=bars.loc[stock].between_time('13:30','20:00')
        ldex=pd.date_range(start=start,end=end ,freq='15min').to_series().between_time('13:30', '20:00').index
        ldex[pd.to_datetime(ldex.date).isin(pd.to_datetime(df.index.date).unique())]

        df=df.drop_duplicates()
        df.loc[:,['open','high','low','close']]=df.loc[:,['open','high','low','close']].diff().dropna().rolling(3,center=False).mean()
        df=df.drop(['vwap','trade_count'],axis=1)
        df=df.reindex(ldex,method='ffill')
        df=df.dropna().tail(13)
        arr=multi_scaler.transform(df).values
        return arr
    
    def preprocess_bars(self,bars,symbol_or_symbols):
        arrs={}
        start=bars.index.get_level_values(1).min()
        end=bars.index.get_level_values(1).max()
        for stock in symbol_or_symbols:
            arr=self.preprocess(bars,stock,start,end,self.multi_scaler)
            arrs[stock]=arr
        return np.vstack(list(arrs.values())).reshape(-1,13,5)
    

    def preprocess_bars_v2(self, bars, symbol_or_symbols):
            start = bars.index.get_level_values(1).min()
            end = bars.index.get_level_values(1).max()
            with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
                tasks = [pool.apply_async(self.preprocess, (bars, stock, start, end,self.multi_scaler)) for stock in symbol_or_symbols]  
                arrs = {stock: task.get() for stock, task in zip(symbol_or_symbols, tasks)}
            return np.vstack(list(arrs.values())).reshape(-1, 13, 5)



    def predict(self,x):
        np.random.seed(1)
        tf.random.set_seed(1)
        predictions=self.model.predict(x,batch_size=1000)
        predictions=self.encoder.inverse_transform(predictions).flatten()
        print(predictions.flatten())
        #percent long
        print(f"{sum(predictions == 1)/len(predictions)}% long")
        return predictions
    @staticmethod
    def target_rebalance(symbol,side,price,positions,asset,flip = True,longshort = True,close_to_reverse = True):
        
        shortable = asset.shortable
        #shortable = True
        if symbol in positions:
            position = positions[symbol]
        else: 
            position = None
        if flip:
            side = PositionSide.LONG if side == 0 else PositionSide.SHORT
        else:
            side = PositionSide.LONG if side == 1 else PositionSide.SHORT
        if position:
            #long==long
            if position.side == side:
                return []
            #long==short
            else:
               # print(f'''{symbol}
               #       {position.side}--->{side} 
               #       qty: {position.qty} price:{price} 
               #       shortable: {shortable}''')
               # #sell to short
                
                trade = MarketOrderRequest(
                    symbol = symbol,
                    qty = abs(int(position.qty)),
                    time_in_force=TimeInForce.DAY,
                    side = OrderSide.BUY if side == PositionSide.LONG else OrderSide.SELL,
                    stop_loss=StopLossRequest(
                        #stop at .5% loss
                        stop_price=price*.9975 if side == PositionSide.LONG else price*1.0025
                    ),
                    take_profit=TakeProfitRequest(
                        #take profit at 2%
                        limit_price=price*1.2 if side == PositionSide.LONG else price*.8
                    )
                    
                )
                
                if close_to_reverse and shortable:
                    trades=[position.asset_id,trade]
                    if abs(float(position.market_value))>3000 and abs(int(position.qty))>1:
                        trades[1].qty = abs(int(3500/price))
                    return trades
                if shortable and not close_to_reverse:
                    return (trade, trade)
                if not shortable and side == PositionSide.LONG:
                    return (trade,)
                if not shortable and side == PositionSide.SHORT:
                    return (position.asset_id,)             
        else:
            #open side
            qty = int(3500/price)
            trade = MarketOrderRequest(
                symbol = symbol,
                qty = abs(int(qty)),
                time_in_force=TimeInForce.DAY,
                side = OrderSide.BUY if side == PositionSide.LONG else OrderSide.SELL,
                stop_loss=StopLossRequest(
                    #stop at .5% loss
                    stop_price=price*.995 if side == PositionSide.LONG else price*1.005
                ),
                take_profit=TakeProfitRequest(
                    #take profit at 2%
                    limit_price=price*1.2 if side == PositionSide.LONG else price*.8
                )
            )
            
            if (side == PositionSide.LONG) or ((side == PositionSide.SHORT) and (shortable == True)):
                return (trade,)
            else:
                return (None,)        
            
            
    def generate_orders(self,trades,prices,positions,flip = None,longshort = True):
        assets=self.assets.copy()
        with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
            tasks = [pool.apply_async(self.target_rebalance, (symbol, trades[symbol], prices[symbol], positions, assets[symbol],flip, longshort)) for symbol in trades]
            orders=[task.get() for task in tasks]

        return orders
    @staticmethod
    def submit_and_monitor_orders(orders, other=None):
        trading_client = TradingClient('PKG5MOE0VTWFQK9PBHPR', '6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD', paper=True)
        trying = True
        max_retries = 5  # Define maximum number of retries for each order

        while trying and orders:
            order = orders[0]
            if not order:
                trying = False
                continue
            
            placed = False
            tries = 0  # Reset retries count for each new order
            while not placed and tries < max_retries:
                tries += 1
                try:
                    if isinstance(order, UUID):
                        order = trading_client.close_position(order)
                        placed = True
                    elif isinstance(order, MarketOrderRequest):
                        dt = datetime.now(timezone.utc)
                        if dt.hour == 20 and dt.minute > 0:
                            order.extended_hours = True
                            order.time_in_force = TimeInForce.IOC
                            if order.side == OrderSide.BUY:
                                order.position_intent = PositionIntent.BUY_TO_CLOSE
                            else:
                                order.position_intent = PositionIntent.SELL_TO_CLOSE    
                        elif dt.hour < 13 and dt.minute < 28:
                            order.extended_hours = True
                            order.time_in_force = TimeInForce.OPG
                            if order.side == OrderSide.BUY:
                                order.position_intent = PositionIntent.BUY_TO_OPEN
                            else:
                                order.position_intent = PositionIntent.SELL_TO_OPEN
                            
                        order = trading_client.submit_order(order)
                        placed = True
                except Exception as e:
                    print(f"Attempt {tries}: {e}, Order: {order}")
                    if hasattr(e, "message"):
                        if 'shortable' in str(e):
                            print(f"Shortable error: {order.symbol}")
                            orders.pop(0)
                            continue
            
            if placed:
                id = order.id
                monitoring_tries = 0
                while monitoring_tries < 10:
                    try:
                        order = trading_client.get_order_by_id(id)
                        if order.status == OrderStatus.FILLED:
                            orders.pop(0)
                            break
                        sleep(1)
                    except Exception as e:
                        print(f"Monitoring error: {e}")
                        monitoring_tries += 1
                    if monitoring_tries >= 10:
                        if placed:
                            trading_client.cancel_order_by_id(id)
                        
                        print(f"Order {id} monitoring failed and cancelled after retries.")
            
            if tries >= max_retries:
                print(f"Order failed after {max_retries} attempts, removing from queue.")
                orders.pop(0)  # Remove the order from the list after max retries

        if not orders:
            trying = False 


                
    def execute(self,orders):
        if self.trading_client.get_clock().is_open:
            with multiprocessing.Pool(multiprocessing.cpu_count()) as poolE:
            #with multiprocessing.Pool(2) as poolE:
    
                tasks = [poolE.apply_async(self.submit_and_monitor_orders, args=(list(order),)) for order in orders]
                [task.get() for task in tasks]
        else:
            print("Market closed")
            
            

