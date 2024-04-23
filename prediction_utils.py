from alpaca.data.historical import *
from alpaca.data.requests import *
from alpaca.data.timeframe import *
from alpaca.data.enums import *
from alpaca.trading.client import *
from alpaca.trading.requests import * 
from alpaca.trading.enums import *
trading_client = TradingClient('PKG5MOE0VTWFQK9PBHPR', '6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD', paper=True)
client = StockHistoricalDataClient('PKG5MOE0VTWFQK9PBHPR', '6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD')

import numpy as np
import pandas as pd
async def get_bars(symbol_or_symbols,time):
    start_time=time - timedelta(days=4)
    request_params = StockBarsRequest(
        symbol_or_symbols=symbol_or_symbols,
        timeframe=TimeFrame(15, TimeFrameUnit('Min')),
        start=start_time,
        end=time,
        adjustment=Adjustment.ALL,
        feed='sip'
    )
    return client.get_stock_bars(request_params).df


async def preprocess_bars(multi_scaler,bars,symbol_or_symbols):
    arrs={}
    for stock in symbol_or_symbols:
        df=bars.loc[stock].between_time('13:30','20:00')
        print(df.index.max())
        df=df.loc[:,['open','high','low','close']].diff().rolling(3).mean().dropna().tail(26)
        arr=multi_scaler.transform(df).values
        arrs[stock]=arr
    return np.vstack(list(arrs.values())).reshape(-1,26,4)

async def predict(model,x):
    return model.predict(x,batch_size=1000).argmax(1)


