from abc import ABC, abstractmethod
import socket
import dill


class Client(ABC):

    def __init__(self, port, bufsize):
        self.port = port
        self.bufsize = bufsize

    def initialize(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = '127.0.0.1'
        try:
            self.socket.connect((self.host, self.port))
        except OSError as e:
            raise RuntimeError('unable to connect to server') from e

    def receive(self):
        data = []
        try:
            while True:
                msg = self.socket.recv(self.bufsize)
                if not msg:
                    break
                data.append(msg)
        except OSError:
            return False, None
        data = dill.loads(b"".join(data))
        return True, data

    def send(self, data):
        msg = dill.dumps(data)
        self.socket.send(msg)

    def close(self):
        self.socket.close()

    def run_client(self):
        self.initialize()
        success, sample = self.receive()
        if not success:
            print("No new sample received from server.")
            return False
        sim = self.simulate(sample)
        self.send(sim)
        self.close()
        return True

    @abstractmethod
    def simulate(self,sample):
        pass
