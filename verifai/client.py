from abc import ABC, abstractmethod
import socket
import dill


class Client(ABC):

    def __init__(self, port, bufsize):
        self.port = port
        self.bufsize = bufsize
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = socket._LOCALHOST
        try:
            self.socket.connect((self.host, self.port))
        except:
            print("Unable to connect")

    def receive(self):

        msg = self.socket.recv(self.bufsize)
        data = dill.loads(msg)
        return data


    def send(self, data):
        msg = dill.dumps(data)
        self.socket.send(msg)

    def close(self):
        self.socket.close()
        
    def run_client(self):
        try:
            sample = self.receive()
            sim = self.simulate(sample)
            self.send(sim)
            self.close()
            return True
        except:
            print("No new sample received.")
            return False


    @abstractmethod
    def simulate(self,sample):
        pass
