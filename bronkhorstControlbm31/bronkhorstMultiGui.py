from PyQt6 import QtCore,QtWidgets, QtGui
import pandas as pd
from .bronkhorstClient import MFCclient
from .bronkhorstServer import PORT, homedir, logdir
from .guiLayout import CommonFunctions
from .bronkhorstGui import parseArguments
import time
from .plotters import clientlogdir, Plotter, getLogFile, logHeader
import logging, socket, os

logger = logging.getLogger()

class MultiWorker(QtCore.QObject):
    outputs = QtCore.pyqtSignal(pd.DataFrame)
    def __init__(self,hosts,ports, waittime = 1):
        super(MultiWorker,self).__init__()

        self.hosts = hosts
        self.ports=ports
        self.waittime = waittime
        self.dfs = {}
        self.mfcs = {}
        for i in range(len(self.hosts)):
            self.mfcs[i] = MFCclient(1, self.hosts[i],self.ports[i])
    def run(self):
        self.running = True
        while self.running:
            self.runOnce()
            time.sleep(self.waittime)
        print('stopped polling')
    def stop(self):
        self.running=False 

    def runOnce(self):
        try:
            for i in range(len(self.hosts)):
                self.dfs[i] = self.mfcs[i].pollAll()
                self.dfs[i]['host'] = [self.hosts[i]]*len(self.dfs[i].index.values)
                self.dfs[i]['port'] = [self.ports[i]]*len(self.dfs[i].index.values)
            dfAll = pd.concat([self.dfs[i] for i in self.dfs], axis=0, ignore_index=True)
            
        except (OSError, AttributeError, ConnectionResetError):
            message = "connection to server lost. Stopping polling"
            print(message)
            logger.warning(message)
            self.outputs.emit(pd.DataFrame())
            return
        except KeyError:
            message = 'no data returned. Stopping'
            print(message)
            logger.warning(message)
            self.outputs.emit(pd.DataFrame())
            return
        except Exception as e:
            logger.exception(e)
            raise e
        self.outputs.emit(dfAll)         

