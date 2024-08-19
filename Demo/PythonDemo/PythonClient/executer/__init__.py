from threading import Thread
import json
import asyncio
from typing import List, Dict
from asyncio.queues import Queue
from copy import deepcopy
from PythonClient.tasks import Task, FunctionReturn, RegisterFunction, FunctinoCall

class FunctionStatus:
    START = "START"
    WAIT = "WAIT"
    END = "END"
    ERROR = "ERROR"


class Function(Thread):
    def __init__(self,function_name,function_ref) -> None:
        Thread.__init__(self)
        self.function_name = function_name
        self.function_Ref = function_ref
        self.__output = None
        self.status = None
        self.task:Task = None
    def _start(self,arguments):
        self.status = FunctionStatus.START
        print(arguments)
        self.arguments = arguments
        self.start()
        return self
    def run(self) -> None:
        print(f"FUNCTION start executing: {self.function_name}")
        try:
            self.status = FunctionStatus.WAIT
            self.__output = self.function_Ref(self.arguments)
            print("GOT OUTPUT")
        except Exception as e:
            self.status = FunctionStatus.ERROR
            print(e)
        self.status = FunctionStatus.END
    def get_output(self):
        if self.__output:
            self.status = None
            return json.dumps(self.__output)
        return ""
def MakeFuntionThread(function:Function)-> Function:
    return Function(function.function_name,function.function_Ref)
class FunctionRegistry:
    def __init__(self,sender_queue:Queue,delta:float) -> None:
        self.__registry:Dict[str,Function] = dict()
        self.sender_queue = sender_queue
        self.thread_pool:List[Function] = list()
        self.delta = delta
    
    def register_function(self,function_name,function_ref):
        self.__registry[function_name] = Function(function_name,function_ref)
        

    def run_function(self,task:Task):
        print(f"TASK: {task}")
        function_name = task.task.function_name
        arguments = task.task.arguments

        function = self.__registry.get(function_name)
        
        if function:
            print(f"PREPRALING FOR LAUNCING FUNCTION {function.function_name}")
            function = MakeFuntionThread(function)
            function.task = task
            self.thread_pool.append(function._start(arguments))
            return True
        return False
    
    async def function_data_push(self):
        while True:
            pop_idx = []
            for idx,val in enumerate(self.thread_pool):
                if val.status == FunctionStatus.END:
                    _task:FunctinoCall = val.task.task
                    _, task = Task.create(FunctionReturn(val.function_name,_task.destination_program_name,val.get_output())) 
                    task.task.task_id = _task.task_id
                    await self.sender_queue.put(task)
            await asyncio.sleep(self.delta)
