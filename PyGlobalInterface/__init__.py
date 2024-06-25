import asyncio
from PyGlobalInterface.log import configure_logger
from PyGlobalInterface.ClientManager import ClientManager, Client
logger = configure_logger(__name__)
class Server:
    def __init__(self,host,port) -> None:
        self.host:str = host
        self.port:int = port
        self.client_manager:ClientManager = ClientManager()
        
    async def handler(self,rd:asyncio.StreamReader,wr:asyncio.StreamWriter,):
        client:Client = Client(rd,wr,self.client_manager)
        self.client_manager.add_Client(client)
        client.start_client()

    async def __start(self):
        self.server = await asyncio.start_server(self.handler,self.host,self.port)
        logger.info(f"START server with PORT: {self.port} and HOST: {self.host}")
        async with self.server as server:
            await server.serve_forever()
    def start(self):
        self.loop = asyncio.new_event_loop()
        # await self.client_manager.start()
        try:
            task = self.loop.create_task(self.client_manager.start())
            self.loop.run_until_complete(self.__start())
        except KeyboardInterrupt:
            self.loop.close()
            logger.info("STOP server")
        except Exception as e:
            logger.error(e)
