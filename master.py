
import asyncio
from ably import AblyRealtime
from datetime import *

import json
import pydantic
active_members = {}

lock = asyncio.Lock()


async def message_listener(message):
    return
    print("Received message:", message.data)
async def heartbeat_listener(message):
    heartbeat = json.loads(message.data)
    current_time = datetime.now(timezone.utc).timestamp()
    async with lock:
        # Update active members with received heartbeat
        active_members.update(heartbeat)
        
        # Remove dead members
        to_remove = [id for id, data in active_members.items() if current_time - data['timestamp'] > 10]
        if to_remove:
            lock.acquire()
        for id in to_remove:
            del active_members[id]
        lock.release()


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
    await heartbeat.subscribe(heartbeat_listener)

    # Attach to the channel
    await channel.attach()
    await heartbeat.attach()
    await assignment.attach()

    assignments={}
    #asyncio.create_task(handle_dead())

    while True:
        await asyncio.sleep(1)
        print(str(active_members).replace(",",'\n'))
        print("--------------------")
        stocks=['AAPL','GOOGL','AMZN','MSFT','TSLA','META','NVDA','PYPL','INTC','ADBE']
        n=len(active_members)
        if n==0:
            print('No active members')
            continue
        chunk_size = (len(stocks) + n - 1) // n  # This computes the ceiling of len(stocks) / n
        chunks = [stocks[i:i + chunk_size] for i in range(0, len(stocks), chunk_size)]
        new_assignments=dict(zip(active_members.keys(),chunks))
        #sorted_assignments = {key: new_assignments[key] for key in sorted(new_assignments)}
        if assignments != new_assignments:
            assignments=new_assignments
            print(str(assignments))
            await assignment.publish('assignment', json.dumps(assignments))
asyncio.run(main())
