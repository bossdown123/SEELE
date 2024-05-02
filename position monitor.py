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

async def handle_bars(message):
    print(message)

   
stock_stream = StockDataStream('PKG5MOE0VTWFQK9PBHPR', '6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD', feed=DataFeed.SIP)
    
stock_stream.subscribe_bars(handler=handle_bars, symbols=['AAPL', 'MSFT'])
    
stock_stream.run()