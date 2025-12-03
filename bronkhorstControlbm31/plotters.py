from bronkhorstControlbm31.bronkhorstServer import PORT, HOST, logdir
from bronkhorstControlbm31.bronkhorstClient import MFCclient
import argparse
import matplotlib.pyplot as plt
import logging, pathlib, os, time
import socket
from datetime import datetime
import numpy as np
import matplotlib
from matplotlib.widgets import CheckButtons
import pandas as pd
matplotlib.rcParams.update({'font.size':12})

homedir = pathlib.Path.home()
fulllogdir = f'{homedir}/{logdir}'
os.makedirs(fulllogdir,exist_ok=True)
logger = logging.getLogger()
clientlogdir = f'{homedir}/bronkhorstClientLog/'
def getArgs(host=HOST, port=PORT, connid = socket.gethostname(),waitTime = 0.5, plotTime = 60, log = True, logInterval = 5):
    parser = argparse.ArgumentParser()

    parser.add_argument('host',nargs='?', default=host, type= str, help = 'host name/address')
    parser.add_argument('-p','--port',default=port, type=int, help = 'port number')
    parser.add_argument('-c','--connid',default=connid, type = str, help='name for connection')
    parser.add_argument('-wt','--waittime',default=waitTime, type = float, help = 'time to wait between iterations (default 0.5 s)')
    parser.add_argument('-pt','--plotTime',default=plotTime, type = float, 
                        help = 'timePlot only. Total time to plot on x-axis (only for timePlot, default 60 minutes)')
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

def barPlotSingle(df, ax1, ax2, title1 = True, title2=True):
    ax1.cla()
    ax2.cla()
    p1 = ax1.bar(df['User tag'].values, df['fMeasure'].values)
    p2 = ax2.bar(df['User tag'].values, df['fSetpoint'].values)
    ax1.bar_label(p1, fmt = '%.3f')
    ax2.bar_label(p2, fmt = '%.3f')
    if title1:
        ax1.set_ylabel('MFC/BPR measure')
    if title2:
        ax2.set_ylabel('MFC/BPR setpoint')

def barplotSingleCombined(df,ax1, title=True):
    basefontsize = 15
    width = 0.45
    mult = 1
    x = df.index.values
    fontsize = int(basefontsize-len(x)*0.7)
    p1 = ax1.bar(x , df['fSetpoint'].values, width, label = 'fSetpoint')
    ax1.bar_label(p1, fmt = '%.2f', padding = 3, fontsize = fontsize)
    p2 = ax1.bar(x+width*mult, df['fMeasure'].values, width, label = 'fMeasure')
    ax1.bar_label(p2, fmt = '%.2f', padding = 3, fontsize = fontsize)
    ax1.legend()
    ax1.set_xticks(x+width*mult*0.5, df['User tag'].values)
    if title:
        ax1.set_ylabel('MFC/BPR flow')

def barPlot(host=HOST, port = PORT,waittime = 1, multi = True, connid = f'{socket.gethostname()}barplot', combined = False):
    host,port,connid, waittime, _, _log, _li =getArgs(host=host,port=port,connid=connid, waitTime=waittime,plotTime=1, log = False)
    nrows = (1-combined) +1

    fig,ax = plt.subplots(nrows,1)

    while True:
        try:
            df = MFCclient(1,host,port,multi=multi, connid=connid).pollAll()
            if combined:
                barplotSingleCombined(df,ax)
            else:
                barPlotSingle(df,ax[0], ax[1])
            plt.tight_layout()
            plt.show(block = False)
            plt.pause(waittime)
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
    return headerString

def getLogFile(host, port = PORT, direc = clientlogdir):
    t = time.time()
    dt = datetime.fromtimestamp(t)
    dtstring = f'{dt.year:04d}{dt.month:02d}{dt.day:02d}'
    logfile = f'{direc}/{dtstring}_{host}_{port}.log'
    if not os.path.exists(direc):
        os.makedirs(direc)
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

