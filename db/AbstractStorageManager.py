from abc import ABC, abstractmethod


class AbstractStorageManager(ABC):

    @abstractmethod
    def create_query(self, data):
        pass

    @abstractmethod
    def read_query(self, data):
        pass

    @abstractmethod
    def update_query(self, data):
        pass

    @abstractmethod
    def delete_query(self, target_obj):
        pass

    @abstractmethod
    def list_query(self):
        pass
