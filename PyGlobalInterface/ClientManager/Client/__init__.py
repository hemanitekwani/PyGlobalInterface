from PyGlobalInterface.log import configure_logger
from asyncio.queues import Queue
from asyncio import StreamReader, StreamWriter
import asyncio
import json
from ResReq import Events, EventsClientManger


logger = configure_logger(__name__)
class Client:
    def __init__(self,stream_reader:StreamReader,stream_writter:StreamWriter,telemetry_queue:Queue,routing_queue:Queue,recever_buffer:int) -> None:
        # buffer
        self.recever_buffer = recever_buffer
        # connection
        self.connection_client_reader:StreamReader = stream_reader
        self.connection_client_writter:StreamWriter = stream_writter

        # processing queue
        self.telemetry_queue:Queue = telemetry_queue
        self.routing_queue:Queue  = routing_queue
        
        # event loop
        self.__loop = asyncio.get_running_loop()

        # internal queue
        self.recever_queue:Queue = Queue()
        self.sender_queue:Queue = Queue()

        # function list
        self.function_register_list:list = list()
        

        ## CLIENT INFORMATION
        self.client_id = None

        ## basic log
        addr, port = self.connection_client_writter.get_extra_info('peername')
        logger.info(f"address {addr} and port {port}")

        self.verify = False
        self.telemetry = False
    #                                                           PROCESS's for client management
    #
    #
    #
    async def __sender(self):
        while True:
            data = await self.sender_queue.get()
            await self.telemetry_queue.put({"client":self.client_id,"event":data['event'],'task':"send"})
            self.connection_client_writter.write(json.dumps(data).encode())
    async def __recever(self):
        while True:
            data = json.loads(await self.connection_client_reader.read(self.recever_buffer))
            await self.telemetry_queue.put({"client":self.client_id,"event":data['event'],'task':"receve"})
            await self.recever_queue.put(data)
    
    async def __process_recever_queue(self):
        while True:
            data:dict = await self.recever_queue.get()
            event:str = data.get('event')
            await self.telemetry_queue.put({"client":self.client_id,"event":data['event'],'task':"process"})
            if not self.verify:
                await self.sender_queue.put({"event":Events.AWK_CLIENT_NOT_VERIFY_DUE_TO_CHECK})
                continue
            if event == Events.REQ_VERIFY:
                await self.routing_queue.put({"event":EventsClientManger.REQ_MAKE_CLIENT_VERIFY,"client_id":data["client_id"], "ref": self})
            
            await self.sender_queue.put({"event":Events.AWK_CLIENT_RECV})

    async def verify_client(self,client_id:str,succesful:bool):
        if not self.verify and succesful:
            self.verify = True
            self.client_id = client_id
            await self.sender_queue.put({"event":Events.AWK_CLIENT_VERIFY})
            return
        await self.sender_queue.put({"event":Events.AWK_CLIENT_NOT_VERIFY_DUE_TO_CHECK})

    #
    #
    #

    def start_client(self):
        logger.info(f"start the client wait for verification")
        self.recever_task = self.__loop.create_task(self.__recever())
        self.sender_task  = self.__loop.create_task(self.__sender())
        self.process_task = self.__loop.create_task(self.__process_recever_queue())


