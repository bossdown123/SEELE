from datetime import *

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import *
from alpaca.data.timeframe import TimeFrame,TimeFrameUnit
from alpaca.data.enums import Adjustment
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import OrderRequest,MarketOrderRequest 
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType,PositionSide,OrderStatus
from supabase import create_client
from supabase.client import Client
url: str = "https://yygimsahwbrurnvyfmul.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl5Z2ltc2Fod2JydXJudnlmbXVsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxMDY4ODI2OCwiZXhwIjoyMDI2MjY0MjY4fQ.A0EiE0m1Ze_bYOz-8LBymdBwHvQwMr3n0wO6ajvJtzw"
supabase: Client = create_client(url, key)

trading_client = TradingClient('PKODZGQ3BIWGQJ6A3HJ4', 'WRCojP9T9ZnV2KZeru9GRbXb41zu7bj2GjRC17XJ', paper=True)
client = StockHistoricalDataClient('PKODZGQ3BIWGQJ6A3HJ4', 'WRCojP9T9ZnV2KZeru9GRbXb41zu7bj2GjRC17XJ')

import asyncio
import websockets
import json
async def connect_websocket():
    uri = "wss://stream.data.alpaca.markets/v2/sip"
    async with websockets.connect(uri) as websocket:
        # Authentication
        await authenticate(websocket)

        # Subscribe to channels
        await subscribe_to_channels(websocket, ["AAPL", "TSLA","MSFT","AMZN","NVDA"])

        # Receive messages
        await receive_messages(websocket)

async def authenticate(websocket):
    auth_data = {
        "action": "auth",
        "key": "PKODZGQ3BIWGQJ6A3HJ4",
        "secret": "WRCojP9T9ZnV2KZeru9GRbXb41zu7bj2GjRC17XJ"
    }
    await websocket.send(json.dumps(auth_data))
    # Wait for authentication response
    response = await websocket.recv()
    print("Authentication Response:", response)

async def subscribe_to_channels(websocket, symbols):
    subscribe_message = {
        "action": "subscribe",
        "bars": symbols
    }
    await websocket.send(json.dumps(subscribe_message))

async def receive_messages(websocket):
    try:
        while True:
            message = await websocket.recv()
            message = json.loads(message)
            print("Received Message:", message)
            if 't' in message[0]:
                dt = datetime.strptime(message[0]['t'], '%Y-%m-%dT%H:%M:%SZ')
                stock=message[0]['S']
                if dt.minute % 5 == 0:
                    start_time=dt-timedelta(days=4)
                    request_params=StockBarsRequest(
                        symbol_or_symbols=message[0]['S'],
                        start=start_time,
                        end=dt,
                        timeframe=TimeFrame(15,TimeFrameUnit('Min')),
                        adjustment=Adjustment.ALL,
                        feed='sip'
                    )
                    barset=client.get_stock_bars(request_params).df.loc[stock]
                    barset.columns=['o','h','l','c','v','n','vw']
                    barset.index.name='t'
                    barset['n'] = barset['n'].astype(int)
                    barset['v'] = barset['v'].astype(int)
                    barset['S'] =stock
                    barset.reset_index(inplace=True)
                    barset['t']=barset['t'].apply(lambda x:x.strftime('%Y-%m-%dT%H:%M:%SZ'))
                    supabase.table('DataStream').upsert(barset.to_dict(orient='records')).execute()
                    
    except websockets.exceptions.ConnectionClosed:
        await websocket.close()
        print("Connection closed")

if __name__ == "__main__":
    asyncio.run(connect_websocket())
