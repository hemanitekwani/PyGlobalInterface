from asyncio import open_connection
from asyncio import StreamReader, StreamWriter
import asyncio
import json
from asyncio.queues import Queue
import time
from .event import ClientEvent, ManagerEvent
from .tasks import  Task, TaskStatus, RegisterClient, RegisterFunction, FunctinoCall, FunctionReturn
from uuid import uuid4
from typing import Dict
from .executer import FunctionRegistry, Function
class BaseClient:
    def __init__(self,host:str,port:int) -> None:
        self.port = port
        self.host = host
        self.sending_queue:Queue = Queue()
        self.receving_queue:Queue = Queue()
        self.reader:StreamReader = None
        self.writter:StreamWriter = None
        
        self.sender_task = None
        self.recever_task = None
        self.tasks:Dict[str,Task] = dict()
        self.delta = 0.00001
    async def connect(self):
        try:
            self.reader, self.writter = await open_connection(host=self.host,port=self.port)
            self.connection_status = True
            print("connection succefully")
            self.sender_task = asyncio.create_task(self.__sender_task())
            self.recever_task = asyncio.create_task(self.__recever_task())
        except Exception as e:
            print(e)
            self.connection_status = False
    def register_task(self,task_id:str,task:Task):
        self.tasks[task_id] = task

    async def start_task(self,task:Task):
        task.status = TaskStatus.WAIT
        await self.sending_queue.put(task)

    async def __sender_task(self):
        while True:
            data:Task = await self.sending_queue.get()
            print(f"SENDING DATA:{data}")
            try:
                self.writter.write(data.task.to_json().encode())
            except Exception as e:
                print(e)
                exit(1)
    
    async def process_request(self,data:dict):
        raise "NOT IMPLEMENTED"
    
    async def __recever_task(self):
        while True:
            try:
                data:dict = json.loads(await self.reader.read(4000))
                print(f"RECEVER DATA: {data}")
            except Exception as e:
                print(e)
                exit(1)
            await self.process_request(data)
  


class CServer(BaseClient):
    def __init__(self, host: str, port: int) -> None:
        super().__init__(host, port)
        self.FunctionRegistry = FunctionRegistry(self.sending_queue,self.delta)
        self.push_data = asyncio.create_task(self.FunctionRegistry.function_data_push())
        
    async def run_forver(self):
        try:
            while True:
                try:
                    await asyncio.sleep(self.delta)
                except asyncio.exceptions.CancelledError:
                    print("CLIENT IS CLOSING")
                    exit(0)
        except Exception as e:
            print(e)

    async def process_request(self, data: dict):
        _event = data.get("event")
        _task_id = data.get("task-id")
        if _event == ClientEvent.CLIENT_REGISTER_FAIL:
            self.tasks[_task_id].status = TaskStatus.ERROR
        elif _event == ClientEvent.CLEINT_FUNCTION_REGISTER_FAIL:
            self.tasks[_task_id].status = TaskStatus.ERROR

        elif _event == ClientEvent.CLIENT_REGISTER_SUCC:
            self.tasks[_task_id].status = TaskStatus.END
        elif _event == ClientEvent.CLEINT_FUNCTION_REGISTER_SUCC:
            self.tasks[_task_id].status = TaskStatus.END
        
        elif _event == ClientEvent.CLIENT_FUNCTION_CALL:
            _, task = Task.create(FunctinoCall(data["function-name"],data["source-program-name"],data["arguments"]))
            task.task.task_id = _task_id
            self.FunctionRegistry.run_function(task)
        
        elif _event == ClientEvent.CLIENT_FUNCTION_RETU:
            self.tasks[_task_id].status = TaskStatus.END
        
    async def register(self,client_name:str):
        task_id, task = Task.create(RegisterClient(client_name))
        self.register_task(task_id,task)
        await self.start_task(task)
        while True:
            if self.tasks[task_id].status == TaskStatus.END:
                return True
            elif self.tasks[task_id].status == TaskStatus.ERROR:
                return False
            await asyncio.sleep(self.delta)
    
    async def register_function(self,function_name:str,function):
        task_id, task = Task.create(RegisterFunction(function_name))
        self.register_task(task_id,task)
        await self.start_task(task)
        while True:
            if self.tasks[task_id].status == TaskStatus.END:
                self.FunctionRegistry.register_function(function_name,function)
                return True
            elif self.tasks[task_id].status == TaskStatus.ERROR:
                return False
            await asyncio.sleep(self.delta)
    async def functionCall(self,function,arguments):
        "program-id@function-name"
        prgram_id,function_name = function.split("@")
        task_id,task = Task.create(FunctinoCall(
            function_name=function_name,
            destination_program_name=prgram_id,
            arguments=arguments
        ))
        self.register_task(task_id,task)
        await self.start_task(task)
        while True:
            if self.tasks[task_id].status == TaskStatus.END:
                self.FunctionRegistry.register_function(function_name,function)
                return True
            elif self.tasks[task_id].status == TaskStatus.ERROR:
                return False
            await asyncio.sleep(self.delta)
