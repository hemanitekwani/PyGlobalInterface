from PyGlobalInterface.log import configure_logger
from asyncio.queues import Queue
from asyncio import StreamReader, StreamWriter
import asyncio
import json
from .Events import ClientEvent, ManagerEvent
from threading import Thread

logger = configure_logger(__name__)
class Client:
    def __init__(self,stream_writter:StreamWriter,ManagerQueue:Queue) -> None:
       self.stream_writter:StreamWriter = stream_writter
       self.manager_queue:Queue = ManagerQueue
       self.manager_out_queue:Queue = Queue()

       self.__sending_queue = Queue()
       self.recever_queue = Queue()

       self.client_name = None
       self.buffer_size = 4000

       self.__functions:set = set()
       self.__stop = False

       self.__thread = Thread(target=self.__start)

    async def __sender_task(self):
        logger.info("START")
        "sending queue olny contain dict"
        while True:
            try:
                
                data = await self.__sending_queue.get()
                logger.info(f"SENDING DATA: {data}")
                data:bytes = json.dumps(data).encode()
                self.stream_writter.write(data)
            except Exception as e:
                logger.error(f"{e}") 


                
    
    async def process_signal(self, payload):
        logger.info("START")
        try:
            logger.info(f"PAYLOADL: {payload}")

            # every payload have three part [event:str, data:str, message:str]
            event = payload["event"]
            task_id = payload["task_id"]
            
            logger.info(f"Processing event: {event}")
            if event == ClientEvent.CLIENT_REGISTER:
                self.client_name = payload["client_name"]
                logger.info(f"Client registration initiated: {self.client_name}")
                await self.manager_queue.put({
                    "event": ManagerEvent.CLIENT_VERIFYED,
                    "ref": self,
                    "task-id":task_id,
                    "client-name":self.client_name,
                    "message": f"NEW CLIENT REGISTER: {self.client_name}"
                })
                logger.info(f"[{event}][{self.client_name}] request manager to register")
                
            elif event == ClientEvent.CLEINT_FUNCTION_REGISTER:
                function_name = payload["function_name"]
                if function_name in self.__functions:
                    logger.warning(f"Function already registered: {function_name}")
                    await self.__sending_queue.put({
                        "event": ClientEvent.CLEINT_FUNCTION_REGISTER_FAIL,
                        "task-id":task_id,
                        "message": "FUNCTION IS ALREADY REGISTER"
                    })
                else:
                    self.__functions.add(function_name)
                    logger.info(f"Function registered successfully: {function_name}")
                    await self.__sending_queue.put({
                        "event": ClientEvent.CLEINT_FUNCTION_REGISTER_SUCC,
                        "task-id":task_id,
                        "message": "FUNCTION IS REGISTER REGISTER"
                    })
            elif event == ClientEvent.CLIENT_FUNCTION_CALL:
                logger.info(f"Function call requested: {payload['function_name']} with task-id: {payload['task_id']}")
                await self.manager_queue.put({
                    "event": ManagerEvent.CLIENT_FUNCTION_CALL,
                    "function-name": payload["function_name"],
                    "ref": self,
                    "task-id":payload['task_id'],
                    "destination-program-name": payload["destination_program_name"],
                    "arguments": payload["arguments"]
                })
            elif event == ClientEvent.CLIENT_FUNCTION_RETU:
                logger.info(f"Function return requested: {payload['function_name']} with task-id: {payload['task_id']}")
                await self.manager_queue.put({
                    "event": ManagerEvent.CLIENT_FUNCTION_RETU,
                    "function-name": payload["function_name"],
                    "ref": self,
                    "task-id":payload['task_id'],
                    "destination-program-name": payload["destination_program_name"],
                    "output": payload["output"]
                })
        except Exception as e:
            logger.info(f"ERROR: {e}")

    
    async def __manager_process(self):
        logger.info("Manager process START")
        while True:
            payload = await self.manager_out_queue.get()
            event = payload['event']
            task_id = payload["task-id"]
            logger.info(f"Processing event: {event}")
            if event == ManagerEvent.CLIENT_VERIFYED_SUCC:
                    logger.info("Client verification succeeded")
                    await self.__sending_queue.put({
                        "event": ClientEvent.CLIENT_REGISTER_SUCC,
                        "task-id":task_id,
                        "message": f"CLIENT IS VERIFY"
                    })
            elif event == ManagerEvent.CLIENT_VERIFYED_FAIL:
                logger.warning("Client verification failed")
                await self.__sending_queue.put({
                    "event": ClientEvent.CLIENT_REGISTER_FAIL,
                    "task-id":task_id,
                    "message": f"CLIENT IS NOT VERIFY"
                })
                logger.info("Sent CLIENT_FUNCTION_REGISTER_FAIL event")
            
            elif event == ManagerEvent.CLIENT_FUNCTION_CALL:
                await self.__sending_queue.put(
                    {
                        "event": ClientEvent.CLIENT_FUNCTION_CALL,
                        "arguments": payload["arguments"],
                        "task-id": payload["task-id"],
                        "function-name": payload["function-name"],
                        "source-program-name": payload["source-program-name"],
                        "message":"",
                    }
                )
                logger.info("Forwarded CLIENT_FUNCTION_CALL event")

            elif event == ManagerEvent.CLIENT_FUNCTION_RETU:
                await self.__sending_queue.put( 
                    {
                        "event": ClientEvent.CLIENT_FUNCTION_RETU,
                        "output": payload["output"],
                        "task-id": payload["task-id"],
                        "function-name": payload["function-name"],
                        "source-program-name": payload["source-program-name"],
                        "message":"",
                    })
                logger.info("Forwarded CLIENT_FUNCTION_RETU event")
            
    async def check_stop(self):
        logger.info("START")
        while not self.__stop:
            # logger.info("CHECK FOR STOP")
            await asyncio.sleep(2)
    

    def __start(self):
        loop = asyncio.new_event_loop()
        # self.manager_queue.put_nowait("HELLO")
        # recv = loop.create_task(self.__receving_task())
        send = loop.create_task(self.__sender_task())
        proc_out = loop.create_task(self.__manager_process())
        
        loop.run_until_complete(self.check_stop())
        
        proc_out.cancel()
        send.cancel()
    
    def stop(self):
        self.__stop = True

    def start(self):
        logger.info("START THREAD")
        self.__thread.start()
            



            