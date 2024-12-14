from alpaca.data.historical import *
from alpaca.data.requests import *
from alpaca.data.timeframe import *
from alpaca.data.enums import *
from alpaca.trading.client import *
from alpaca.trading.requests import * 
from alpaca.trading.enums import *
from alpaca.data.live.stock import StockDataStream
from datetime import *

import asyncio
import os

async def handle_bars(message):
    print(message)

   
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')

stock_stream = StockDataStream(API_KEY, SECRET_KEY, feed=DataFeed.SIP)
    
stock_stream.subscribe_bars(handler=handle_bars, symbols=['AAPL', 'MSFT'])
    
stock_stream.run()