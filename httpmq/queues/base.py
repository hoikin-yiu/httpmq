from abc import ABCMeta, abstractmethod


class Queue(metaclass=ABCMeta):

    @abstractmethod
    async def get(self):
        pass

    @abstractmethod
    async def put(self, data):
        pass

    @abstractmethod
    async def status(self):
        pass

    @abstractmethod
    async def reset(self):
        pass

    @abstractmethod
    async def view(self, position):
        pass
