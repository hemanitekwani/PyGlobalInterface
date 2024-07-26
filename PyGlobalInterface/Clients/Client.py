from PyGlobalInterface.log import configure_logger
from asyncio.queues import Queue
from asyncio import StreamReader, StreamWriter
import asyncio
import json
from .Events import ClientEvent, ManagerEvent
from threading import Thread

logger = configure_logger(__name__)
class Client:
    def __init__(self,stream_reader:StreamReader,stream_writter:StreamWriter,ManagerQueue:Queue,ManagerOutQueue:Queue) -> None:
       self.stream_reader:StreamReader = stream_reader
       self.stream_writter:StreamWriter = stream_writter
       self.manager_queue:Queue = ManagerQueue
       self.manager_out_queue:Queue = ManagerOutQueue

       self.__sending_queue = Queue()
       self.__recever_queue = Queue()

       self.client_name = None
       self.buffer_size = 1024 * 10

       self.function:set = set()
       self.__stop = False

       self.__thread = Thread(target=self.__start)
    async def __sender_task(self):
        "sending queue olny contain dict"
        while True:
            data:bytes = json.dumps(await self.__sending_queue.get()).encode()
            self.stream_writter.write(data)
    async def __receving_task(self):
        "receive that data and put in the __recever_queue for futher processing"
        while True:
            data:dict = json.loads(await self.stream_reader.read(self.buffer_size))
            await self.__recever_queue.put(data)

    async def __process_signal(self):
        while True:
            payload:dict = await self.__recever_queue.get()
            event = payload["event"]
            if event == ClientEvent.CLIENT_REGISTER:
                self.client_name = payload["client_name"]
                await self.manager_queue.put({
                    "event": ManagerEvent.CLIENT_VERIFYED,
                    "client_name":self.client_name,
                    "message": f"NEW CLIENT REGISTER: {self.client_name}"
                })
                res:dict = await self.manager_out_queue.get()
                if res["event"] == ManagerEvent.CLIENT_VERIFYED_SUCC:
                    await self.__sending_queue.put({
                        "event": ClientEvent.CLEINT_FUNCTION_REGISTER_SUCC,
                        "message": f"CLIENT IS VERIFY"
                    })
                else:
                    await self.__sending_queue.put({
                        "event": ClientEvent.CLEINT_FUNCTION_REGISTER_FAIL,
                        "message": f"CLIENT IS NOT VERIFY"
                    })
            elif event == ClientEvent.CLEINT_FUNCTION_REGISTER:
                function_name = payload["function_name"]
                if function_name in self.function:
                    await self.__sending_queue.put({
                        "event": ClientEvent.CLEINT_FUNCTION_REGISTER_FAIL,
                        "message": "FUNCTION IS ALREADY REGISTER"
                    })
                else:
                    await self.__sending_queue.put({
                        "event": ClientEvent.CLEINT_FUNCTION_REGISTER_SUCC,
                        "message": "FUNCTION IS REGISTER REGISTER"
                    })
            elif event == ClientEvent.CLIENT_FUNCTION_CALL:
                pass
    async def check_stop(self):
        while not self.__stop:
            await asyncio.sleep(0.5)

    def __start(self):
        loop = asyncio.new_event_loop()
        recv = loop.create_task(self.__receving_task())
        send = loop.create_task(self.__sender_task())
        proc = loop.create_task(self.__process_signal())
        loop.run_until_complete(self.check_stop())
        recv.cancel()
        send.cancel()
        proc.cancel()
    
    def stop(self):
        self.__stop = True
    def start(self):
        self.__thread.start()
            



            