from PyGlobalInterface.ClientManager.Client import Client
from PyGlobalInterface.log import configure_logger
from time import time
from asyncio import sleep
from typing import List, Dict
import asyncio
import gc

logger = configure_logger(__name__)
class ClientManager:
    def __init__(self) -> None:
        self.client_stored_for_verfication:List[List[Client,float]] = []
        self.clients_mapping:Dict[str,Client] = dict()
        self.clear_verification_stuff_task = None

        self.number_of_client_verify = 0
        self.number_of_client_added = 0
        self.function_call_routed = 0
        self.function_return_routed = 0

        self.function_call_to = ""
        self.function_call_from = ""

        self.function_return_to = ""
        self.function_return_from = ""

        self.policys:Dict[str,Dict[str,list]] = {}
        self.load_blance_group:Dict[str,list] = {} 
    def add_Client(self,client:Client):
        self.number_of_client_added += 1
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
            self.number_of_client_verify += 1
            logger.info(f"new client is verifyed with id: {client_id}")
            self.clients_mapping[client_id] = client
            return True
        return False
    async def call_function_from_another_program(self,to_client:str ,from_client:str,function_name:str,task_id:str,data:dict):
        client:Client = self.clients_mapping.get(from_client)
        logger.info(f" policy data {self.policys.get(from_client)}")
        logger.info(f"to_client: {to_client}, from_client: {from_client}, client: {client}")
        if self.policys.get(from_client) == None:
            return False
        
        if client != None:
            logger.info(f"to_client: {to_client}, from_client: {from_client}")
            if to_client in self.policys.get(from_client).get("allow") or "all" in self.policys.get(from_client).get("allow"):
                if function_name in self.policys.get(from_client).get(to_client) or "all" in self.policys.get(from_client).get(to_client):
                    self.function_call_to = to_client
                    self.function_call_from = from_client
                    self.function_call_routed += 1
                    logger.info(f"client with id {from_client} is found and init functino call process")
                    if client.function_present(function_name):
                        logger.info(f"client with id {from_client} register function {function_name}")
                        return client.call_function(to_client,function_name,data,task_id)
                    return False
                return False
            return False
        
    def ad_host_client_function_policy(self,host:str,client:str,function:str):
        if self.policys.get(host) == None:
            self.policys[host] = dict()
            self.policys[host]["allow"] = []
            self.policys[host]["allow"].append(client)
            self.policys[host][client] = []
            self.policys[host][client].append(function)
            return True
        else:
            if client in self.policys[host]["allow"]:
                if function not in self.policys[host][client]:
                    self.policys[host][client].append(function)
                else:
                    return False
            else:
                self.policys[host]["allow"].append(client)
                self.policys[host][client] = []
                self.policys[host][client].append(function)
        return False
    def rm_host_client_policy(self,host:str,client:str):
        self.policys[host]["allow"].remove(client)
        self.policys[host].pop(client)
    def rm_host_client_function_permit(self,host:str,client:str,function:str):
        self.policys[host][client].remove(function)
    
    async def return_function_from_another_program(self,from_client:str,to_client:str,data:dict,task_id:str):
        client:Client = self.clients_mapping.get(to_client)
        if client != None:
            self.function_return_to = to_client
            self.function_return_from = from_client
            self.function_return_routed += 1
            logger.info(f"found client with {to_client} and sending requested process output task id: {task_id} and data: {data}")
            return client.return_function(data,task_id)
    
    def unregister_client(self,client_id):
        client = self.clients_mapping.get(client_id)
        client.delete()
        self.clients_mapping.pop(client_id)
    async def start(self):
        self.clear_verification_stuff_task = await asyncio.create_task(self.__clear_verification_stuff())
    
    