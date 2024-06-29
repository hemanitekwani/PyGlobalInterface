from .ClientManager import ClientManager, Client
import PySimpleGUI as sg
import asyncio
from threading import Thread
from asyncio import Queue
from .log import configure_logger

logger = configure_logger(__name__)
class TaskManager:
    def __init__(self,manager:ClientManager) -> None:
        self.manager:ClientManager = manager
        self.num = 0
        self.layout = [
            [sg.Text("TASK MANAGER")],
            # [sg.Listbox(values=[],key="client_list",size=(30, 30))],
            [sg.Text(text="status from manager loading ...",key="manager_status")],
            [sg.Table(values=[],key="table", headings=["sno.", "client name", "revc", "send", "functions", "function called", "function returned"],size=(40,20))],
            [sg.Text("Execute Command")],
            [[sg.Input(tooltip="command execute",key="command"),sg.Button(button_text="execute",key="exce")]],
            [sg.Text("Commnad history")],
            [sg.Table(values=[],headings=["command","status"],key="history_list",size=(50,20))]


        ]
        self.window = sg.Window('Window Title', self.layout)
        self.window.Resizable = True

        self.command_history:list = []
        self.command_unprocess_queue:Queue = Queue()
        self.command_procced = 0
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
                report.append([idx+1,client_key,client.recv,client.send," ".join(client.function_register_list),client.funcation_called,client.function_return])

            self.window['manager_status'].update(f"Manager Status\n\nClient Added: {self.manager.number_of_client_added}\nClient verify: {self.manager.number_of_client_verify}\nFunction routed: {self.manager.function_call_routed}\nFunction return: {self.manager.function_return_routed}\nCALLING QUEUE: {self.manager.function_call_to} -> {self.manager.function_call_from}\nRETURING QUEUE: {self.manager.function_return_from} -> {self.manager.function_call_to}\nPOLICYS: {self.manager.policys}")
            self.window['table'].update(report)
            self.window['history_list'].update(self.command_history)
            
    def __command_execute(self,command_tokens:list):
        if len(command_tokens) == 2:
            if command_tokens[0] == "delete":
                client_name = command_tokens[1]
                if client_name in self.manager.clients_mapping.keys():
                    client = self.manager.clients_mapping.pop(client_name)
                    del client
                    self.command_history.append([' '.join(command_tokens), "sucessful"])
                else:
                    self.command_history.append([' '.join(command_tokens), "fails"])
            else:
                self.command_history.append([' '.join(command_tokens), "fails"])
        elif len(command_tokens) == 4:
            if command_tokens[0] == "allow":
                host_name = command_tokens[1]
                function_name = command_tokens[2]
                client_name = command_tokens[3]
                host_client = self.manager.clients_mapping.get(host_name)
                if host_client != None:
                    if host_client.function_present(function_name):
                        if self.manager.ad_host_client_function_policy(host_name,client_name,function_name):
                            self.command_history.append([' '.join(command_tokens), "sucessful"])
                        else:
                            self.command_history.append([' '.join(command_tokens), "fails"])
                    else:
                        self.command_history.append([' '.join(command_tokens), "fails"])
                else:
                    self.command_history.append([' '.join(command_tokens), "fails"])
    async def __process_command(self):
        while True:
            command:str = await self.command_unprocess_queue.get()
            command = command.lower().strip()
            command_tokens = command.split(" ")
            self.__command_execute(command_tokens)
    async def __start_event_manager_task(self):
        while True:
            event, values = self.window.read(timeout=1)

            if event == sg.WIN_CLOSED:
                break
            elif event == "exce":
                command = values['command']
                await self.command_unprocess_queue.put(command)
           
            await asyncio.sleep(0.001)
            
        self.window.close()
    def start(self):
        loop = asyncio.new_event_loop()
        loop.create_task(self.__update_client_list())
        loop.create_task(self.__process_command())
        loop.run_until_complete(self.__start_event_manager_task())
        
    
