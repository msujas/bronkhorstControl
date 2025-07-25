import socket
import pandas as pd
import selectors,types
import os, pathlib
from bronkhorstControlbm31.bronkhorstServer import PORT, HOST, logdir
import json
import logging
import numpy as np

homedir = pathlib.Path.home()
#logdir = 'bronkhorstLogger'
fulllogdir = f'{homedir}/{logdir}'
os.makedirs(fulllogdir,exist_ok=True)
logger = logging.getLogger()




def connect(host=HOST, port=PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host,port))
    return s

class MFCclient():
    def __init__(self,address, host=HOST,port=PORT, connid = socket.gethostname(),multi=True):
        self.address = address
        self.host = host
        self.port = port
        self.connid = connid
        self.multi = multi
        self.types = {'fMeasure': float, 'address':np.uint8, 'fSetpoint':float, 'Setpoint_pct':float, 'Measure_pct':float, 
                      'Valve output': float, 'Fluidset index': np.uint8,  'Control mode':np.uint8, 'Setpoint slope': int}
    def strToBool(self,string):
        if string == 'True' or string == 'False':
            return string == 'True'
        return string
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
    def writeName(self,newname):
        string = self.makeMessage(self.address,'writeName',newname)
        data = self.sendMessage(string)
        return data
    def readParam(self, name):
        string = self.makeMessage(self.address, 'readParam', name)
        data = self.sendMessage(string)
        return data
    def readParams(self,*names):
        string = self.makeMessage(self.address, 'readParams_names', *names)
        data = self.sendMessage(string)
        datadct = json.loads(data)
        return datadct
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
        return self.strToBool(data)
    def writeSetpoint(self,value):
        string = self.makeMessage(self.address, 'writeSetpoint', value)
        data = self.sendMessage(string)
        return float(data)
    def readControlMode(self):
        string = self.makeMessage(self.address, 'readControlMode')
        data = self.sendMessage(string)
        return int(data)
    def writeControlMode(self,value):
        string = self.makeMessage(self.address, 'writeControlMode',value)
        data = self.sendMessage(string)
        return int(data)
    def readFluidType(self):
        string = self.makeMessage(self.address, 'readFluidType')
        data = self.sendMessage(string)
        datadct = json.loads(data)
        return datadct
    def writeFluidIndex(self,value):
        string = self.makeMessage(self.address, 'writeFluidIndex',value)
        data = self.sendMessage(string)
        return json.loads(data)
    def readMeasure_pct(self):
        string = self.makeMessage(self.address,'readMeasure_pct')
        data = self.sendMessage(string)
        return float(data)
    def readSetpoint_pct(self):
        string = self.makeMessage(self.address,'readSetpoint_pct')
        data = self.sendMessage(string)
        return float(data)
    def readValve(self):
        string = self.makeMessage(self.address,'readValve')
        data = self.sendMessage(string)
        return float(data)
    def readSlope(self):
        string = self.makeMessage(self.address,'readSlope')
        data = self.sendMessage(string)
        return int(data)
    def writeSlope(self,value):
        string = self.makeMessage(self.address,'writeSlope',value)
        data = self.sendMessage(string)
        return int(data)
    def writeSP_slope(self,sp,slope):
        string = self.makeMessage(self.address,'writeSP_slope',sp, slope)
        data = self.sendMessage(string)
        return json.loads(data)
        
    def pollAll(self):
        string = self.makeMessage(self.address, 'pollAll')
        data = self.sendMessage(string)
        datalines = data.split('\n')
        columns = datalines[0].split(';')
        array = [[i for i in line.split(';')] for line in datalines[1:] if line]
        df = pd.DataFrame(data = array,columns=columns)
        df = df.astype(self.types)
        return df
    
    def pollAll2(self):
        string = self.makeMessage(self.address,'readParams_allAddsPars')
        data = self.sendMessage(string)
        datadct = json.loads(data)
        df = pd.DataFrame.from_dict(datadct)
        df['Measure'] = df['Measure'].apply(lambda x: x*100/32000)
        df['Setpoint'] = df['Setpoint'].apply(lambda x: x*100/32000)
        df['Valve output'] = df['Valve output'].apply(lambda x: x/2**24)
        df = df.rename({'Measure':'Measure_pct', 'Setpoint':'Setpoint_pct'}, axis = 1)
        df = df.astype(self.types)
        return df

    def testMessage(self):
        string = self.makeMessage(self.address,'testMessage')
        data = self.sendMessage(string)
        return data

    def wink(self):
        string = self.makeMessage(self.address,'wink')
        data = self.sendMessage(string)
        return data
    def sendMessage(self,message):
        bytemessage = bytes(message,encoding='utf-8')
        if not self.multi:
            self.s = connect(self.host,self.port)
            self.s.sendall(bytemessage)
            data = self.s.recv(1024)
            self.s.close()
            strdata = data.decode()
            strdata = strdata.replace('!','')
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
        sock.settimeout(5)
        #sock.setblocking(False)
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
        except Exception as e:
            logger.exception(e)
            raise e
        finally:
            sel.close()
        return receivedMessage

    def service_connection(self,key, mask,sel):
        sock = key.fileobj
        data = key.data
        receivedMessage = b''
        strMessage = '!'
        if mask & selectors.EVENT_READ:
            while True:
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
                    return
                
            
        if mask & selectors.EVENT_WRITE:
            if not data.outb and data.messages:
                data.outb = data.messages.pop(0)
            if data.outb:
                print(f"Sending {data.outb} to connection {data.connid}")
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]

