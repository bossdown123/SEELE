import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress most warnings
stocks=['MSFT','AAPL','NVDA','GOOGL','AMZN','META','BRK-B','LLY','AVGO','V','JPM','TSLA','WMT','XOM','UNH','MA','PG','JNJ','HD','ORCL','MRK','COST','ABBV','CVX','BAC','CRM','NFLX','KO','AMD','PEP','ADBE','TMO','DIS','WFC','MCD','CSCO','TMUS','ABT','QCOM','CAT','DHR','INTU','GE','IBM','VZ','AMAT','AXP','CMCSA','NOW','COP','INTC','TXN','UBER','BX','MS','PFE','NKE','AMGN','PM','UNP','RTX','ISRG','SPGI','GS','LOW','NEE','MU','SCHW','SYK','HON','PGR','UPS','LRCX','ELV','BKNG','T','BLK','C','DE','LMT','TJX','BA','ABNB','VRTX','BSX','ADP','PLD','CI','SBUX','REGN','MMC','BMY','ADI','PANW','MDLZ','KLAC','SCCO','FI','CVS','DELL','KKR','GILD','WM','HCA','ANET','SNPS','AMT','CMG','CDNS','SHW','GD','EOG','SO','TGT','CME','ITW','ICE','MPC','DUK','MO','SLB','FCX','CL','CRWD','ZTS','EQIX','PH','MCK','MAR','MCO','TDG','CTAS','WDAY','PSX','BDX','APH','NOC','CSX','PYPL','FDX','ORLY','EMR','ECL','PXD','USB','EPD','APO','PCAR','RSG','PNC','OXY','CEG','MRVL','MSI','MNST','ROP','SMCI','VLO','NSC','DASH','EW','COF','CPRT','COIN','DXCM','ET','WELL','APD','AZO','HLT','MMM','AJG','MET','SNOW','EL','AIG','FTNT','GM','CARR','DHI','COR','TFC','TRV','STZ','F','GWW','NUE','HES','AFL','PSA','IBKR','ADSK','MCHP','SPG','WMB','ODFL','OKE','SQ','PLTR']
stocks=[stock.replace('-','.') for stock in stocks][:100]
from order_routerv2 import *
import tensorflow as tf
from keras.models import load_model
from utils import*
import pandas as pd
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor
from datetime import*
import pickle as pkl
with open('multi_scaler3.pkl','rb') as f:
    multi_scaler=pkl.load(f)
with open('encoder.pkl','rb') as f:
    encoder=pkl.load(f)
trader=Trader(model=load_model('model3.keras'),multi_scaler=multi_scaler,encoder=encoder)
import time

import multiprocessing
client=trader.trading_client
def sl(x,client,trading_client):
    plpc=float(x.unrealized_plpc)*100
    if plpc<-.1 or plpc>.2:
        print(f'Closing position for {x.symbol} with plpc of {plpc:.2f}\n')
        order=client.close_position(x.asset_id)
        while True:
            try:
                order=client.get_order_by_id(order.id)
                if order.status==OrderStatus.FILLED:
                    sell_val=float(order.filled_qty)*float(order.filled_avg_price)
                    sell_val=abs(sell_val)
                    entry=float(x.avg_entry_price)*float(x.qty)
                    val=float(x.qty)*float(x.current_price)
                    val=abs(val)
                    # calculate slippage
                    slippage=abs(sell_val-val)
                    print(f"Symbol:{x.symbol} Slippage: {slippage:.2f} {'profit' if sell_val>entry else 'loss'}: {abs(sell_val)-abs(entry):.2f} ")
                    break
                time.sleep(1)
            except Exception as e:
                print(e)
                if Exception == KeyboardInterrupt:
                    break    
                time.sleep(1)
while True:
    try:
        if datetime.now().minute%15==0:
            continue
        positions=trader.trading_client.get_all_positions()
        
        with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
            results = [pool.apply_async(sl, (pos,client,trader.trading_client)) for pos in positions]
            [r.get() for r in results]
        time.sleep(1)
        
    except Exception as e:
        #print(e)
        if Exception == KeyboardInterrupt:
            break