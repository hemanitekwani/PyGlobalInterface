from .base import BaseTask
from PythonClient.event import ClientEvent
import json


class FunctinoCall(BaseTask):
    def __init__(self,function_name:str, 
                 destination_program_name:str, 
                 arguments:dict) -> None:
        super().__init__(ClientEvent.CLIENT_FUNCTION_CALL,"","")
        self.function_name:str = function_name
        self.destination_program_name:str = destination_program_name
        if type(arguments) == dict:
            self.arguments:str = json.dumps(arguments)
        else: self.arguments = arguments
    def get(self):
        return json.loads(self.arguments)