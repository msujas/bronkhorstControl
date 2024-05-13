import socket
from bronkhorstControlbm31.bronkhorstServer import addresses
HOST = 'localhost'
PORT = 61245




class MFCclient():
    def __init__(self,address, host = HOST, port = PORT):
        self.address = address
        self.host = host
        self.port = port
    def readName(self):
        string = f'{self.address} readName'
        self.sendMessage(string)
        return string
    def readParam(self, name):
        string = f'{self.address} readParam {name}'
        self.sendMessage(string)
        return string
    def readFlow(self):
        string = f'{self.address} readFlow'
        self.sendMessage(string)
        return string
    def readSetpoint(self):
        string = f'{self.address} readSetpoint'
        self.sendMessage(string)
        return string
    def writeParam(self, name, value):
        string = f'{self.address} writeParam {name} {value}'
        self.sendMessage(string)
        return string
    def writeSetpoint(self,value):
        string = f'{self.address} writeSetpoint {value}'
        self.sendMessage(string)
        return string
    def closeServer(self):
        self.sendMessage('close')
    def sendMessage(self,message):
        s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(self.host,self.port)
        s.sendall(bytes(message,encoding='utf-8'))
        data = s.recv(1024)
        print(data)
        s.close()




    
    
