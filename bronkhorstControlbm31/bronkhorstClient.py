import socket

HOST = 'localhost'
PORT = 61245



class MFCclient():
    def __init__(self,address, host = HOST, port = PORT):
        self.address = address
        self.host = host
        self.port = port
    def readAddresses(self):
        addressesString = self.sendMessage(f'{self.address} getAddresses')
        addresses = [int(a) for a in addressesString.split()]
        self.addresses = addresses
        print(addresses)
        return addresses
    def readName(self):
        string = f'{self.address} readName'
        data = self.sendMessage(string)
        return data
    def readParam(self, name):
        string = f'{self.address} readParam {name}'
        data = self.sendMessage(string)
        return data
    def readFlow(self):
        string = f'{self.address} readFlow'
        data = self.sendMessage(string)
        return float(data)
    def readSetpoint(self):
        string = f'{self.address} readSetpoint'
        data = self.sendMessage(string)
        return float(data)
    def writeParam(self, name, value):
        string = f'{self.address} writeParam {name} {value}'
        data = self.sendMessage(string)
        return data
    def writeSetpoint(self,value):
        string = f'{self.address} writeSetpoint {value}'
        data = self.sendMessage(string)
        return data
    def readControlMode(self):
        string = f'{self.address} readControlMode'
        data = self.sendMessage(string)
        return data
    def writeControlMode(self,value):
        string = f'{self.address} writeControlMode {value}'
        data = self.sendMessage(string)
        return data
    def readFluidType(self):
        string = f'{self.address} readFluidType'
        data = self.sendMessage(string)
        return data
    def writeFluidIndex(self,value):
        string = f'{self.address} writeFluidIndex {value}'
        data = self.sendMessage(string)
        return data
    def closeServer(self):
        self.sendMessage('close')
    def sendMessage(self,message):
        s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host,self.port))
        s.sendall(bytes(message,encoding='utf-8'))
        data = s.recv(1024)
        strdata = data.decode()
        print(strdata)
        s.close()
        return strdata
    def pollAll(self):
        string = f'{self.address} pollAll'
        data = self.sendMessage(string)
        return data




    
    
