
import asyncio
from ably import AblyRest, AblyRealtime
import json

async def main():
    # Create a client using an Ably API key
    client = AblyRealtime('rFzlEA.aAHNZw:3ybEePEcrI20nqAWmSyvQdjANv2XWGiOMfW05c4T_kw')
    
    # Subscribe to connection state changes
    client.connection.on('connected', lambda state_change: print('Connected to Ably'))
    client.connection.on('failed', lambda state_change: print('Connection to Ably failed'))
    
    # Get a reference to the command channel
    command = client.channels.get('command')
    
    # Attach to the channel
    await command.attach()
    
    # Publish a command to the channel
    await command.publish('trade', json.dumps({
        "scope": "ALL",
        "command": "trade",
    }))

# Start the asyncio event loop and run the main function
asyncio.run(main())
