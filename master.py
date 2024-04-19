
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

        for id in to_remove:
            del active_members[id]


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
    new_active_members = {}

    assignments={}
    #asyncio.create_task(handle_dead())

    while True:
        await asyncio.sleep(1)

        stocks=['MSFT','AAPL','NVDA','GOOGL','AMZN','META','BRK-A','LLY','AVGO','V','JPM','TSLA','WMT','XOM','UNH','MA','PG','JNJ','HD','ORCL','MRK','COST','ABBV','CVX','BAC','CRM','NFLX','KO','AMD','PEP','ADBE','TMO','DIS','WFC','MCD','CSCO','TMUS','ABT','QCOM','CAT','DHR','INTU','GE','IBM','VZ','AMAT','AXP','CMCSA','NOW','COP','INTC','TXN','UBER','BX','MS','PFE','NKE','AMGN','PM','UNP','RTX','ISRG','SPGI','GS','LOW','NEE','MU','SCHW','SYK','HON','PGR','UPS','LRCX','ELV','BKNG','T','BLK','C','DE','LMT','TJX','BA','ABNB','VRTX','BSX','ADP','PLD','CI','SBUX','REGN','MMC','BMY','ADI','PANW','MDLZ','KLAC','SCCO','FI','CVS','DELL','KKR','GILD','WM','HCA','ANET','SNPS','AMT','CMG','CDNS','SHW','GD','EOG','SO','TGT','CME','ITW','ICE','MPC','DUK','MO','SLB','FCX','CL','CRWD','ZTS','EQIX','PH','MCK','MAR','MCO','TDG','CTAS','WDAY','PSX','BDX','APH','NOC','CSX','PYPL','FDX','ORLY','EMR','ECL','PXD','USB','EPD','APO','PCAR','RSG','PNC','OXY','CEG','MRVL','MSI','MNST','ROP','SMCI','VLO','NSC','DASH','EW','COF','CPRT','COIN','DXCM','ET','WELL','APD','AZO','HLT','MMM','AJG','MET','SNOW','EL','AIG','FTNT','GM','CARR','DHI','COR','TFC','CTA-PA','TRV','STZ','F','GWW','NUE','HES','AFL','PSA','IBKR','ADSK','MCHP','SPG','WMB','ODFL','OKE','SQ','PLTR']
        stocks=[stock.replace('-','.') for stock in stocks]
        n=len(active_members)
        if active_members != new_active_members:
            new_active_members=active_members
            if n==0:
                print('No active members')
                continue
            print(str(len(active_members)).replace(",",'\n'))
            print("--------------------")
        if n==0:
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
