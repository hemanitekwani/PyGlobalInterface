from PythonClient import PyGlobalInterface_Client
from asyncio import sleep
import time
from random import randint 

client = PyGlobalInterface_Client("program4")

if client.client_register():
    print("sucessful registration")

def run_print(data:dict):
    print(data['val'])
    task = client.loop.create_task(client.call_function("program2@run_print",data={"val":f"hello from {client.client_name}"}))
    client.loop.run_until_complete(task)
    time.sleep(randint(1,10)/10)
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
