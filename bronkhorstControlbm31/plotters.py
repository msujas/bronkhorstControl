from bronkhorstControlbm31.bronkhorstServer import PORT, HOST, logdir
from bronkhorstControlbm31.bronkhorstClient import MFCclient
import argparse
import matplotlib.pyplot as plt
import logging, pathlib, os, time
import socket
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.rcParams.update({'font.size':12})

homedir = pathlib.Path.home()
fulllogdir = f'{homedir}/{logdir}'
os.makedirs(fulllogdir,exist_ok=True)
logger = logging.getLogger()

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
    '''
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
    if title1:
        ax1.set_ylabel('MFC/BPR flow')
    '''

    p1 = ax1.bar(df['User tag'].values, df['fMeasure'].values)
    p2 = ax2.bar(df['User tag'].values, df['fSetpoint'].values)
    ax1.bar_label(p1, fmt = '%.3f')
    ax2.bar_label(p2, fmt = '%.3f')
    if title1:
        ax1.set_ylabel('MFC/BPR measure')
    if title2:
        ax2.set_ylabel('MFC/BPR setpoint')

    

def barPlot(host=HOST, port = PORT,waittime = 1, multi = True, connid = f'{socket.gethostname()}barplot'):
    host,port,connid, waittime, _, _log, _li =getArgs(host=host,port=port,connid=connid, waitTime=waittime,plotTime=1, log = False)
    fig,ax = plt.subplots(2,1)

    while True:
        try:
            df = MFCclient(1,host,port,multi=multi, connid=connid).pollAll()
            barPlotSingle(df,ax[0], ax[1])
            plt.tight_layout()
            plt.show(block = False)
            plt.pause(waittime)
            ax[0].cla()
            ax[1].cla()
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
    xlims = xlim*60
    userTags = df['User tag'].to_list()
    if tlist[-1] -tlist[0] > xlims:
        tlist.pop(0)
    for i in df.index.values:
        measure[i].append(df.loc[i][colName])
        while len(measure[i]) > len(tlist):
            measure[i].pop(0)

    tlistPlot = [t-tlist[-1] for t in tlist] 
    for a in measure:
        ax.plot(tlistPlot,measure[a],'o-',label = userTags[a],markersize = 3)
    if title:
        dt = datetime.fromtimestamp(tlist[-1])
        dtstring = f'{dt.year:04d}/{dt.month:02d}/{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}'
        ax.set_title(f'measure, tscale: {xlim} minutes. Updated: {dtstring}')
    ax.legend()
    if xlabel:
        ax.set_xlabel('t-current time (s)')
    ax.set_ylabel(ylabel)

def getLogFile():
    
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

def timePlot(host=HOST, port = PORT,waittime = 1, multi = True, connid = f'{socket.gethostname()}timePlot',xlim = 60, log = True, logInterval = 5):
    host,port,connid, waittime, xlim, log, logInterval = getArgs(host=host,port=port,connid=connid, waitTime=waittime,plotTime=xlim, log = log, logInterval=logInterval)
    measure = {}
    c=0
    fig,ax = plt.subplots()
    tlist = []
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
            timePlotSingle(df,ax,measure, tlist, xlim)

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

def plotAllSingle(df, tlist, fig, ax, measureFlow, measureValve,xlim, waittime = 1,  log=False, logfile =None,tlog=None, logInterval=0, headerString=''):
    
    tlist.append(time.time())
    barPlotSingle(df,ax[0,1], ax[1,1], title1=True)

    timePlotSingle(df,ax[0,0],measureFlow,tlist,xlim, xlabel=True)

    if log and time.time() - tlog > logInterval:
        logMFCs(logfile, df, headerString)

    timePlotSingle(df,ax[1,0], measureValve, tlist, xlim, colName='Valve output', ylabel='MFC/BPR valve output',
                    title=False)
    plt.tight_layout()
    
    plt.show()
    plt.pause(waittime)
    #time.sleep(waittime)
    ax[0,0].cla()
    ax[1,0].cla()
    ax[0,1].cla()
    ax[1,1].cla()

def plotAll(host=HOST, port = PORT,waittime = 1, multi = True, connid = f'{socket.gethostname()}allPlot',xlim = 60, log = True, logInterval = 5):
    host,port,connid, waittime, xlim, log, logInterval = getArgs(host=host,port=port,connid=connid, 
                                                                 waitTime=waittime,plotTime=xlim, log = log, logInterval=logInterval)
    eventlogfile = f'{homedir}/{logdir}/mfcPlotAll.log'
    logging.basicConfig(filename=eventlogfile, level = logging.INFO, format = '%(asctime)s %(levelname)-8s %(message)s',
                        datefmt = '%Y/%m/%d_%H:%M:%S')
    logger.info('mfcPlotAll started')
    plt.ion()
    fig, ax = plt.subplots(2,2)
    #plt.delaxes(ax[1,0])
    measureFlow = {}
    measureValve = {}
    c=0
    tlist = []
    if log:
        logfile = getLogFile()
    tlog = 0
    
    while True:
        try:
            df = MFCclient(1,host,port, connid=connid).pollAll()
            if c == 0:
                for i in df.index.values:
                    measureFlow[i] = []
                    measureValve[i] = []
                c=1
                if log:
                    headerString = logHeader(logfile,df)
            plotAllSingle(df,tlist,fig,ax,measureFlow, measureValve,xlim, waittime=waittime,  log = log, logfile=logfile, tlog=tlog,
                          logInterval=logInterval, headerString=headerString)
            
        except KeyboardInterrupt:
            logger.info('keyboard interrupt')
            plt.close(fig)
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