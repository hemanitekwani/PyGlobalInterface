from asyncio import open_connection
from asyncio import StreamReader, StreamWriter
import asyncio
import json
from asyncio.queues import Queue
from threading import Thread
from uuid import uuid4
import time
from .event import ClientEvent, ManagerEvent

class PyGlobalInterface_Client:
    def __init__(self,client_name:str) -> None:
        self.port = 9800
        self.host = "127.0.0.1"
        self.reader:StreamReader = None
        self.writter:StreamWriter = None
        self.connection_status = False
        self.loop = asyncio.new_event_loop()
        self.loop.run_until_complete(self.connect())
        self.client_name:str = client_name

        self.sending_queue:Queue = Queue()
        self.receving_queue:Queue = Queue()
        self.function_call_queue:Queue = Queue()


        self.recever_task = self.loop.create_task(self.__sender())
        self.sender_task = self.loop.create_task(self.__recever())
        self.function_runner = self.loop.create_task(self.__function_prcessing())


        self.function_register_hashmap:dict = dict()

        self.function_called_task_hashmap:dict = dict()

        self.rm_cli = False

        self.thread_list = []
    async def connect(self):
        try:
            self.reader,self.writter = await open_connection(host=self.host,port=self.port)
            self.connection_status = True
        except:
            self.connection_status = False


    async def __sender(self):
        while self.connection_status:
            data:dict = await self.sending_queue.get()
            print(f"sending data: {data}")
            self.writter.write(json.dumps(data).encode())
            
    async def __recever(self):
        while self.connection_status:
            data:dict = json.loads(await self.reader.read(4000))
            print(f"receving from {data}")
            if data['event'] == "func-call":
                await self.function_call_queue.put(data)
            elif data['event'] == "func-ret":
                # print(data)
                self.function_called_task_hashmap[data['task_id']] = data['data']
            elif data['event'] == "rm-cli":
                self.rm_cli = True
            else:
                await self.receving_queue.put(data)


    def __function_runner(self,data:dict):
        __ = time.time()
        output = self.function_register_hashmap.get(data['function_name'])(data["data"])
        print(output)
        print( time.time() -__ )
        self.sending_queue.put_nowait({"event":"func-ret","data":output,"to_client":data["to_client"],"task_id":data['task_id']})
    
    async def __function_prcessing(self):
        while True:
            data:dict = await self.function_call_queue.get()
            async def __task(data):
                thread = Thread(target=self.__function_runner,args=(data,))
                thread.start()
                while thread.is_alive():
                    await asyncio.sleep(0.005)
            self.thread_list.append(self.loop.create_task(__task(data)))
            

    
    def client_register(self):
        print(self.connection_status)
        if self.connection_status:
            self.sending_queue.put_nowait(
                {
                    "event":ClientEvent.CLIENT_REGISTER,
                    "client-name":self.client_name
                }
            )
            data = self.loop.run_until_complete(self.receving_queue.get())
            if data['event'] == ClientEvent.CLEINT_FUNCTION_REGISTER_SUCC:
                return True
            return False
        
    def func_register(self,function_name:str,function_ref):
        if self.connection_status:
            self.function_register_hashmap[function_name] = function_ref
            self.sending_queue.put_nowait({"event":"reg-func","function_name":function_name})
            data = self.loop.run_until_complete(self.receving_queue.get())
            if data['event'] == "func-reg-suc":
                return True
            elif data['event'] == "func-reg-err":
                return False
            return False
    
    async def call_function(self,function_name:str,data:dict):
        """function: program2@run_function1"""
        client_name,function_name = function_name.split("@")
        task_id = str(uuid4())
        self.function_called_task_hashmap[task_id] = None
        await self.sending_queue.put({"event":"func-call","from_client":client_name,"data":data,"task_id":task_id,"function_name":function_name})
        while self.function_called_task_hashmap[task_id] == None:
            await asyncio.sleep(0.03)
        return self.function_called_task_hashmap[task_id]
    
    def stop(self):
        self.sending_queue.put_nowait({"event":"unreg-cli","client_name":self.client_name})
        while not self.rm_cli:
            time.sleep(0.3)
        self.sender_task.cancel("time to stop")
        self.recever_task.cancel("time to stop")
        self.function_runner.cancel("time to stop")


from .tasks import  Task, TaskStatus, RegisterClient, RegisterFunction, FunctinoCall, FunctionReturn
from uuid import uuid4
from typing import Dict
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
            pass
   
        
    async def register(self,client_name:str):
        task_id, task = Task.create(RegisterClient(client_name))
        self.register_task(task_id,task)
        await self.start_task(task)
        while True:
            if self.tasks[task_id].status == TaskStatus.END:
                return True
            elif self.tasks[task_id].status == TaskStatus.ERROR:
                return False
            await asyncio.sleep(0.5)
    
    async def register_function(self,function_name:str,function):
        task_id, task = Task.create(RegisterFunction(function_name))
        self.register_task(task_id,task)
        await self.start_task(task)
        while True:
            if self.tasks[task_id].status == TaskStatus.END:
                return True
            elif self.tasks[task_id].status == TaskStatus.ERROR:
                return False
            await asyncio.sleep(0.5)