import json
import random
import pickle as pkl
from datetime import *
import os
import sys
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress most warnings
import numpy as np
from tensorflow.keras.models import load_model
import tensorflow as tf

import asyncio
from ably import AblyRealtime

sys_id = str(random.randint(0, 10000000000))

from prediction_utils import *
from order_logic import *
global assignments
assignments = []
from concurrent.futures import ThreadPoolExecutor
def rd(dt):
    # Extract minutes and find how many minutes to subtract to round down to the nearest 15
    minute = dt.minute
    minute_to_subtract = minute % 15
    
    # Subtract the extra minutes from the datetime object
    rounded_dt = dt - timedelta(minutes=minute_to_subtract)
    
    return rounded_dt

with open("multi_scaler.pickle", "rb") as f:
    multi_scaler = pkl.load(f)
model = load_model("model.keras")

async def publish_heartbeat(channel, sys_id=sys_id):
    while True:
        await asyncio.sleep(2)
        await channel.publish(
            name="alive",
            data=json.dumps({sys_id: {"timestamp": datetime.now(timezone.utc).timestamp()}}),)
        print("Published heartbeat")
            
async def assignment_listener(message, sys_id=sys_id):
    global assignments
    data = json.loads(message.data)
    assignments = data[sys_id]
    print("Received assignments:", len(assignments))
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor

async def trade_exec(model=model, multi_scaler=multi_scaler):
    print("Executing trades")
    if assignments:
        print("Assignments:", len(assignments))
        dt=datetime.now(timezone.utc)
        if dt.hour < 13 or dt.hour > 20:
            print("Not trading hours")
            return
        bars=await get_bars(assignments,rd(dt))
        arr=await preprocess_bars(multi_scaler,bars,assignments)
        prediction=await predict(model,arr)
        targets=dict(zip(assignments,prediction))
        try:
            with ProcessPoolExecutor(max_workers=16) as executor:
                tasks = [executor.submit(target_rebalance, PositionSide.LONG if pred == 0 else PositionSide.SHORT, symbol,{i.symbol:i for i in trading_client.get_all_positions()})
                    for symbol, pred in targets.items()]
                trades = [task.result() for task in tasks]
        except Exception as e:
            print(e)
        print(targets)

        with ProcessPoolExecutor(max_workers=16) as executor:
            tasks = [executor.submit(execute, trade) for trade in trades]
            orders = [task.result() for task in tasks]
        return targets
    else:
        print ("No assignments")
# await trade_alert.publish(name='trades', data=json.dumps({sys_id:targets}))
async def command_listener(message, sys_id=sys_id):
    print("Received command:", message.data)
    data = json.loads(message.data)
    if data["scope"] == "ALL" and data["command"] == "trade":
        trades = await trade_exec()
        await trade_alert.publish(name="trades", data=json.dumps({sys_id: str(trades)}))
        print('DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE ')
async def trade_task():
    while True:
        await asyncio.sleep(1)
        dt = datetime.now(timezone.utc)
        if assignments and dt.minute % 15 == 0 and dt.second < 2:
            await asyncio.sleep(2)
            trades = await trade_exec()
            print("Trades:", trades)
            await trade_alert.publish(name="trades", data=json.dumps({sys_id: str(trades)}))
            print('DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE DONE ')


async def main():
    # Create a client using an Abl1y API key

    client = AblyRealtime("rFzlEA.aAHNZw:3ybEePEcrI20nqAWmSyvQdjANv2XWGiOMfW05c4T_kw")
    client.realtime_request_timeout = 2000000000
    # Subscribe to connection state changes
    client.connection.on("connected", lambda state_change: print("Connected to Ably"))
    client.connection.on("failed", lambda state_change: print("Connection to Ably failed"))
    client.connection.on("disconnected", lambda state_change: print("Disconnected from Ably"))
    # Get a realtime channel instance
    command = client.channels.get("command")
    heartbeat = client.channels.get("heartbeat")
    assignment = client.channels.get("assignment")
    global trade_alert
    trade_alert = client.channels.get("trades")

    # Subscribe to messages on the channel
    await assignment.subscribe(assignment_listener, sys_id)
    await command.subscribe(command_listener, sys_id)

    await command.attach()
    await heartbeat.attach()
    await assignment.attach()
    
    heartbeat_task_executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_running_loop()
    loop.run_in_executor(heartbeat_task_executor, lambda: asyncio.run(publish_heartbeat(heartbeat, sys_id)))
    #asyncio.create_task(publish_heartbeat(heartbeat, sys_id))

    #trade_task_executor = ProcessPoolExecutor(max_workers=1)
    #loop = asyncio.get_running_loop()
    #loop.run_in_executor(trade_task_executor, lambda: asyncio.run(trade_task()))
    asyncio.run(await trade_task())
    
    while True:
        await asyncio.sleep(1)

asyncio.run(main())
