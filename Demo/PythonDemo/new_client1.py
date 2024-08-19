from PythonClient import CServer
import asyncio
import time

def run(data):
    print(data)
    return {"hello": "world"}
async def main():
    client = CServer('0.0.0.0',9800)
    await client.connect()
    if await client.register("program9089"):
        print("SUCCEFUL")
    
    for i in range(10000):
        __ = time.time()
        await client.functionCall("program_iomm@run","{'hello':'1'}")
        print(time.time() - __)

asyncio.run(main())
