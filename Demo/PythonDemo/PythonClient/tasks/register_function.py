from .base import BaseTask
from PythonClient.event import ClientEvent

class RegisterFunction(BaseTask):
    def __init__(self, function_name:str) -> None:
        super().__init__(ClientEvent.CLEINT_FUNCTION_REGISTER, 
                         f"New Function is register {function_name}",
                         "")
        self.function_name = function_name