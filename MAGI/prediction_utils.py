from alpaca.data.historical import *
from alpaca.data.requests import *
from alpaca.data.timeframe import *
from alpaca.data.enums import *
from alpaca.trading.client import *
from alpaca.trading.requests import * 
from alpaca.trading.enums import *
trading_client = TradingClient(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'), paper=True)
client = StockHistoricalDataClient(os.getenv('APCA_API_KEY_ID'), os.getenv('APCA_API_SECRET_KEY'))
import tensorflow as tf
import numpy as np
import pandas as pd
import os
def get_bars(symbol_or_symbols,time):
    start_time=time - timedelta(days=3)
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
    start=bars.index.get_level_values(1).min()
    end=bars.index.get_level_values(1).max()
    for stock in symbol_or_symbols:
        df=bars.loc[stock].between_time('13:30','20:00')
        ldex=pd.date_range(start=start,end=end ,freq='15min').to_series().between_time('13:30', '20:00').index
        ldex[pd.to_datetime(ldex.date).isin(pd.to_datetime(df.index.date).unique())]

        df=df.drop_duplicates()
        df.loc[:,['open','high','low','close']]=df.loc[:,['open','high','low','close']].diff().dropna().rolling(3,center=False).mean()
        df=df.drop(['vwap','trade_count'],axis=1)
        df=df.reindex(ldex,method='ffill')
        df=df.dropna().tail(13)
        arr=multi_scaler.transform(df).values
        arrs[stock]=arr
    return np.vstack(list(arrs.values())).reshape(-1,13,5)

async def predict(model,x,encoder):
    np.random.seed(1)
    tf.random.set_seed(1)
    predictions=model.predict(x,batch_size=1000)
    predictions=encoder.inverse_transform(predictions).flatten()
    print(predictions.flatten())
    #percent long
    print(f"{sum(predictions==1)/len(predictions)}% long")
    return predictions



