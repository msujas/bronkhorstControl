import socket
import os
import pandas as pd
import matplotlib.pyplot as plt
import selectors,types
import numpy as np
#from bronkhorstControlbm31.bronkhorstServer import getIP
import matplotlib
matplotlib.rcParams.update({'font.size':14})

HOST = 'localhost'
PORT = 61245

def connect(host=HOST, port=PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host,port))
    return s

class MFCclient():
    def __init__(self,address, host=HOST,port=PORT, multi=False,connid = socket.gethostname()):
        self.address = address
        self.host = host
        self.port = port
        self.connid = connid
        self.multi = multi
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
        datalines = data.split('\n')
        columns = datalines[0].split(';')
        print(datalines)
        array = [line.split(';') for line in datalines[1:] if line]
        print(array)
        df = pd.DataFrame(data = array,columns=columns)
        return df
    def closeServer(self):
        self.sendMessage('close')
    def sendMessage(self,message):
        bytemessage = bytes(message,encoding='utf-8')
        if not self.multi:
            self.s = connect(self.host,self.port)
            self.s.sendall(bytemessage)
            data = self.s.recv(1024)
            self.s.close()
            strdata = data.decode()
        else:
            strdata = self.multiClient(bytemessage)
        print(strdata)
        return strdata
    def makeMessage(self, *args):
        sep = ';'
        string = f'{args[0]}'
        for arg in args[1:]:
            string += f'{sep}{arg}'
        return string

    def multiClient(self,message):
        sel = selectors.DefaultSelector()
        server_addr = (self.host, self.port)

        print(f"Starting connection {self.connid} to {server_addr}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(server_addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        data = types.SimpleNamespace(
            connid=self.connid,
            msg_total=len(message),
            recv_total=0,
            messages=[message],
            outb=b"",
        )
        sel.register(sock, events, data=data)
        try:
            while True:
                events = sel.select(timeout=1)
                if events:
                    for key, mask in events:
                        receivedMessage = self.service_connection(key, mask,sel)
                        if receivedMessage:
                            receivedMessage = receivedMessage.replace('!','')
                # Check for a socket being monitored to continue.
                if not sel.get_map():
                    break
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            sel.close()
        return receivedMessage

    def service_connection(self,key, mask,sel):
        sock = key.fileobj
        data = key.data
        receivedMessage = b''
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                #print(f"Received {recv_data!r} from connection {data.connid}")
                receivedMessage+= recv_data
                data.recv_total += len(recv_data)
                if receivedMessage:
                    strMessage = receivedMessage.decode()
            if not recv_data or '!' in strMessage:
                print(f"Closing connection {data.connid}")
                sel.unregister(sock)
                sock.close()
                if recv_data:
                    return strMessage
                
            
        if mask & selectors.EVENT_WRITE:
            if not data.outb and data.messages:
                data.outb = data.messages.pop(0)
            if data.outb:
                print(f"Sending {data.outb} to connection {data.connid}")
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]      

def plotLoop(host, port = PORT,waittime = 1, multi = True, connid = 'plotLoop'):
    fig,(ax1,ax2) = plt.subplots(2,1)
    while True:
        try:
            ax1.set_title('Measure')
            ax2.set_title('Setpoint')
            df = MFCclient(1,host,port,multi=True, connid=connid).pollAll()
            df.plot.bar(x='User tag', y='fMeasure',ax=ax1)
            df.plot.bar(x='User tag', y='fSetpoint',ax=ax2)
            plt.tight_layout()
            plt.show(block = False)
            plt.pause(waittime)
            ax1.cla()
            ax2.cla()
        except KeyboardInterrupt:
            plt.close(fig)
            break

    
    
