from .base import BaseTask
from PythonClient.event import ClientEvent

class RegisterClient(BaseTask):
    def __init__(self, client_name:str) -> None:
        super().__init__(ClientEvent.CLIENT_REGISTER, f"New Client {client_name}","")
        self.client_name = client_name
    