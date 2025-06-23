import socket
import pandas as pd
import matplotlib.pyplot as plt
import selectors,types
import matplotlib
matplotlib.rcParams.update({'font.size':14})
import time
from datetime import datetime
import argparse
import os, pathlib
from bronkhorstControlbm31.bronkhorstServer import PORT, HOST
from PyQt6 import QtCore


def getArgs(host=HOST, port=PORT, connid = socket.gethostname(),waitTime = 0.5, plotTime = 1, log = True, logInterval = 5):
    parser = argparse.ArgumentParser()

    parser.add_argument('host',nargs='?', default=host, type= str, help = 'host name/address')
    parser.add_argument('-p','--port',default=port, type=int, help = 'port number')
    parser.add_argument('-c','--connid',default=connid, type = str, help='name for connection')
    parser.add_argument('-wt','--waittime',default=waitTime, type = float, help = 'time to wait between iterations (default 0.5 s)')
    parser.add_argument('-pt','--plotTime',default=plotTime, type = float, 
                        help = 'timePlot only. Total time to plot on x-axis (only for timePlot, default 1 hour)')
    parser.add_argument('-l','--log', default = log, type = bool, 
                        help='timePlot only, boolean. Whether or not to log the data (default True, file saved in <homedir>/bronkhorstClientLog/<yyyymmdd>.log)')
    parser.add_argument('-li', '--logInterval', default = logInterval, type = int, help='timePlot only. Integer, time interval between each log entry (default 5 s)')
    args = parser.parse_args()

    host = args.host
    port = args.port
    connid = args.connid
    waitTime = args.waittime
    plotTime = args.plotTime
    log = args.log
    logInterval = args.logInterval

    print(host)
    print(port)
    print(connid)
    return host, port, connid, waitTime, plotTime, log, logInterval

def connect(host=HOST, port=PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host,port))
    return s

class MFCclient():
    def __init__(self,address, host=HOST,port=PORT, multi=True,connid = socket.gethostname()):
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
        return int(data)
    def writeControlMode(self,value):
        string = self.makeMessage(self.address, 'writeControlMode',value)
        data = self.sendMessage(string)
        return data
    def readFluidType(self):
        string = self.makeMessage(self.address, 'readFluidType')
        data = self.sendMessage(string)
        data = data.replace('(','').replace(')','').replace('\'','')
        datasplit = data.split(',')
        index = int(datasplit[1])
        name = datasplit[0]
        return index, name
    def writeFluidIndex(self,value):
        string = self.makeMessage(self.address, 'writeFluidIndex',value)
        data = self.sendMessage(string)
        return data
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
    def strToData(self,datastring : str):
        if datastring.isdigit():
            return int(datastring)
        elif datastring.replace('.','',1).isdigit():
            return float(datastring)
        else:
            return datastring
    def pollAll(self):
        string = self.makeMessage(self.address, 'pollAll')
        data = self.sendMessage(string)
        datalines = data.split('\n')
        columns = datalines[0].split(';')
        array = [[self.strToData(i) for i in line.split(';')] for line in datalines[1:] if line]
        df = pd.DataFrame(data = array,columns=columns)
        df = df.astype({'address':'int8'})
        return df
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

'''
class Worker(QtCore.QThread):
    outputs = QtCore.pyqtSignal(list)
    def __init__(self, host, port):
        super(Worker,self).__init__()
        self.host = host
        self.port = port
    def run(self):
        while True:
            df = MFCclient(1,self.host,self.port).pollAll()
            self.outputs.emit(df)
    def stop(self):
        self.terminate()
def getdf(df):
    print(df)

def startWorker(host=HOST,port=PORT):
    thread = Worker(host,port)
    thread.start()
    thread.outputs.connect(getdf)
'''

import threading
def gettmpDFfile():
    homedir = pathlib.Path.home()
    filedir = f'{homedir}/bronkhorstClientLog/'
    return f'{filedir}/tmpdf.txt'

