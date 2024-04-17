import asyncio
from datetime import *
from prediction_utils import *
import pickle as pkl
import tensorflow as tf
from tensorflow.keras.models import load_model

with open('multi_scaler.pickle','rb') as f:
    multi_scaler=pkl.load(f)
    
model=load_model('model.keras')

stocks=["AAPL", "TSLA","MSFT","AMZN","NVDA"]

from order_logic import *

async def main():

    bars=await get_bars(["AAPL", "TSLA","MSFT","AMZN","NVDA"],datetime.now(timezone.utc))
    arr=await preprocess_bars(multi_scaler,bars)
    prediction=await predict(model,arr)
    targets=dict(zip(stocks,prediction))
    print(targets)
    for stock,target in zip(stocks,prediction):
        target_rebalance(PositionSide.LONG if target==1 else PositionSide.SHORT,stock)

asyncio.run(main())