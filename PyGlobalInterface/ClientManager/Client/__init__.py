from PyGlobalInterface.log import configure_logger
from asyncio.queues import Queue
from asyncio import StreamReader, StreamWriter
import asyncio
import json
from ResReq import Events, ResponsePayload


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
        self.task_recever_queue:Queue = Queue()
        self.task_sender_queue:Queue = Queue()

        # function list
        self.function_register_list:list = list()
        

        ## CLIENT INFORMATION
        self.client_id = None

        ## basic log
        addr, port = self.connection_client_writter.get_extra_info('peername')
        logger.info(f"address {addr} and port {port}")

        self.telemetry = False
    #                                                           PROCESS's for client management
    #
    #
    #
    async def __sender(self):
        while True:
            data = await self.task_sender_queue.get()
            await self.telemetry_queue.put({"client":self.client_id,"event":data['event'],'task':"send"})
            self.connection_client_writter.write(json.dumps(data).encode())
    async def __recever(self):
        while True:
            data = json.loads(await self.connection_client_reader.read(self.recever_buffer))
            await self.telemetry_queue.put({"client":self.client_id,"event":data['event'],'task':"receve"})
            await self.task_recever_queue.put(data)
    
    async def __process_recever_queue(self):
        while True:
            data:dict = await self.task_recever_queue.get()
            event:str = data.get('event')
            await self.telemetry_queue.put({"client":self.client_id,"event":data['event'],'task':"process"})
            if event == Events.REQ_VERIFY:
                await self.routing_queue.put()
    #
    #
    #
    def delete(self):
        self.task_sender_queue.put_nowait({"event":"rm-cli"})


    def function_present(self,function_name:str):
        logger.info(f"checking for function {function_name}")
        return function_name in self.function_register_list
    
    def return_function(self,data:dict,task_id:str):
        logger.info(f"CLIENT: {self.client_id} we get the task return data:{data} and task id:{task_id}")
        self.task_sender_queue.put_nowait({"event":"func-ret","data":data,"task_id":task_id})

    def call_function(self,to_client:str, function_name:str,data:dict,task_id:str):
        logger.info(f"getting function call request function name; {function_name} task id:{task_id} with input data : {data}")
        self.task_sender_queue.put_nowait({"event":"func-call","data":data,"task_id":task_id,"function_name":function_name,"to_client":to_client})
        return True
    
    def start_client(self):
        logger.info(f"start the client wait for verification")
        self.recever_task = self.__loop.create_task(self.__recever())
        self.sender_task  = self.__loop.create_task(self.__sender())
        self.process_task = self.__loop.create_task(self.__process_recever_queue())


