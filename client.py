import json
import random
import pickle as pkl
from datetime import *
import os
import sys

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress most warnings
import tensorflow as tf

import asyncio
from ably import AblyRealtime

sys_id = str(random.randint(0, 10000000000))

from prediction_utils import *
from order_logic import *
global assignments
assignments = []

with open("multi_scaler.pickle", "rb") as f:
    multi_scaler = pkl.load(f)
model = load_model("model.keras")

async def publish_heartbeat(channel, sys_id=sys_id):
    while True:
        await asyncio.sleep(5)
        await channel.publish(
            name="alive",
            data=json.dumps({sys_id: {"timestamp": datetime.now(timezone.utc).timestamp()}}),)


async def assignment_listener(message, sys_id=sys_id):
    global assignments
    data = json.loads(message.data)
    assignments = data[sys_id]
    print("Received assignments:", assignments)

async def trade_exec(model=model, multi_scaler=multi_scaler):
    print("Executing trades")
    if assignments:
        bars = await get_bars(assignments, datetime.now(timezone.utc))
        arr = await preprocess_bars(multi_scaler, bars)
        prediction = await predict(model, arr)  # targets=dict(zip(assignments,prediction))
        for stock, target in zip(assignments, prediction):
            execute(target_rebalance(PositionSide.LONG if target == 1 else PositionSide.SHORT, stock))
        return dict(zip(assignments, prediction))

# await trade_alert.publish(name='trades', data=json.dumps({sys_id:targets}))
async def command_listener(message, sys_id=sys_id):
    print("Received command:", message.data)
    data = json.loads(message.data)
    if data["scope"] == "ALL" and data["command"] == "trade":
        trades = await trade_exec()
        await trade_alert.publish(name="trades", data=json.dumps({sys_id: str(trades)}))

async def trade_task():
    while True:
        await asyncio.sleep(1)
        dt = datetime.now(timezone.utc)
        if assignments and dt.minute % 15 == 0 and dt.second < 2:
            trades = await trade_exec()
            print("Trades:", trades)
            await trade_alert.publish(name="trades", data=json.dumps({sys_id: str(trades)}))


async def main():
    # Create a client using an Abl1y API key

    client = AblyRealtime("rFzlEA.aAHNZw:3ybEePEcrI20nqAWmSyvQdjANv2XWGiOMfW05c4T_kw")

    # Subscribe to connection state changes
    client.connection.on("connected", lambda state_change: print("Connected to Ably"))
    client.connection.on("failed", lambda state_change: print("Connection to Ably failed"))
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

    asyncio.create_task(publish_heartbeat(heartbeat, sys_id))

    asyncio.create_task(trade_task())

    while True:
        await asyncio.sleep(1)

asyncio.run(main())