def getdf(host,port):
    df = MFCclient(1,host,port).pollAll()
    df.to_csv(gettmpDFfile(),sep = ';', index=False)
    return df

def getdfThread(host,port=PORT, connid= socket.gethostname()):
    t = threading.Thread(target=getdf, args = (host,port))
    t.start()
    t.join()
    fname = gettmpDFfile()
    df = pd.read_csv(fname,sep=';')
    return df

def barPlotSingle(df, ax1,ax2, title1 = True, title2 = True):
    p1 = ax1.bar(df['User tag'].values, df['fMeasure'].values)
    p2 = ax2.bar(df['User tag'].values, df['fSetpoint'].values)
    ax1.bar_label(p1, fmt = '%.2f')
    ax2.bar_label(p2, fmt = '%.2f')
    if title1:
        ax1.set_ylabel('MFC/BPR Measure')
    if title2:
        ax2.set_ylabel('MFC/BPR Setpoint')


def barPlot(host=HOST, port = PORT,waittime = 1, multi = True, connid = 'plotLoop'):
    host,port,connid, waittime, _, _log, _li =getArgs(host=host,port=port,connid=connid, waitTime=waittime,plotTime=1, log = False)
    fig,(ax1,ax2) = plt.subplots(2,1)

    while True:
        try:
            df = MFCclient(1,host,port,multi=multi, connid=connid).pollAll()
            #df = getdfThread(host,port,connid)
            barPlotSingle(df,ax1,ax2)
            plt.tight_layout()
            plt.show(block = False)
            plt.pause(waittime)
            #time.sleep(waittime)
            ax1.cla()
            ax2.cla()
        except (KeyboardInterrupt, AttributeError) as e:
            print(e)
            plt.close(fig)
            return
        
def writeLog(file,string):
    f = open(file,'a')
    f.write(string)
    f.close()

def logMFCs(logfile, df, headerString):
    curtime = time.time()
    dt = datetime.fromtimestamp(curtime)
    dtstring = f'{dt.year:04d}/{dt.month:02d}/{dt.day:02d}_{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}'
    logString = f'{dtstring} {int(curtime)}'
    newHeaderString = f'datetime unixTime(s)'
    for i in df.index.values:
        name = df.loc[i]['User tag'].replace(' ','')
        newHeaderString += f' {name}Setpoint {name}Measure'
        meas = df.loc[i]['fMeasure']
        sp = df.loc[i]['fSetpoint']
        logString += f' {sp:.3f} {meas:.3f}'
    newHeaderString += '\n'
    logString += '\n'                 
    if newHeaderString != headerString:
        headerString = newHeaderString
        writeLog(logfile,headerString)
    writeLog(logfile,logString)


def timePlotSingle(df, ax, measure, tlist, xlim, colName = 'fMeasure', ylabel = 'MFC/BPR measure', title = True, xlabel = True):
    xlims = xlim*3600
    userTags = df['User tag'].to_list()
    for i in df.index.values:
        measure[i].append(df.loc[i][colName])
        if tlist[-1] -tlist[0] > xlims:
            measure[a].pop(0)

    tlistPlot = [t-tlist[-1] for t in tlist] 
    for a in measure:
        ax.plot(tlistPlot,measure[a],'o-',label = userTags[a],markersize = 3)
    if title:
        ax.set_title(f'measure, tscale: {xlim} hours')
    ax.legend()
    if xlabel:
        ax.set_xlabel('t-current time (s)')
    ax.set_ylabel(ylabel)

def getLogFile():
    homedir = pathlib.Path.home()
    logdir = f'{homedir}/bronkhorstClientLog/'
    t = time.time()
    dt = datetime.fromtimestamp(t)
    dtstring = f'{dt.year:04d}{dt.month:02d}{dt.day:02d}'
    logfile = f'{logdir}/{dtstring}.log'
    if not os.path.exists(logdir):
        os.makedirs(logdir)
    return logfile

