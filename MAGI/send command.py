
import asyncio
from ably import AblyRest, AblyRealtime
import json
import os

async def main():
    # Create a client using an Ably API key from environment variables
    ably_api_key = os.getenv('ABLY_API_KEY')
    if not ably_api_key:
        raise ValueError("No ABLY_API_KEY environment variable set")
    client = AblyRealtime(ably_api_key) 
    # Subscribe to connection state changes
    client.connection.on('connected', lambda state_change: print('Connected to Ably'))
    client.connection.on('failed', lambda state_change: print('Connection to Ably failed'))
    
    # Get a reference to the command channel
    command = client.channels.get('command')
    
    
    # Publish a command to the channel
    await command.publish('trade', json.dumps({
        "scope": "ALL",
        "command": "trade",
    }))

# Start the asyncio event loop and run the main function
asyncio.run(main())
