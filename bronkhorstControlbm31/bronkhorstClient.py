import socket
import os
import pandas as pd
import matplotlib.pyplot as plt

HOST = 'localhost'
PORT = 61245



class MFCclient():
    def __init__(self,address, host = HOST, port = PORT):
        self.address = address
        self.host = host
        self.port = port
    def readAddresses(self):
        string = self.makeMessage(self.address, 'getAddresses')
        addressesString = self.sendMessage(string)
        addresses = [int(a) for a in addressesString.split()]
        self.addresses = addresses
        print(addresses)
        return addresses
    def readName(self):
        string = self.makeMessage(self.address, 'readName')
        data = self.sendMessage(string)
        return data
    def readParam(self, name):
        string = self.makeMessage(self.address, 'readParam', name)
        data = self.sendMessage(string)
        return data
    def readFlow(self):
        string = self.makeMessage(self.address, 'readFlow')
        data = self.sendMessage(string)
        return float(data)
    def readSetpoint(self):
        string = self.makeMessage(self.address, 'readSetpoint')
        data = self.sendMessage(string)
        return float(data)
    def writeParam(self, name, value):
        string = self.makeMessage(self.address, 'writeParam', name, value)
        data = self.sendMessage(string)
        return data
    def writeSetpoint(self,value):
        string = self.makeMessage(self.address, 'writeSetpoint', value)
        data = self.sendMessage(string)
        return data
    def readControlMode(self):
        string = self.makeMessage(self.address, 'readControlMode')
        data = self.sendMessage(string)
        return data
    def writeControlMode(self,value):
        string = self.makeMessage(self.address, 'writeControlMode',value)
        data = self.sendMessage(string)
        return data
    def readFluidType(self):
        string = self.makeMessage(self.address, 'readFluidType')
        data = self.sendMessage(string)
        return data
    def writeFluidIndex(self,value):
        string = self.makeMessage(self.address, 'writeFluidIndex',value)
        data = self.sendMessage(string)
        return data
    def pollAll(self):
        string = self.makeMessage(self.address, 'pollAll')
        data = self.sendMessage(string)
        tmpfile = f'{os.path.dirname(os.path.realpath(__file__))}/tmpdf2.dat'
        f= open(tmpfile,'w')
        f.write(data)
        f.close()
        df = pd.read_csv(tmpfile,sep = ';',index_col=0)
        return df
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
    def makeMessage(self, *args):
        sep = ';'
        string = f'{args[0]}'
        for arg in args[1:]:
            string += f'{sep}{arg}'
        return string
        

def plotLoop(ipaddress = 'localhost'):
    
    fig,(ax1,ax2) = plt.subplots(2,1)
    while True:
        ax1.set_title('Measure')
        ax2.set_title('Setpoint')
        df = MFCclient(1,ipaddress)
        df.plot.bar(x='User tag', y='fMeasure',ax=ax1)
        df.plot.bar(x='User tag', y='fSetpoint',ax=ax2)
        plt.show(block = False)
        plt.pause(1)
        ax1.cla()
        ax2.cla()


    
    
