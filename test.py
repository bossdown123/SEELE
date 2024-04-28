import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress most warnings
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor

import asyncio
from datetime import *
from prediction_utils import *
import pickle as pkl
import tensorflow as tf
from functools import lru_cache, wraps

from alpaca.trading.client import TradingClient
import multiprocessing


trading_client = TradingClient('PKG5MOE0VTWFQK9PBHPR', '6DS4Nx9rm8VhgekPWSFwYuoFnpAUJTmfAAhmyJlD', paper=True)
def rd(dt):
    # Extract minutes, seconds, and microseconds
    minute = dt.minute
    seconds = dt.second
    microseconds = dt.microsecond
    
    # Find how many minutes to subtract to round down to the nearest 15-minute interval
    minute_to_subtract = minute % 15
    
    # Subtract the extra minutes, all seconds, and all microseconds
    rounded_dt = dt - timedelta(minutes=minute_to_subtract, seconds=seconds, microseconds=microseconds)
    
    return rounded_dt

#trading_client.cancel_orders()
from tensorflow.keras.models import load_model
with open('multi_scaler3.pkl','rb') as f:
    multi_scaler=pkl.load(f)
with open('encoder.pkl','rb') as f:
    encoder=pkl.load(f)
np.random.seed(1)
tf.random.set_seed(1)

model=load_model('model3.keras')

symbol_or_symbols=['MSFT','GOOGL','AAPL','NVDA','AMZN','META','BRK-B','LLY','AVGO','V','JPM','TSLA','WMT','XOM','UNH','MA','PG','JNJ','HD','ORCL','MRK','COST','ABBV','CVX','BAC','CRM','NFLX','KO','AMD','PEP','ADBE','TMO','DIS','WFC','MCD','CSCO','TMUS','ABT','QCOM','CAT','DHR','INTU','GE','IBM','VZ','AMAT','AXP','CMCSA','NOW','COP','INTC','TXN','UBER','BX','MS','PFE','NKE','AMGN','PM','UNP','RTX','ISRG','SPGI','GS','LOW','NEE','MU','SCHW','SYK','HON','PGR','UPS','LRCX','ELV','BKNG','T','BLK','C','DE','LMT','TJX','BA','ABNB','VRTX','BSX','ADP','PLD','CI','SBUX','REGN','MMC','BMY','ADI','PANW','MDLZ','KLAC','SCCO','FI','CVS','DELL','KKR','GILD','WM','HCA','ANET','SNPS','AMT','CMG','CDNS','SHW','GD','EOG','SO','TGT','CME','ITW','ICE','MPC','DUK','MO','SLB','FCX','CL','CRWD','ZTS','EQIX','PH','MCK','MAR','MCO','TDG','CTAS','WDAY','PSX','BDX','APH','NOC','CSX','PYPL','FDX','ORLY','EMR','ECL','PXD','USB','EPD','APO','PCAR','RSG','PNC','OXY','CEG','MRVL','MSI','MNST','ROP','SMCI','VLO','NSC','DASH','EW','COF','CPRT','COIN','DXCM','ET','WELL','APD','AZO','HLT','MMM','AJG','MET','SNOW','EL','AIG','FTNT','GM','CARR','DHI','COR','TFC','TRV','STZ','F','GWW','NUE','HES','AFL','PSA','IBKR','ADSK','MCHP','SPG','WMB','ODFL','OKE','SQ','PLTR']
symbol_or_symbols=[symbol_or_symbols.replace('-','.') for symbol_or_symbols in symbol_or_symbols][:100]
import multiprocessing

from order_logic import *
async def main():

    #bars=await get_bars()
   # print(bars)
        
    with ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        tasks = [executor.submit(get_bars,symbol_or_symbols,rd(datetime.now(timezone.utc))) for i in symbol_or_symbols]

        barsets = [task.result() for task in tasks]
        executor.shutdown(wait=True)
        
    bars=pd.concat([i.reset_index() for i in  barsets]).set_index(['symbol','timestamp'])
    arr=await preprocess_bars(multi_scaler,bars,symbol_or_symbols)
    prediction=await predict(model,arr,encoder)
    targets=dict(zip(symbol_or_symbols,prediction))
    print(targets)
    with ProcessPoolExecutor(max_workers=32) as executor:
        tasks = [executor.submit(target_rebalance, PositionSide.LONG if pred == 1 else PositionSide.SHORT, symbol,{i['symbol']:i for i in get_all_positions()})
                 for symbol, pred in targets.items()]
        trades = [task.result() for task in tasks]
        executor.shutdown(wait=True)

    for trade in trades:
        if trade:
            trade=trade[0]
            print(trade.symbol,trade.side,trade.qty,trade.time_in_force,trade.type) 

    with ProcessPoolExecutor(max_workers=2) as executor:
        tasks = [executor.submit(execute, trade) for trade in trades]
        orders = [task.result(timeout=10) for task in tasks]
        executor.shutdown(wait=True)

    print('done')
import time
asyncio.run(main())

