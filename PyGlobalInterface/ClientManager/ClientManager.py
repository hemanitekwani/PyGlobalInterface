from PyGlobalInterface.ClientManager.Client import Client
from PyGlobalInterface.log import configure_logger
from time import time
from asyncio import sleep
from typing import List, Tuple, Dict
import asyncio
import gc
from PyGlobalInterface.ClientManager.Client.ResReq import EventsClientManger
from asyncio.queues import Queue

logger = configure_logger(__name__)
class ClientManager:
    def __init__(self) -> None:
       self.unregister_client_temp:List[Tuple[Client,float]] = []
       self.process_queue:Queue = Queue()
       self.telemetry_queue:Queue = Queue()
       self.verify_client:Dict[str:Client] = dict()
       self.__allow_time_secs = 3

    async def add_new_client(self,rd:asyncio.StreamReader,wr:asyncio.StreamWriter):
        client = Client(rd,wr,self.telemetry_queue,self.process_queue)
        logger.info("NEW CLIENT IS ADDED, WAITING FOR VERIFY")
        client.start_client()
        self.unregister_client_temp.append((client,time()))

    async def __process_request(self):
        while True:
            packet:dict = await self.process_queue.get()
            event:str  = packet.get("event")
            if event == EventsClientManger.REQ_MAKE_CLIENT_VERIFY:
                client_id = packet.get("client_id")
                client:Client = packet.get("ref")
                if client_id not in self.verify_client.keys():
                    self.verify_client[client_id] = client
                    client.verify_client(client_id=client_id,succesful=True)
                client.verify_client(client_id=client_id,succesful=False)
                del client_id
                del client
            elif event == EventsClientManger.REQ_MAKE_FUNCTION_CALL:
                caller = packet.get("caller")
                callee = packet.get("callee")
                function_name= packet.get("function_name")
                task_id = packet.get("task_id")
                client:Client = packet.get('ref')

                # client.



    async def __clean_up_process(self):
        while True:
            await sleep(0.4)
            remove_list = []
            for i,value in enumerate(self.unregister_client_temp):
                client,_time = value
                if self.__allow_time_secs < time()-_time and not client.verify:
                    remove_list.append(i)
            for idx in remove_list[::-1]:
                client,_time = self.unregister_client_temp.pop(idx)
                logger.info(f"POPING THE CLIENT REGISTER AT TIME: {_time}")
            gc()
    def start(self):
        loop = asyncio.get_running_loop()
        loop.create_task(self.__process_request())
        loop.create_task(self.__clean_up_process())