import asyncio
from PyGlobalInterface.log import configure_logger
from PyGlobalInterface.ClientManager import ClientManager, Client
from concurrent.futures import ThreadPoolExecutor
import traceback
# from .TaskManager import TaskManager
logger = configure_logger(__name__)
class Server:
    def __init__(self,host,port) -> None:
        self.host:str = host
        self.port:int = port
        self.client_manager:ClientManager = ClientManager()
        # self.task_manager = TaskManager()
        
    async def handler(self,rd:asyncio.StreamReader,wr:asyncio.StreamWriter):
        logger.info("SOME THING IS CONNECTED")
        client = self.client_manager.make_client(rd,wr)
        client.start()

    async def __start(self):
        logger.info("SOME THING")
        self.server = await asyncio.start_server(self.handler,self.host,self.port)
        logger.info(f"START server with PORT: {self.port} and HOST: {self.host}")
        async with self.server as server:
            await server.serve_forever()
    def start(self):
        self.loop = asyncio.new_event_loop()
        self.loop.set_default_executor(ThreadPoolExecutor(20))
        # await self.client_manager.start()
        try:
            #TODO: fix it
            # t1,t2 = self.client_manager.start()
            # task1 = self.loop.create_task(t1)
            task2 = self.loop.create_task(self.client_manager.start())
            self.loop.run_until_complete(self.__start())
        except KeyboardInterrupt:
            self.client_manager.stop_all()
            self.loop.close()
            logger.info("STOP server")
        except Exception as e:
            logger.error(f"ERROR: {e}")
        # logger.info(traceback.print_exc())
        
