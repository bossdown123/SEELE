
import asyncio
from datetime import *
from prediction_utils import *

import pickle as pkl
import tensorflow as tf
from tensorflow.keras.models import load_model
with open('multi_scaler.pickle','rb') as f:
    multi_scaler=pkl.load(f)
    
model=load_model('model.keras')
from order_logic import *

from ably import AblyRealtime
from ably import AblyRest
import random
sys_id=str(random.randint(0, 10000000000))
import json
# Define a function to handle incoming messages
def message_listener(message):
    print("Received message:", message.data)
global assignments
assignments = []

async def assignment_listener(message,sys_id=sys_id):
    global assignments
   # print("Received assignment:", message.data)
    data = json.loads(message.data)
    assignments=data[sys_id]

async def command_listener(message,sys_id=sys_id):
    print("Received command:", message.data)
    data = json.loads(message.data)
    if data['scope']=='ALL' and data['command']=='trade':
        dt=datetime.now(timezone.utc)
        if not assignments:
            return
        bars=await get_bars(assignments,datetime.now(timezone.utc))
        arr=await preprocess_bars(multi_scaler,bars)
        prediction=await predict(model,arr)
        targets=dict(zip(assignments,prediction))
        print(targets)
        for stock,target in zip(assignments,prediction):
            execute(target_rebalance(PositionSide.LONG if target==1 else PositionSide.SHORT,stock))
        trade_alert = client.channels.get('trades')

        await trade_alert.publish(name='trades', data=json.dumps({sys_id:targets}))
        

async def publish_heartbeat(channel, sys_id=sys_id):
    while True:
        await asyncio.sleep(5)
        await channel.publish(name='alive', data=json.dumps({sys_id:{'timestamp': datetime.now(timezone.utc).timestamp()}}))

async def trade_task(sys_id=sys_id,command=None, assignments=assignments,model=model,multi_scaler=multi_scaler):
    
    while True:
        await asyncio.sleep(1)
        dt=datetime.now(timezone.utc)
        if not assignments:
            return
        if dt.minute % 15 == 0 or command == 'trade':
            bars=await get_bars(assignments,datetime.now(timezone.utc))
            arr=await preprocess_bars(multi_scaler,bars)
            prediction=await predict(model,arr)
            targets=dict(zip(assignments,prediction))
            print(targets)
            for stock,target in zip(assignments,prediction):
                target_rebalance(PositionSide.LONG if target==1 else PositionSide.SHORT,stock)
            trade_alert = client.channels.get('trades')

            await trade_alert.publish(name='trades', data=json.dumps({sys_id:targets}))
async def main():
    # Create a client using an Abl1y API key

    client = AblyRealtime('rFzlEA.aAHNZw:3ybEePEcrI20nqAWmSyvQdjANv2XWGiOMfW05c4T_kw')
    
    # Subscribe to connection state changes
    client.connection.on('connected', lambda state_change: print('Connected to Ably'))
    client.connection.on('failed', lambda state_change: print('Connection to Ably failed'))
    # Get a realtime channel instance
    channel = client.channels.get('test')
    command = client.channels.get('command')
    heartbeat = client.channels.get('heartbeat')
    assignment = client.channels.get('assignment')
    trade_alert = client.channels.get('trades')
    
    # Subscribe to messages on the channel
    await channel.subscribe(message_listener)
    await assignment.subscribe(assignment_listener,sys_id)
    await command.subscribe(command_listener,sys_id)
    #await heartbeat.subscribe(heartbeat_listener)

    # Attach to the channel
    await channel.attach()
    await command.attach()
    await heartbeat.attach()
    await assignment.attach()
    await trade_alert.attach()

    asyncio.create_task(publish_heartbeat(heartbeat, sys_id))

    asyncio.create_task(trade_task(trade_alert, sys_id))

    old_assignments = assignments
    while True:
        await asyncio.sleep(1)
        if assignments != old_assignments:
            print("Assignments received")
            print(assignments)
            old_assignments = assignments
            
asyncio.run(main())
