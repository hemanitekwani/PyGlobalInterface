import json
class BaseTask:
    def __init__(self,event:str,message:str,task_id:str) -> None:
        self.event = event
        self.message = message
        self.task_id = task_id
    def set_task_id(self,id:str):
        self.task_id = id
    def to_json(self):
       return json.dumps(self.__dict__)
   