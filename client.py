
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

async def publish_heartbeat(channel, sys_id=sys_id):
    while True:
        await asyncio.sleep(5)
        await channel.publish(name='alive', data=json.dumps({sys_id:{'timestamp': datetime.now(timezone.utc).timestamp()}}))
async def trade_task(channel, sys_id=sys_id, assignments=assignments,model=model,multi_scaler=multi_scaler):
    
    while True:
        await asyncio.sleep(1)
        dt=datetime.now(timezone.utc)
        if not assignments:
            return
        if dt.minute % 15 == 0:
            bars=await get_bars(assignments,datetime.now(timezone.utc))
            arr=await preprocess_bars(multi_scaler,bars)
            prediction=await predict(model,arr)
            targets=dict(zip(assignments,prediction))
            print(targets)
            for stock,target in zip(assignments,prediction):
                target_rebalance(PositionSide.LONG if target==1 else PositionSide.SHORT,stock)
            
async def main():
    # Create a client using an Abl1y API key

    client = AblyRealtime('rFzlEA.aAHNZw:3ybEePEcrI20nqAWmSyvQdjANv2XWGiOMfW05c4T_kw')
    
    # Subscribe to connection state changes
    client.connection.on('connected', lambda state_change: print('Connected to Ably'))
    client.connection.on('failed', lambda state_change: print('Connection to Ably failed'))

    # Get a realtime channel instance
    channel = client.channels.get('test')
    heartbeat = client.channels.get('heartbeat')
    assignment = client.channels.get('assignment')
    # Subscribe to messages on the channel
    await channel.subscribe(message_listener)


    await assignment.subscribe(assignment_listener,sys_id)
    #await heartbeat.subscribe(heartbeat_listener)

    # Attach to the channel
    await channel.attach()
    await heartbeat.attach()
    await assignment.attach()

    asyncio.create_task(publish_heartbeat(heartbeat, sys_id))

    asyncio.create_task(trade_task(assignment, sys_id))

    old_assignments = assignments
    while True:
        await asyncio.sleep(1)
        if assignments != old_assignments:
            print("Assignments received")
            print(assignments)
            old_assignments = assignments
            
asyncio.run(main())
