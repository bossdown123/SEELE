from datetime import datetime, timedelta
from time import sleep
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import *
from alpaca.data.timeframe import TimeFrame,TimeFrameUnit
from alpaca.data.enums import Adjustment
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import OrderRequest,MarketOrderRequest 
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType,PositionSide,OrderStatus
trading_client = TradingClient('PKG5MOE0VTWFQK9PBHPR', '6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD', paper=True)
client = StockHistoricalDataClient('PKG5MOE0VTWFQK9PBHPR', '6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD')
import numpy as np
from functools import lru_cache, wraps

import numpy as np
#trading_client.cancel_orders()
from datetime import *
import time
import os
def rd(dt):
    return dt - (dt % (15 * 60))
t=datetime.fromtimestamp(1620000000+(15*60)-1)
print(rd(t))
print(t)
#for i in range(1000000):
#
#    timestamp = 1620000000 + i
#
#    print(datetime.fromtimestamp(timestamp))
#    print(datetime.fromtimestamp(rd(timestamp)))
#    time.sleep(.001)
#    os.system("clear")
