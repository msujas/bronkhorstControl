import socket
import pandas as pd
import matplotlib.pyplot as plt
import selectors,types
import matplotlib
matplotlib.rcParams.update({'font.size':14})
import time 

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
    def writeName(self,newname):
        string = self.makeMessage(self.address,'writeName',newname)
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
        array = [[float(i) if i.replace('.','',1).isdigit() else i for i in line.split(';')] for line in datalines[1:] if line]
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
            ax1.set_ylabel('MFC/BPR Measure')
            ax2.set_ylabel('MFC/BPR Setpoint')
            df = MFCclient(1,host,port,multi=multi, connid=connid).pollAll()
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

def timePlot(host, port = PORT,waittime = 1, multi = True, connid = 'timePlot',xlim = 1):
    measure = {}
    c=0
    fig,ax = plt.subplots()
    tlist = []
    xlims = xlim*3600
    while True:
        try:
            tlist.append(time.time())
            df = MFCclient(1,host,port,multi=multi, connid=connid).pollAll()

            if c == 0:
                for ut in df['User tag'].values:
                    measure[ut] = []
                c = 1

            for ut in measure:
                measure[ut].append(df[df['User tag'] == ut]['fMeasure'])
                if tlist[-1] -tlist[0] > xlims:
                    measure[ut].pop(0)
            if tlist[-1] -tlist[0] > xlims:
                tlist.pop(0)
            tlistPlot = [t-tlist[-1] for t in tlist]
            for ut in measure:
                ax.plot(tlistPlot,measure[ut],'o-',label = ut,markersize = 3)
            ax.set_title(f'measure, tscale: {xlim} hours')
            ax.legend()
            ax.set_xlabel('t-current time (s)')
            ax.set_ylabel('MFC/BPR measure')

            plt.tight_layout()
            plt.show(block = False)
            plt.pause(waittime)
            ax.cla()
        except KeyboardInterrupt:
            plt.close(fig)
            break
    