def logHeader(logfile, df):
    names = []
    headerString = f'datetime unixTime(s)'
    for i in df.index.values:
        name = df.loc[i]['User tag'].replace(' ','_')
        names.append(name)
        headerString += f' {name}Setpoint {name}Measure'
    headerString += '\n'
    writeLog(logfile,headerString)
    return headerString

def timePlot(host=HOST, port = PORT,waittime = 1, multi = True, connid = 'timePlot',xlim = 1, log = True, logInterval = 5):
    host,port,connid, waittime, xlim, log, logInterval = getArgs(host=host,port=port,connid=connid, waitTime=waittime,plotTime=xlim, log = log, logInterval=logInterval)
    measure = {}
    c=0
    fig,ax = plt.subplots()
    tlist = []
    xlims = xlim*3600
    if log:
        logfile = getLogFile()
    tlog = 0

    while True:
        try:
            tlist.append(time.time())
            df = MFCclient(1,host,port,multi=multi, connid=connid).pollAll()
            df = df.astype({'fMeasure':float})
            if c == 0:
                for i in df.index.values:
                    measure[i] = []
                c = 1
                if log:
                    headerString = logHeader(logfile, df)
            timePlotSingle(df,ax,measure, tlist, xlims)
            if tlist[-1] -tlist[0] > xlims:
                tlist.pop(0)
            if log and time.time() - tlog > logInterval:
                logMFCs(logfile,df, headerString)
                tlog = time.time()
                
            plt.tight_layout()
            plt.show(block = False)
            plt.pause(waittime)
            ax.cla()
        except (KeyboardInterrupt,AttributeError):
            plt.close(fig)
            return
        
def plotValvesBar(df, ax):
    p1 = ax.bar(df['User tag'].values, df['Valve output'].values)
    ax.bar_label(p1, fmt = '%.2f')
    ax.set_ylabel('MFC/BPR Measure')


        
def plotAll(host=HOST, port = PORT,waittime = 1, multi = True, connid = 'allPlot',xlim = 1, log = True, logInterval = 5):
    host,port,connid, waittime, xlim, log, logInterval = getArgs(host=host,port=port,connid=connid, 
                                                                 waitTime=waittime,plotTime=xlim, log = log, logInterval=logInterval)
    plt.ion()
    xlims = xlim*3600
    fig, ax = plt.subplots(2,2, width_ratios=[1.3,1], gridspec_kw={'wspace': 0.15, 'hspace':0.15})
    #fig.delaxes(ax[1,0])
    df = MFCclient(1,host,port).pollAll()
    measureFlow = {}
    measureValve = {}
    c=0
    tlist = []
    if log:
        logfile = getLogFile()
    tlog = 0
    while True:
        try:
            tlist.append(time.time())
            df = MFCclient(1,host,port).pollAll()
            barPlotSingle(df,ax[0,1], ax[1,1], title1=False)
            if c == 0:
                for i in df.index.values:
                    measureFlow[i] = []
                    measureValve[i] = []

                c=1
                if log:
                    headerString = logHeader(logfile,df)
            timePlotSingle(df,ax[0,0],measureFlow,tlist,xlim, xlabel=False)

            if log and time.time() - tlog > logInterval:
                logMFCs(logfile, df, headerString)

            #plt.tight_layout()
            #plotValvesBar(df,ax[1,0])
            timePlotSingle(df,ax[1,0], measureValve, tlist, xlim, colName='Valve output', ylabel='MFC/BPR valve output',
                           title=False)
            if tlist[-1] -tlist[0] > xlims:
                tlist.pop(0)
            plt.show(block = False)
            plt.pause(waittime)
            #time.sleep(waittime)
            ax[0,0].cla()
            ax[1,0].cla()
            ax[0,1].cla()
            ax[1,1].cla()
        except (KeyboardInterrupt, AttributeError):
            plt.close(fig)
            return






    
