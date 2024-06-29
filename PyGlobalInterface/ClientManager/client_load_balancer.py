class LoadBrancer:
    def __init__(self) -> None:
        self.client_list:list = list()
        self.client_selection_pointer = 0
        self.__counter = 0
    def is_aviable(self):
        return len(self.client_list) != 0
    def client_is_present(self,client_name):
        return client_name in self.client_list
    def add_client(self,client_name):
        self.client_list.append(client_name)
    def client_to_select(self):
        self.__counter += 1
        self.client_selection_pointer = self.__counter % len(self.client_list)
        return self.client_list[self.client_selection_pointer] 
