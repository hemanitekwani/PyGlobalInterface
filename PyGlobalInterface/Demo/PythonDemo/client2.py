from PythonClient import PyGlobalInterface_Client
from asyncio import sleep
import uuid


client = PyGlobalInterface_Client(f"{uuid.uuid4()}")

if client.client_register():
    print("sucessful registration")


tasks = []
for i in range(1000):
    task = client.loop.create_task(client.call_function("program1@run_print",data={"val":f"hello from {client.client_name}"}))
    client.loop.run_until_complete(task)




client.loop.close()


