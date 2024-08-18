from PythonClient import CServer
import asyncio


def run(data):
    print(data)
    return {"hello": "world"}
async def main():
    client = CServer('0.0.0.0',9800)
    await client.connect()
    if await client.register("program10"):
        print("SUCCEFUL")
    
    await client.functionCall("program1@run","{'hello':'1'}")
    await client.run_forver()

asyncio.run(main())
