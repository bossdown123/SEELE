from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import *
from alpaca.data.timeframe import TimeFrame,TimeFrameUnit
from alpaca.data.enums import Adjustment
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import OrderRequest,MarketOrderRequest 
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType,PositionSide,OrderStatus
trading_client = TradingClient('PKVL24J3O7MEAJKC5WIO', 'eKXDYtCs1HlGOfu6z3mL2GrpNpaL5oreVMzcfmwH', paper=True)
client = StockHistoricalDataClient('PKVL24J3O7MEAJKC5WIO', 'eKXDYtCs1HlGOfu6z3mL2GrpNpaL5oreVMzcfmwH')

import asyncio
import json
from ably import realtime
import random
sys_id = str(random.randint(0, 10000000000))

async def rebalance():


async def main():
    # Create a client using an Ably
    client = realtime.AblyRealtime('rFzlEA.aAHNZw:3ybEePEcrI20nqAWmSyvQdjANv2XWGiOMfW05c4T_kw')
    client.realtime_request_timeout = 2000000000
    # Subscribe to connection state changes
    client.connection.on('connected', lambda state_change: print('Connected to Ably'))
    client.connection.on('failed', lambda state_change: print('Connection to Ably failed'))
    
    command = client.channels.get('test')