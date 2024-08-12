from PythonClient import CServer
import asyncio


def run():
    print("jjj")
async def main():
    client = CServer('0.0.0.0',9800)
    await client.connect()
    if await client.register("program4"):
        print("SUCCEFUL")
    if await client.register_function("run",run):
        print("run function")
    return

asyncio.run(main())