class MultiServerGui(QtWidgets.QMainWindow, CommonFunctions):
    def __init__(self):
        super().__init__()
        eventlogfile = f'{homedir}/{logdir}/multigui.log'
        logging.basicConfig(filename=eventlogfile, level = logging.INFO, format = '%(asctime)s %(levelname)-8s %(message)s',
                            datefmt = '%Y/%m/%d_%H:%M:%S')
        self.centralWidget = QtWidgets.QWidget()
        self.centralWidget.setObjectName("centralWidget")
        self.setWindowTitle('bronkhorst multi server GUI')
        curpath = os.path.dirname(os.path.realpath(__file__))
        iconfile = f'{curpath}/images/drawingMulti.ico'
        icon = QtGui.QIcon(iconfile)
        self.setWindowIcon(icon)
        self.connid = f'{socket.gethostname()}GUI'
        self.maxMFCs = parseArguments()
        self.running = False
        self.rows = {'wink':0,
                'host':1,
                'port':2,
                'address':3,
                'slope':4,
                'setpoint':5,
                'measure':6,
                'setpointpct':7,
                'measurepct':8,
                'valve':9,
                'controlMode':10,
                'fluidIndex':11,
                'fluidName':12,
                'writesp':13,
                'usertag':14}
        super().guiLayout()
        self.portInput = QtWidgets.QLineEdit()
        self.portInput.setObjectName('portInput')
        self.portInput.setMinimumWidth(120)
        self.portInput.setText(str(PORT))
        self.bottomLayout.addWidget(self.portInput,0,2)

        self.hostBoxes = {}
        self.portBoxes = {}
        for i in range(self.maxMFCs):
            self.hostBoxes[i] = QtWidgets.QLineEdit()
            self.hostBoxes[i].setObjectName(f'hostBoxes{i}')
            self.hostBoxes[i].setEnabled(False)
            self.gridLayout.addWidget(self.hostBoxes[i], self.rows['host'],i+1)

            self.portBoxes[i] = QtWidgets.QSpinBox()
            self.portBoxes[i].setObjectName(f'portBoxes{i}')
            self.portBoxes[i].setEnabled(False)
            self.portBoxes[i].setMaximum(2**16)
            self.gridLayout.addWidget(self.portBoxes[i], self.rows['port'],i+1)
        
        self.hostBoxLabel = QtWidgets.QLabel()
        self.hostBoxLabel.setObjectName('hostBoxLabel')
        self.hostBoxLabel.setText('host name')
        self.leftLayout.addWidget(self.hostBoxLabel, self.rows['host'], 0)

        self.portBoxLabel = QtWidgets.QLabel()
        self.portBoxLabel.setObjectName('portBoxLabel')
        self.portBoxLabel.setText('port')
        self.leftLayout.addWidget(self.portBoxLabel, self.rows['port'],0)

        super().formatLayouts()

        self.centralWidget.setLayout(self.outerLayout)
        self.setCentralWidget(self.centralWidget)
        QtCore.QMetaObject.connectSlotsByName(self)
        self.startButton.clicked.connect(self.connectLoop)
        self.lockFluidIndex.stateChanged.connect(self.lockFluidIndexes)
        self.plotBox.stateChanged.connect(self.plotSetup)

    def repoll(self):
        pass
    def getAHP(self,i):
        address = self.addressLabels[i].value()
        host = self.hostBoxes[i].text()
        port = self.portBoxes[i].value()
        return address, host, port
    def wink(self, i):
        address, host, port = self.getAHP(i)
        MFCclient(address,host,port, connid=self.connid).wink()
    def setControlMode(self,i):
        if not self.running:
            return
        address, host, port = self.getAHP(i)
        value = self.controlBoxes[i].currentIndex()
        print(f'setting address {address} to control mode {value}')
        newmode = MFCclient(address, host,port, connid=self.connid).writeControlMode(value)
        self.controlBoxes[i].setCurrentIndex(newmode)
    def setFluidIndex(self,i):
        if not self.running:
            return
        address, host, port = self.getAHP(i)
        value = self.fluidBoxes[i].value()
        print(f'setting address {address} to fluid {value}')
        newfluid = MFCclient(address,host,port, connid=self.connid).writeFluidIndex(value)
        newfluidIndex = newfluid['Fluidset index']
        self.fluidBoxes[i].setValue(newfluidIndex)
    def setSlope(self,i):
        if not self.running:
            return
        address, host, port = self.getAHP(i)
        value = self.slopeBoxes[i].value()
        print(f'setting slope to {value} on address {address}')
        newslope = MFCclient(address,host,port,connid=self.connid).writeSlope(value)
        self.slopeBoxes[i].setValue(newslope)
    def setFlow(self,i):
        if not self.running:
            return
        value = self.writeSetpointBoxes[i].value()
        address, host, port = self.getAHP(i)
        print(f'setting flow to {value} on address {address}')
        newflow = MFCclient(address,host,port, connid=self.connid).writeSetpoint(value)
        self.writeSetpointBoxes[i].setValue(newflow)
    def setUserTag(self,i):
        if not self.running:
            return
        value = self.userTags[i].text()
        address, host, port = self.getAHP(i)
        print(f'setting flow to {value} on address {address}')
        newtag = MFCclient(address,host,port, connid=self.connid).writeName(value)
        self.userTags[i].setText(newtag)

    def plotSetup(self):
        pass

    def initialDF(self):
        dfs = {}
        print(self.hosts, self.ports)
        for i,(host,port) in enumerate(zip(self.hosts,self.ports)):
            dfs[i] = MFCclient(1,host,port, connid=self.connid).pollAll()
            dfs[i].index.values 
            dfs[i]['host'] = [host]*len(dfs[i].index.values)
            dfs[i]['port'] = [port]*len(dfs[i].index.values)
        df = pd.concat([dfs[i] for i in dfs], axis = 0, ignore_index=True)
        self.fmeas = df['fMeasure'].values
        self.fsp = df['fSetpoint'].values
        return df
    
    def getHPs(self):
        self.hosts = self.hostInput.text().split(',')
        self.ports = [int(p) for p in self.portInput.text().split(',')]
    def connect(self):
        self.getHPs()
        try:
            df = self.initialDF()
        except (OSError, AttributeError) as e:
            raise e
        
        self.plot = self.plotBox.isChecked()
        if self.plot:
            self.plotter = Plotter(host = self.hosts[0], port = self.ports[0], log=False, initDF=df)

        self.tlog = 0
        self.logfile = getLogFile(self.hosts[0],self.ports[0], self.logDirectory.text())
        self.headerstring = logHeader(self.logfile, df)
        self.originalUserTags = {}
        self.originalControlModes = {}
        self.originalFluidIndexes = {}
        self.originalSetpoints = {}
        self.originalSlopes = {}
        for i in df.index.values:
            self.originalSetpoints[i] = df.loc[i]['fSetpoint']
            self.writeSetpointBoxes[i].setValue(self.originalSetpoints[i])
            self.enabledMFCs.append(i)
            self.originalUserTags[i] = df.loc[i]['User tag']
            self.originalControlModes[i] = df.loc[i]['Control mode']
            self.userTags[i].setText(self.originalUserTags[i])
            self.controlBoxes[i].setCurrentIndex(self.originalControlModes[i])
            self.originalFluidIndexes[i] = df.loc[i]['Fluidset index']
            self.fluidBoxes[i].setValue(self.originalFluidIndexes[i])
            self.winkbuttons[i].setEnabled(True)
            self.writeSetpointBoxes[i].setEnabled(True)
            self.controlBoxes[i].setEnabled(True)
            self.slopeBoxes[i].setEnabled(True)
            self.originalSlopes[i] = df.loc[i]['Setpoint slope']
            self.slopeBoxes[i].setValue(self.originalSlopes[i])
            if not self.lockFluidIndex.isChecked():
                self.fluidBoxes[i].setEnabled(True)
            self.userTags[i].setEnabled(True)
            self.addressLabels[i].setStyleSheet('color: black;')
            self.hostBoxes[i].setText(df.loc[i]['host'])
            self.portBoxes[i].setValue(df.loc[i]['port'])
        self.updateMFCs(df)
        message = f'connected to server. Hosts: '
        for host in self.hosts:
            message += f'{host}, '
        message += 'ports: '
        for port in self.ports:
            message += f':{port}, '
        logger.info(message)

    def connectLoop(self):
        if not self.running:
            self.getHPs()
            self.waittime = self.pollTimeBox.value()
            try:
                self.connect()
            except (OSError, AttributeError):
                message = f"couldn't find server at hosts: {self.hosts}, ports: {self.ports}. Try starting it or checking host and port settings"
                print(message)
                logger.warning(message)
                return
            except KeyError:
                message = 'no data returned. Stopping'
                print(message)
                logger.warning(message)
                return
            except Exception as e:
                logger.exception(e)
                raise e
            self.running = True
            self.startButton.setText('stop connection')
            self.hostInput.setEnabled(False)
            self.portInput.setEnabled(False)
            self.pollTimeBox.setEnabled(False)
            self.repollButton.setEnabled(False)
            #self.logDirButton.setEnabled(False)
            self.worker = MultiWorker(self.hosts,self.ports, self.waittime)
            self.thread = QtCore.QThread()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.outputs.connect(self.updateMFCs)
            self.thread.start()
        else:
            self.stopConnect()
            self.disableWidgets()
            logger.info(f'connection closed to server at hosts: {self.hosts}, ports: {self.ports}')
import sys
def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = MultiServerGui()
    ui.show()
    sys.exit(app.exec())