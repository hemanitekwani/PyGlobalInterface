from PyGlobalInterface.log import configure_logger
from asyncio.queues import Queue
from asyncio import StreamReader, StreamWriter
import asyncio
import json
from .ClientManager import ClientManager

logger = configure_logger(__name__)
class Client:
    def __init__(self,stream_reader:StreamReader,stream_writter:StreamWriter,manager) -> None:
        self.connection_client_reader:StreamReader = stream_reader
        self.connection_client_writter:StreamWriter = stream_writter
        self.manager:ClientManager = manager
        
        self.__loop = asyncio.get_running_loop()

        self.task_recever_queue:Queue = Queue()
        self.task_sender_queue:Queue = Queue()

        self.function_register_list:list = list()
        ## TASKS
        self.sender_task = None
        self.recever_task = None
        self.process_task = None

        ## CLIENT INFORMATION
        self.client_id = None

        ## basic log
        addr, port = self.connection_client_writter.get_extra_info('peername')
        logger.info(f"address {addr} and port {port}")

        self.telemetry = False
    async def __sender(self):
        while True:
            data = await self.task_sender_queue.get()
            self.connection_client_writter.write(json.dumps(data).encode())
    async def __recever(self):
        while True:
            data = json.loads(await self.connection_client_reader.read(4000))
            logger.info(f"receving data from client {data}")
            await self.task_recever_queue.put(data)
    
    async def __process_recever_queue(self):
        while True:
            data:dict = await self.task_recever_queue.get()
            event:str = data.get('event')
            if event == "reg-cli":
                self.client_id = data.get('client_id')
                logger.info(f"client is register with id: {data.get('client_id')}")
                await self.manager.add_verify_client(self.client_id,self)
                await self.task_sender_queue.put({"event":"reg-suc","client_id":data.get('client_id')})
            elif event == "reg-tel":
                self.telemetry = True
                self.client_id = data.get('client_id')
                logger.info(f"telemetry client is register with id: {data.get('client_id')}")
                await self.manager.add_verify_client(self.client_id,self)
                await self.task_sender_queue.put({"event":"reg-tel-suc","client_id":data.get('client_id')})
            elif event == "reg-func":
                function_name = data.get('function_name')
                if self.client_id != None:
                    self.function_register_list.append(function_name)
                    await self.task_sender_queue.put({"event":"func-reg-suc","function_name":function_name})
                    logger.info(f"CLIENT: {self.client_id} register new function {function_name}")
                else:
                    await self.task_sender_queue.put({"event":"func-reg-err","function_name":function_name})
            elif event == "func-call":
                from_client = data.get("from_client")
                function_name = data.get('function_name')
                task_id = data.get('task_id')
                __data:dict = data.get('data')
                to_client = self.client_id
                logger.info(f"program: {self.client_id} call this {function_name} function from program {from_client}")
                await self.manager.call_function_from_another_program(to_client,from_client,function_name,task_id,__data)
            elif event == "func-ret":
                __data:dict = data.get('data')
                to_client = data.get('to_client')
                task_id = data.get('task_id')
                logger.info(f"program {self.client_id} return output {__data} task id: {task_id}")
                await self.manager.return_function_from_another_program(to_client,__data,task_id)
            elif event == "unreg-cli":
                self.manager.unregister_client(self.client_id)
            elif event == "tel-info":
                if self.telemetry:
                    pass
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


