from PyGlobalInterface.log import configure_logger
from asyncio.queues import Queue
from asyncio import StreamReader, StreamWriter
import asyncio
import json
from .Events import ClientEvent, ManagerEvent
from threading import Thread

logger = configure_logger(__name__)
class Client:
    def __init__(self,stream_reader:StreamReader,stream_writter:StreamWriter,ManagerQueue:Queue) -> None:
       self.stream_reader:StreamReader = stream_reader
       self.stream_writter:StreamWriter = stream_writter
       self.manager_queue:Queue = ManagerQueue
       self.manager_out_queue:Queue = Queue()

       self.__sending_queue = Queue()
       self.__recever_queue = Queue()

       self.client_name = None
       self.buffer_size = 4000

       self.function:set = set()
       self.__stop = False

       self.__thread = Thread(target=self.__start)
    async def __sender_task(self):
        logger.info("START")
        "sending queue olny contain dict"
        while True:
            data:bytes = json.dumps(await self.__sending_queue.get()).encode()
            self.stream_writter.write(data)
    async def __receving_task(self):
        logger.info("START")
        "receive that data and put in the __recever_queue for futher processing"
        while True:
            data:dict = json.loads(await self.stream_reader.read(self.buffer_size))
            logger.info(data)
            await self.__recever_queue.put(data)

    async def __process_signal(self):
        logger.info("START")
        try:
            while True:
                payload:dict = await self.__recever_queue.get()
                logger.info(f"PAYLOADL: {payload}")
                event = payload["event"]
                if event == ClientEvent.CLIENT_REGISTER:
                    self.client_name = payload["client-name"]
                    await self.manager_queue.put({
                        "event": ClientEvent.CLEINT_FUNCTION_REGISTER,
                        "ref": self,
                        "client-name":self.client_name,
                        "message": f"NEW CLIENT REGISTER: {self.client_name}"
                    })
                    logger.info("PUSH THE REG REQ IN MANAGER QUEUE")
                    
                elif event == ClientEvent.CLEINT_FUNCTION_REGISTER:
                    function_name = payload["function-name"]
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
                    await self.manager_queue.put({
                        "event": ManagerEvent.CLIENT_FUNCTION_CALL,
                        "function-name": payload["function-name"],
                        "ref": self,
                        "task-id":payload['task-id'],
                        "destination-program-name": payload["destination-program-name"],
                        "arguments": payload["arguments"]
                    })
                elif event == ClientEvent.CLIENT_FUNCTION_RETU:
                    await self.manager_queue.put({
                        "event": ManagerEvent.CLIENT_FUNCTION_RETU,
                        "function-name": payload["function-name"],
                        "ref": self,
                        "task-id":payload['task-id'],
                        "destination-program-name": payload["destination-program-name"],
                        "output": payload["output"]
                    })
        except Exception as e:
            logger.info(f"ERROR: {e}")

    #TODO: no need of this remove this
    async def __manager_process(self):
        logger.info("START")
        while True:
            payload = await self.manager_out_queue.get()
            event = payload['event']
            if event == ManagerEvent.CLIENT_VERIFYED_SUCC:
                    await self.__sending_queue.put({
                        "event": ClientEvent.CLEINT_FUNCTION_REGISTER_SUCC,
                        "message": f"CLIENT IS VERIFY"
                    })
            elif event == ManagerEvent.CLIENT_VERIFYED_FAIL:
                await self.__sending_queue.put({
                    "event": ClientEvent.CLEINT_FUNCTION_REGISTER_FAIL,
                    "message": f"CLIENT IS NOT VERIFY"
                })
            elif event == ManagerEvent.CLIENT_FUNCTION_CALL:
                await self.__sending_queue.put(payload)

            elif event == ManagerEvent.CLIENT_FUNCTION_RETU:
                await self.__sending_queue.put(payload)
            
    async def check_stop(self):
        logger.info("START")
        while not self.__stop:
            await asyncio.sleep(30)
    

    def __start(self):
        loop = asyncio.new_event_loop()
        recv = loop.create_task(self.__receving_task())
        send = loop.create_task(self.__sender_task())
        proc = loop.create_task(self.__process_signal())
        proc_out = loop.create_task(self.__manager_process())
        loop.run_until_complete(self.check_stop())
        proc_out.cancel()
        recv.cancel()
        send.cancel()
        proc.cancel()
    
    def stop(self):
        self.__stop = True
    def start(self):
        logger.info("START THREAD")
        self.__thread.start()
            



            