def timePlotSingle(df, ax, measure, tlist, xlim, colName = 'fMeasure', ylabel = 'MFC/BPR measure', title = True, xlabel = True, resetAxes = False):
    xlims = xlim*60

    userTags = df['User tag'].to_list()
    if tlist[-1] -tlist[0] > xlims:
        tlist.pop(0)
    for i in df.index.values:
        measure[i].append(df.loc[i][colName])
        while len(measure[i]) > len(tlist):
            measure[i].pop(0)
    tlistPlot = [t-tlist[-1] for t in tlist] 
    
    xlimzoom = ax.get_xbound()
    ylimzoom = ax.get_ybound()

    ax.cla()
    for a in measure:
        ax.plot(tlistPlot,measure[a],'o-',label = userTags[a],markersize = 3)
    if title:
        dt = datetime.fromtimestamp(tlist[-1])
        dtstring = f'{dt.year:04d}/{dt.month:02d}/{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}'
        ax.set_title(f'measure, tscale: {xlim} minutes. Updated: {dtstring}')

    if len(tlist) > 2 and xlimzoom[0] > tlistPlot[2] and not resetAxes:
        ax.set_xbound(*xlimzoom)
        ax.set_ybound(*ylimzoom)
    ax.legend()
    if xlabel:
        ax.set_xlabel('t-current time (s)')
    ax.set_ylabel(ylabel)

def timePlot(host=HOST, port = PORT,waittime = 1, multi = True, connid = f'{socket.gethostname()}timePlot',xlim = 60, log = True, logInterval = 5):
    host,port,connid, waittime, xlim, log, logInterval = getArgs(host=host,port=port,connid=connid, waitTime=waittime,plotTime=xlim, log = log, logInterval=logInterval)
    measure = {}
    c=0
    fig,ax = plt.subplots()
    tlist = []
    if log:
        logfile = getLogFile(host,port)
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
            timePlotSingle(df,ax,measure, tlist, xlim)

            if log and time.time() - tlog > logInterval:
                headerString = logMFCs(logfile,df, headerString)
                tlog = time.time()
                
            plt.tight_layout()
            plt.show(block = False)
            plt.pause(waittime)
        except (KeyboardInterrupt,AttributeError):
            plt.close(fig)
            return
        
def plotValvesBar(df, ax):
    p1 = ax.bar(df['User tag'].values, df['Valve output'].values)
    ax.bar_label(p1, fmt = '%.2f')
    ax.set_ylabel('MFC/BPR Measure')


