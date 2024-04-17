
from realtime.connection import Socket
from datetime import *
SUPABASE_ID = "yygimsahwbrurnvyfmul"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl5Z2ltc2Fod2JydXJudnlmbXVsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxMDY4ODI2OCwiZXhwIjoyMDI2MjY0MjY4fQ.A0EiE0m1Ze_bYOz-8LBymdBwHvQwMr3n0wO6ajvJtzw"
from supabase import create_client
from supabase import Client
from utils import*
url: str = 'https://yygimsahwbrurnvyfmul.supabase.co'
key: str = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl5Z2ltc2Fod2JydXJudnlmbXVsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxMDY4ODI2OCwiZXhwIjoyMDI2MjY0MjY4fQ.A0EiE0m1Ze_bYOz-8LBymdBwHvQwMr3n0wO6ajvJtzw'
supabase: Client = create_client(url, key)
supabase.options.postgrest_client_timeout = 100000

from trade_logic import *
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import *
from alpaca.data.timeframe import TimeFrame,TimeFrameUnit
from alpaca.data.enums import Adjustment
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import OrderRequest,MarketOrderRequest 
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType,PositionSide,OrderStatus
trading_client = TradingClient('PKODZGQ3BIWGQJ6A3HJ4', 'WRCojP9T9ZnV2KZeru9GRbXb41zu7bj2GjRC17XJ', paper=True)
client = StockHistoricalDataClient('PKODZGQ3BIWGQJ6A3HJ4', 'WRCojP9T9ZnV2KZeru9GRbXb41zu7bj2GjRC17XJ')


import tensorflow as tf
import numpy as np
from tensorflow import keras
from keras.models import *
import asyncio
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
from utils import MultiScalerOld
import pickle as pkl

with open('multi_scaler.pickle','rb') as f:
    multi_scaler=pkl.load(f)
    
model=load_model('model.keras')

stocks=["AAPL", "TSLA","MSFT","AMZN","NVDA"]


from trade_logic import *
def preprocess_bars(bars):
    bars=bars.loc[:,['open','high','low','close']]
    bars=bars.diff().rolling(3).mean().dropna()
    return multi_scaler.transform(bars.tail(26)).values.reshape(1,26,4)
def predict(x):
    return float(model.predict(x).argmax(1))

def callback1(payload):
    print("Callback 1: ", payload,type(payload))
    if 'record' in payload:
        dt = datetime.fromisoformat(payload['record']['t'])
        start_time = dt - timedelta(days=4)
        end_time = dt
        res=supabase.table('DataStream') \
                .select('S', 'o', 'h', 'l', 'c', 'v', 't') \
                .eq('S', payload['record']['S']) \
                .gte('t', start_time.isoformat()) \
                .lte('t', end_time.isoformat()) \
                .order('t', desc=False) \
                .limit(10000) \
                .execute()
        df=pd.DataFrame(res.model_dump()['data']).rename(columns={'S':'symbol','o':'open','h':'high','l':'low','c':'close','v':'volume','t':'timestamp'}).assign(timestamp=lambda x: pd.to_datetime(x.timestamp)).set_index(['symbol','timestamp']).sort_index()
        
        execute(target_rebalance(PositionSide.LONG if predict(preprocess_bars(df.loc[payload['record']['S']]))==1 else PositionSide.SHORT,payload['record']['S']))
if __name__ == "__main__":
    URL = f"wss://{SUPABASE_ID}.supabase.co/realtime/v1/websocket?apikey={API_KEY}&vsn=1.0.0"
    s = Socket(URL)
    s.connect()
    #for i in stocks:
        #callback1({'columns': [{'name': 'S', 'type': 'varchar'}, {'name': 'o', 'type': 'float4'}, {'name': 'h', 'type': 'float4'}, {'name': 'l', 'type': 'float4'}, {'name': 'c', 'type': 'float4'}, {'name': 'v', 'type': 'int4'}, {'name': 't', 'type': 'timestamptz'}, {'name': 'n', 'type': 'int4'}, {'name': 'vw', 'type': 'float4'}, {'name': 'T', 'type': 'WsType'}], 'commit_timestamp': '2024-04-17T13:46:01.011Z', 'errors': None, 'record': {'S': i, 'T': None, 'c': 170.335, 'h': 170.353, 'l': 170.045, 'n': 1835, 'o': 170.21, 't': '2024-04-17T14:15:00+00:00', 'v': 156743, 'vw': 170.181}, 'schema': 'public', 'table': 'DataStream', 'type': 'INSERT'} )
    channel_1 = s.set_channel("realtime:public:DataStream")
    channel_1.join().on("INSERT", callback1)
    s.listen()