import json
class BaseSerilizer:
    def __init__(self,_json:str) -> None:
        self.__dict__ = json.loads(_json)
   