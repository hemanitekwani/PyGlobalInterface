from PythonClient import PyGlobalInterface_Client
from asyncio import sleep
import time 

client = PyGlobalInterface_Client("program1")

if client.client_register():
    print("sucessful registration")

def run_print(data:dict):
    print(data['val'])
    j = 1
    for i in range(10000000):
        j+=1
    return {"output":data["val"]}
if client.func_register("run_print",run_print):
    print("sucessful registration")
async def run_forever():
    while True:
        await sleep(3)
try:
    client.loop.run_until_complete(run_forever())
except Exception as e:
    print(e)
