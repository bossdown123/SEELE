from alpaca.data.historical import *
from alpaca.data.requests import *
from alpaca.data.timeframe import *
from alpaca.data.enums import *
from alpaca.trading.client import *
from alpaca.trading.requests import * 
from alpaca.trading.enums import *
trading_client = TradingClient('PKODZGQ3BIWGQJ6A3HJ4', 'WRCojP9T9ZnV2KZeru9GRbXb41zu7bj2GjRC17XJ', paper=True)
client = StockHistoricalDataClient('PKODZGQ3BIWGQJ6A3HJ4', 'WRCojP9T9ZnV2KZeru9GRbXb41zu7bj2GjRC17XJ')
import numpy as np
import pandas as pd
async def get_bars(symbol_or_symbols,time):
    start_time=time - timedelta(days=3)
    request_params = StockBarsRequest(
        symbol_or_symbols=symbol_or_symbols,
        timeframe=TimeFrame(30, TimeFrameUnit('Min')),
        start=start_time,
        end=time,
        adjustment=Adjustment.ALL,
        feed='sip'
    )
    return client.get_stock_bars(request_params).df


async def preprocess_bars(multi_scaler,bars):
    arrs=[]
    for stock in bars.index.get_level_values(0).unique():
        df=bars.loc[stock]
        df=df.loc[:,['open','high','low','close']].diff().rolling(3).mean().dropna().tail(26)
        arr=multi_scaler.transform(df).values
        arrs.append(arr)
    return np.hstack(arrs)#.reshape(-1,26,4)

async def predict(model,x):
    return model.predict(x,batch_size=1000).argmax(1)


