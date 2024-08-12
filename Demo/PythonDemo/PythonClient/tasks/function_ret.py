from .base import BaseTask
from PythonClient.event import ClientEvent
import json
class FunctionReturn(BaseTask):
    def __init__(self,function_name:str, destination_program_name:str, output:dict) -> None:
        super().__init__(ClientEvent.CLIENT_FUNCTION_RETU, "", "")
        self.function_name = function_name
        self.destination_program_name = destination_program_name
        if type(output) == dict:
            self.output = json.dumps(output)
        else: self.output = output
    def get(self):
        return json.loads(self.output)