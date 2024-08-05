from PyGlobalInterface.ClientManager import Client
from PyGlobalInterface.log import configure_logger
from time import time
from asyncio import sleep
from typing import List, Dict
import asyncio
from asyncio import StreamReader, StreamWriter
from asyncio import Queue
from PyGlobalInterface.Clients.Client import Client
from PyGlobalInterface.Clients.Events import ManagerEvent

logger = configure_logger(__name__)
class ClientManager:
    def __init__(self) -> None:
        self.client_mapping:dict = dict()
        self.client_verify_list:list = []

        self.manager_queue:Queue = Queue()

        self.time_delta = 3


    def make_client(self,stream_reader:StreamReader,stream_writter:StreamWriter):
        client = Client(
            stream_reader=stream_reader,
            stream_writter=stream_writter,
            ManagerQueue=self.manager_queue
        )
        self.client_verify_list.append(
            (
                client,
                time()
            )
        )
        return client
    
    async def clean_corotine(self):
        "client_verify_list:list [] run every 5 sec and remove the bud client"
        #BUG
        while True:
            await asyncio.sleep(5)
            logger.info("CLEAN COROTINE WAKE UP")
            start = time()
            idx = []
            for i,v in enumerate(self.client_verify_list):
                c,t = v
                if (start - t) > self.time_delta or c.client_name != None:
                    idx.append(i)
            for i in idx[::-1]:
                self.client_verify_list.pop(i)

    async def __verify_client(self,name,ref:Client) -> bool:
        if name in self.client_mapping:
            return False
       
        else:
            self.client_mapping[name] = ref
            return True
    

        

    async def __process_client(self):
        logger.info("START")
        
        try:
            while True:
                logger.info("start the client queue")
                try:
                    command = await self.manager_queue.get()
                # "this two were fix for every packet {event:<>,ref:<>}"
                    logger.info(f"DATA: {command}")
                    event:str = command.get("event")
                    ref:Client = command.get("ref")
                except Exception as e:
                    logger.info(f"ERROR {e}")
                
                if event == ManagerEvent.CLIENT_VERIFYED:
                    "ref, name"
                    try:
                        verified = await self.__verify_client(command.get("client-name"),ref)
                        if verified:
                          await ref.manager_out_queue.put({
                            "event": ManagerEvent.CLIENT_VERIFYED_SUCC,
                            "message": "client is succefully verify"
                          })

                        else:
                            await ref.manager_out_queue.put({
                                "event": ManagerEvent.CLIENT_VERIFYED_FAIL,
                                "message": "Client already exists"
                            })
                    except Exception as e:
                        await ref.manager_out_queue.put({
                            "event": ManagerEvent.CLIENT_VERIFYED_FAIL,
                            "message": f"error: {e}"
                        })

                elif event == ManagerEvent.CLIENT_FUNCTION_CALL:
                    "function-name, destination-program-name, arguments(base64), task_id"
                    #TODO: add checks
                    destination:Client = self.client_mapping.get(event["destination-program-name"])
                    await destination.manager_out_queue.put({
                        "event": ManagerEvent.CLIENT_FUNCTION_CALL,
                        "function-name": command.get('function-name'),
                        "source-program-name": ref.client_name,
                        "arguments": command.get("arguments"),
                        "task-id": command.get("task-id"),
                        "message": f"calling function {command.get('function-name')}, by {ref.client_name}"
                    })
                elif event == ManagerEvent.CLIENT_FUNCTION_RETU:
                    "function-name, destination-program-name, output(base64), task_id"
                    destination:Client = self.client_mapping.get(event["destination-program-name"])
                    await destination.manager_out_queue.put({
                        "event": ManagerEvent.CLIENT_FUNCTION_RETU,
                        "function-name": command.get('function-name'),
                        "source-program-name": ref.client_name,
                        "output": command.get("output"),
                        "task-id": command.get("task-id"),
                        "message": f"calling function {command.get('function-name')}, by {ref.client_name}"
                    })
                else:
                    await ref.manager_out_queue.put({
                        "event":ManagerEvent.INVALID_EVENT,
                        "message":"INVALID EVENT COMES"
                    })
        except Exception as e:
            logger.info(f"ERROR: {e}")

    def stop_all(self):
        for i in self.client_mapping.keys():
            self.client_mapping[i].stop()

    async def start(self):
        await self.__process_client()


            


    