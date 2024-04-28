import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress most warnings
stocks=['MSFT','AAPL','NVDA','GOOGL','AMZN','META','BRK-B','LLY','AVGO','V','JPM','TSLA','WMT','XOM','UNH','MA','PG','JNJ','HD','ORCL','MRK','COST','ABBV','CVX','BAC','CRM','NFLX','KO','AMD','PEP','ADBE','TMO','DIS','WFC','MCD','CSCO','TMUS','ABT','QCOM','CAT','DHR','INTU','GE','IBM','VZ','AMAT','AXP','CMCSA','NOW','COP','INTC','TXN','UBER','BX','MS','PFE','NKE','AMGN','PM','UNP','RTX','ISRG','SPGI','GS','LOW','NEE','MU','SCHW','SYK','HON','PGR','UPS','LRCX','ELV','BKNG','T','BLK','C','DE','LMT','TJX','BA','ABNB','VRTX','BSX','ADP','PLD','CI','SBUX','REGN','MMC','BMY','ADI','PANW','MDLZ','KLAC','SCCO','FI','CVS','DELL','KKR','GILD','WM','HCA','ANET','SNPS','AMT','CMG','CDNS','SHW','GD','EOG','SO','TGT','CME','ITW','ICE','MPC','DUK','MO','SLB','FCX','CL','CRWD','ZTS','EQIX','PH','MCK','MAR','MCO','TDG','CTAS','WDAY','PSX','BDX','APH','NOC','CSX','PYPL','FDX','ORLY','EMR','ECL','PXD','USB','EPD','APO','PCAR','RSG','PNC','OXY','CEG','MRVL','MSI','MNST','ROP','SMCI','VLO','NSC','DASH','EW','COF','CPRT','COIN','DXCM','ET','WELL','APD','AZO','HLT','MMM','AJG','MET','SNOW','EL','AIG','FTNT','GM','CARR','DHI','COR','TFC','TRV','STZ','F','GWW','NUE','HES','AFL','PSA','IBKR','ADSK','MCHP','SPG','WMB','ODFL','OKE','SQ','PLTR']
stocks=[stock.replace('-','.') for stock in stocks][:100]
from order_routerv2 import *
import tensorflow as tf
from keras.models import load_model
from utils import*
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor
from datetime import*
import pickle as pkl
with open('multi_scaler3.pkl','rb') as f:
    multi_scaler=pkl.load(f)
with open('encoder.pkl','rb') as f:
    encoder=pkl.load(f)
trader=Trader(model=load_model('model3.keras'),multi_scaler=multi_scaler,encoder=encoder)
start=datetime.now()


trader.trading_client.get_asset('AAPL')

end=datetime.now()-start
print(end)


