import aiohttp
import asyncio
import random
import time
async def send_order_async(session):
    data = {
        "symbol": "AAPL",
        "qty": random.randint(1, 10),
        "side": random.choice(["buy", "sell"]),
    }
    async with session.post("http://127.0.0.1:8000/api/orders/", json=data) as response:
        status = response.status
async def main():
    async with aiohttp.ClientSession() as session:
        while True:  # Loop indefinitely
            tasks = [send_order_async(session) for _ in range(500)]  # Send 10 requests concurrently
            await asyncio.gather(*tasks)

# Run the asynchronous main function
asyncio.run(main())