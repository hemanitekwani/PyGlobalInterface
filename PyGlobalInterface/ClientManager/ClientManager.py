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
        self.manager_out_queue:Queue = Queue()

        clean_task = asyncio.create_task(self.__clean_corotine())

        self.time_delta = 3
    def make_client(self,stream_reader:StreamReader,stream_writter:StreamWriter):
        client = Client(
            stream_reader=stream_reader,
            stream_writter=stream_writter,
            ManagerQueue=self.manager_queue,
            ManagerOutQueue=self.manager_out_queue
        )
        self.client_verify_list.append(
            (
                client,
                time()
            )
        )
    async def __clean_corotine(self):
        while True:
            start = time()
            idx = []
            for i,v in enumerate(self.client_verify_list):
                t,c = v
                if (start - t) > self.time_delta:
                    idx.append(i)
            for i in idx[::-1]:
                self.client_verify_list.pop(i)
    
    async def __process_client(self):
        while True:
            pass
            


    