class Plotter():
    def __init__(self,host=HOST, port = PORT,waittime = 1, connid = f'{socket.gethostname()}allPlot',xlim = 60, 
                 log = True, logInterval = 20):
        self.host = host
        self.port = port
        self.waittime = waittime
        self.connid = connid
        self.xlim = xlim
        self.log = log
        self.logInterval = logInterval
        self.fig, self.ax = plt.subplots(2,2)
        plt.ion()
        self.measureFlow = {}
        self.measureValve = {}
        self.tlist = []
        
        self.logfile = getLogFile(self.host,self.port)
        self.tlog = 0
        self.mfcclient = MFCclient(1,self.host,self.port, connid=self.connid)
        df = self.mfcclient.pollAll()
        self.fmeas = df['fMeasure'].values
        self.fsp = df['fSetpoint'].values
        if self.log:
            self.headerString = logHeader(self.logfile,df)
        axes = plt.axes([0.001, 0.0001, 0.08, 0.05])
        axes.axis('off')
        self.radiobutton = CheckButtons(axes, ['reset axes'],[False])
        for i in df.index.values:
            self.measureFlow[i] = []
            self.measureValve[i] = []
        self.fig.show()
    def plotAll(self):
        eventlogfile = f'{homedir}/{logdir}/mfcPlotAll.log'
        logging.basicConfig(filename=eventlogfile, level = logging.INFO, format = '%(asctime)s %(levelname)-8s %(message)s',
                            datefmt = '%Y/%m/%d_%H:%M:%S')
        logger.info('mfcPlotAll started')
        
        while True:
            try:
                df = self.mfcclient.pollAll()
                self.plotAllSingle(df)
                plt.pause(self.waittime)
                
            except KeyboardInterrupt:
                logger.info('keyboard interrupt')
                plt.close(self.fig)
                return
            except AttributeError as e:
                logger.error(f'{e}, possible keyboard interrupt during connection')
                return
            except OSError as e:
                message = f'{e}.\nbronkhorstServer is probably not open, or host or port settings are incorrect'
                print(message)
                logger.error(message)
                return
            except ConnectionResetError as e:
                message = f'{e}.\nbronkhorstServer likely closed while running'
                logger.error(message)
                print(message)
                return
            except np.core._exceptions._UFuncNoLoopError as e:
                logger.warning(e)
                continue
            except Exception as e:
                logger.exception(e)
                raise e
    def plotAllSingle(self,df):
        self.tlist.append(time.time())
        self.resetAxes = self.radiobutton.get_status()[0]

        barPlotSingle(df,self.ax[0,1], self.ax[1,1], title1=True)

        timePlotSingle(df,self.ax[0,0],self.measureFlow,self.tlist,self.xlim, xlabel=True, resetAxes=self.resetAxes)
        measDiff = np.max(np.abs(df['fMeasure'].values - self.fmeas))
        spchange = (df['fSetpoint'].values != self.fsp).any()
        if self.log and (time.time() - self.tlog > self.logInterval or measDiff > 0.2 or spchange):
            self.headerString = logMFCs(self.logfile, df, self.headerString)
            self.tlog = time.time()
            self.fmeas = df['fMeasure'].values
            self.fsp = df['fSetpoint'].values

        timePlotSingle(df,self.ax[1,0], self.measureValve, self.tlist, self.xlim, colName='Valve output', ylabel='MFC/BPR valve output',
                        title=False, resetAxes=self.resetAxes)

        plt.subplots_adjust(top = 0.95, bottom = 0.07, right = 0.99, left = 0.1, 
            hspace = 0.2, wspace = 0.2)

import matplotlib.dates as mdates

def logplotargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type = str, help = 'name of log file to plot')
    args = parser.parse_args()
    filename = args.filename
    return filename

def logPlotter(logfile = None):
    if not logfile:
        logfile = logplotargs()
    f = open(logfile, 'r')
    lines = f.readlines()
    f.close()
    skiplines = [i for i in range(len(lines)) if 'datetime' in lines[i]]
    header = lines[skiplines[-1]]
    header = header.split()
    df = pd.read_csv(logfile, skiprows=skiplines, header = None, sep = ' ')
    df.columns = header
    fig,ax = plt.subplots(1,dpi = 150)
    xfmt = mdates.DateFormatter('%Y-%m-%d %H:%M:%S')
    ax.xaxis.set_major_formatter(xfmt)
    time = df['unixTime(s)'].values
    dt = np.array([datetime.fromtimestamp(t) for t in time])
    plotCols = [col for col in df.columns if 'Measure' in col]
    for c in plotCols:
        ax.plot(dt, df[c].values, 'o-', label = c.replace('Measure',''), markersize = 2)
    ax.legend()
    ax.set_ylabel('MFC/BPR measure')
    ax.set_xlabel('date time')
    ax.tick_params(axis = 'x', labelrotation = 90, labelsize = 10)
    plt.tight_layout()
    plt.show()




def plotAll(host = HOST, port = PORT, connid = f'{socket.gethostname()}allPlot', xlim = 60, log = True, 
            logInterval = 5, waittime = 0.5):
    host,port,connid,waittime, xlim, log, logInterval = getArgs(host=host,port=port,connid=connid, waitTime=waittime,plotTime=xlim, 
                                                                log = log, logInterval=logInterval)
    plotter = Plotter(host=host, port = port,waittime = waittime, connid = connid,xlim = xlim, log = log, logInterval = logInterval)
    plotter.plotAll()
