from .function_call import FunctinoCall
from .function_ret import FunctionReturn
from .register_client import RegisterClient
from .register_function import RegisterFunction
from .base import BaseTask
from uuid import uuid4

class TaskStatus:
    START = "START"
    WAIT = "WAIT"
    END = "END"
    ERROR = "ERROR"
class Task:
    def __init__(self,task:BaseTask) -> None:
        self.status:str = TaskStatus.START
        self.task = task
    @staticmethod
    def getID():
        return str(uuid4())
    @staticmethod
    def create(task:BaseTask):
        task_id = Task.getID()
        task.set_task_id(task_id)
        return task_id, Task(task)
    def __repr__(self) -> str:
        return f"""
status {self.status}
task {self.task.to_json()}
"""
    