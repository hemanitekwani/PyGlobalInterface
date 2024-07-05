from PyGlobalInterface.ClientManager import Client
from PyGlobalInterface.log import configure_logger
from time import time
from asyncio import sleep
from typing import List, Dict
import asyncio
import gc
from asyncio.queues import Queue

logger = configure_logger(__name__)
class ClientManager:
    def __init__(self) -> None:
        self.client_stored_for_verfication:List[List[Client,float]] = []
        self.clients_mapping:Dict[str,Client] = dict()
        self.routeing_queue:Queue = Queue()
        self.clear_verification_stuff_task = None

    def add_Client(self,client:Client):
        self.client_stored_for_verfication.append((
                client,
                time()
            )
        )
    async def __clear_verification_stuff(self):
        logger.info(f"CLEANER VERIFICATION TASK IS RUNNING")
        while True:
            await sleep(1.5)
            for idx , client in enumerate(self.client_stored_for_verfication[::-1]):
                if client[0].client_id != None or time() - client[1] > 3.00:
                    self.client_stored_for_verfication.pop(idx)
            gc.collect()

    async def add_verify_client(self,client_id:str,client:Client) -> bool:
        if client_id not in self.clients_mapping.keys():
            logger.info(f"new client is verifyed with id: {client_id}")
            self.clients_mapping[client_id] = client
            return True
        return False
    
    async def call_function_from_another_program(self,sender:str ,recever:str,function_name:str,task_id:str,data:dict):
        client:Client = self.clients_mapping.get(recever)
        if client != None:
            logger.info(f"client with id {recever} is found and init functino call process")
            if client.function_present(function_name):
                logger.info(f"client with id {recever} register function {function_name}")
                return client.call_function(recever,function_name,data,task_id)
    
    async def return_function_from_another_program(self,to_client:str,data:dict,task_id:str):
        client:Client = self.clients_mapping.get(to_client)
        if client != None:
            logger.info(f"found client with {to_client} and sending requested process output task id: {task_id} and data: {data}")
            return client.return_function(data,task_id)
    
    def unregister_client(self,client_id):
        client = self.clients_mapping.get(client_id)
        client.delete()
        self.clients_mapping.pop(client_id)
    async def start(self):
        self.clear_verification_stuff_task = await asyncio.create_task(self.__clear_verification_stuff())
    
    