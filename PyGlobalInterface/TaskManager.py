from .ClientManager import ClientManager, Client
import PySimpleGUI as sg
import asyncio
from threading import Thread
import collections  


class TaskManager:
    def __init__(self,manager:ClientManager) -> None:
        self.manager:ClientManager = manager
        self.num = 0
        self.layout = [
            [sg.Text("TASK MANAGER")],
            # [sg.Listbox(values=[],key="client_list",size=(30, 30))],
            [sg.Table(values=[],key="table", headings=["sno.", "client name", "revc", "send", "functions"],size=(40,20))]

        ]
        self.window = sg.Window('Window Title', self.layout)
        self.window.Resizable = True
        self.display_thread = Thread(target=self.start,args=())
        self.display_thread.start()
        
  
    async def __update_client_list(self):
        # prev = []
        while True:
            await asyncio.sleep(0.07)
            
            data = list(self.manager.clients_mapping.keys())
            report = []
            for idx, client_key in enumerate(data):
                client = self.manager.clients_mapping[client_key]
                send = client.task_sender_queue.qsize()
                revc = client.task_recever_queue.qsize()
                
                report.append([idx+1,client_key,revc,send," ".join(client.function_register_list)])

            
            self.window['table'].update(report)
            
          

    async def __start_event_manager_task(self):
        while True:
            event, values = self.window.read(timeout=1)

            if event == sg.WIN_CLOSED:
                break
            elif event == "hi":
                self.num += 1
                self.window['xxx'].update(self.num)
           
            await asyncio.sleep(0.001)
            
        self.window.close()
    def start(self):
        loop = asyncio.new_event_loop()
        loop.create_task(self.__update_client_list())
        loop.run_until_complete(self.__start_event_manager_task())
    
