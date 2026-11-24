from PyQt6 import QtWidgets, QtCore, QtGui
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from .bronkhorstClient import MFCclient
from .bronkhorstServer import HOST, PORT, logdir
from .plotters import Plotter, getLogFile, logHeader, logMFCs, clientlogdir
from .guiLayout import CommonFunctions, fulllogdir
import logging
import pathlib, os
import socket
import platform

if platform.system() == 'Windows':
	import ctypes
	myappid = '_mfcgui' 
	ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


homedir = pathlib.Path.home()

logger = logging.getLogger()

def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m','--maxMFCs', default=10, type=int, help=('maximum number of MFCs that might be ' 
                                                                      'needed (default 10)'))
    parser.add_argument('-v', '--verbose', default=0, type = int, help= 'verbose level. Integer, default 0. 1 to print more, -1 to print less')
    args = parser.parse_args()
    maxMFCs = args.maxMFCs
    vlevel = parser.verbose
    return maxMFCs, vlevel

class Worker(QtCore.QObject):
    outputs = QtCore.pyqtSignal(pd.DataFrame)
    stopsignal = QtCore.pyqtSignal()
    def __init__(self, host, port, waittime = 1, vlevel = 0):
        super(Worker,self).__init__()
        self.host = host
        self.port = port
        self.waittime = waittime
        self.mfc = MFCclient(1,self.host,self.port, connid=f'{socket.gethostname()}GUIthread', vlevel=vlevel)
        self.running = True
    def run(self):
        self.wait = False
        while self.running:
            if self.wait:
                continue
            #os.system('cls')
            self.runOnce()
            QtCore.QThread.msleep(int(self.waittime*1000))
            #time.sleep(self.waittime)
        print('stopping polling')

    def stop(self):
        self.running = False
    
    def runOnce(self):
        try:
            df = self.mfc.pollAll()
        except (OSError, AttributeError, ConnectionResetError):
            message = "connection to server lost. Stopping polling"
            print(message)
            logger.warning(message)
            self.outputs.emit(pd.DataFrame())
            return
        except KeyError as e:
            message = f'no data returned. Stopping:\n{e}'
            print(message)
            logger.warning(message)
            self.outputs.emit(pd.DataFrame())
            return
        except Exception as e:
            logger.exception(e)
            print(e)
            self.wait = True
            self.stopsignal.emit()
            return
            #raise e
        self.outputs.emit(df)
        

class Ui_MainWindow(QtWidgets.QMainWindow, CommonFunctions):
    def setupUi(self):
        self.worker:Worker|None=None
        self.multi = False
        self.useQclient = True
        eventlogfile = f'{homedir}/{logdir}/mfcgui.log'
        logging.basicConfig(filename=eventlogfile, level = logging.INFO, format = '%(asctime)s %(levelname)-8s %(message)s',
                            datefmt = '%Y/%m/%d_%H:%M:%S')
        logger.info('mfcgui opened')
        self.connid = f'{socket.gethostname()}GUI'
        self.setWindowTitle('Bronkhorst GUI')
        self.centralwidget = QtWidgets.QWidget()
        self.centralwidget.setObjectName("centralwidget")

        
        curpath = os.path.dirname(os.path.realpath(__file__))
        iconfile = f'{curpath}/images/drawing.ico'
        icon = QtGui.QIcon(iconfile)
        super().setWindowIcon(icon)
        self.hostlabeltext = 'host name'
        self.portlabeltext = 'port value'
        self.rows = {'wink':0,
                     'com':1,
                'address':2,
                'slope':3,
                'setpoint':4,
                'measure':5,
                'setpointpct':6,
                'measurepct':7,
                'valve':8,
                'controlMode':9,
                'fluidIndex':10,
                'fluidName':11,
                'writesp':12,
                'usertag':13}

        #self.maxMFCs, self.vlevel = parseArguments()
        super().parseArguments()
        super().guiLayout()
        self.portInput = QtWidgets.QSpinBox()
        self.portInput.setObjectName('portInput')
        self.portInput.setMinimumWidth(120)
        self.portInput.setMaximum(2**16)
        self.portInput.setMinimum(8000)
        self.portInput.setValue(PORT)
        self.bottomLayout.addWidget(self.portInput,0,2)
        super().formatLayouts()
        self.centralwidget.setLayout(self.outerLayout)

        #self.resize(800, int(1.15*(self.group.height()+self.group2.height())))
        
        self.setCentralWidget(self.centralwidget)
        QtCore.QMetaObject.connectSlotsByName(self)

        self.readConfig()
        self.initialisevaluedcts()
        self.startButton.clicked.connect(self.connectLoop)
        self.lockFluidIndex.stateChanged.connect(self.lockFluidIndexes)
        self.plotBox.stateChanged.connect(self.plotSetup)

    def plotSetup(self):
        self.plot = self.plotBox.isChecked()
        if self.plot and self.running:
            self.plotter = Plotter(host = self.host, port = self.port, log = False)
        elif not self.plot:
            plt.close()



    def connectMFCs(self):
        self.host = self.hostInput.text()
        self.port = self.portInput.value()
        self.firstconnect=True
        
        try:
            df = MFCclient(1,self.host,self.port, connid=self.connid).pollAll()
            self.fmeas = df['fMeasure'].values
            self.fsp = df['fSetpoint'].values
        except (OSError, AttributeError) as e:
            raise e
        
        self.plot = self.plotBox.isChecked()
        if self.plot:
            self.plotter = Plotter(host = self.host, port = self.port, log=False, initDF=df)

        self.tlog = 0
        self.logfile = getLogFile(self.host,self.port, self.logDirectory.text())
        self.headerstring = logHeader(self.logfile, df)

        
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
        self.updateMFCs(df)
        logger.info(f'connected to server. Host: {self.host}, port: {self.port}')


    def setwidgets(self,enabled:bool):
        self.hostInput.setEnabled(enabled)
        self.portInput.setEnabled(enabled)
        self.pollTimeBox.setEnabled(enabled)
        self.repollButton.setEnabled(enabled)
        if not enabled:
            self.startButton.setText('stop connection')
        else:
            self.startButton.setText('connect MFCs')
        #self.logDirButton.setEnabled(enabled)
    def connectLoop(self):
        self.logfile = getLogFile(self.hostInput.text() ,self.portInput.value(), self.logDirectory.text())
        if not self.running and not self.useQclient:
            self.host = self.hostInput.text()
            self.port = self.portInput.value()
            self.waittime = self.pollTimeBox.value()
            self.firstconnect = True
            '''
            try:
                self.connectMFCs()
            except (OSError, AttributeError):
                message = f"couldn't find server at host: {self.host}, port: {self.port}. Try starting it or checking host and port settings"
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
            '''
            self.running = True
            
            self.setwidgets(False)
            self.worker = Worker(self.host,self.port, self.waittime, vlevel = self.vlevel)
            self.thread = QtCore.QThread()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.outputs.connect(self.updateMFCs)
            self.worker.stopsignal.connect(self.closefromthread)
            self.thread.start()
        elif self.useQclient and not self.running: #handles running and not running
            #self.connectMFCs()

            self.setwidgets(False)
            self.connectQt()
            self.running = True
        elif self.running:
            self.stopConnect()
            self.disableWidgets()
            
            logger.info(f'connection closed to server at host: {self.host}, port {self.port}')

    def setClientLogDir(self):
        if self.logDirectory.text():
            currDir = self.logDirectory.text()
        else:
            currDir = '.'
        dialog = QtWidgets.QFileDialog.getExistingDirectory(caption='select log directory', directory=currDir)
        if dialog:
            self.logDirectory.setText(dialog)
            if self.running:
                self.logfile = getLogFile(self.host,self.port, self.logDirectory.text())
                df = MFCclient(1,self.host,self.port, connid='getheader').pollAll()
                logHeader(self.logfile, df)
            self.writeConfig()
            
    def setFlow(self,i):
        if not self.running:
            return
        value = self.writeSetpointBoxes[i].value()
        address = self.addressLabels[i].value()
        print(f'setting flow to {value} on address {address}')
        newflow = MFCclient(address,self.host, self.port, connid=self.connid).writeSetpoint(value)
        self.writeSetpointBoxes[i].setValue(newflow)
        
    def setUserTag(self,i):
        if not self.running or self.firstconnect:
            return
        value = self.userTags[i].text()
        address = self.addressLabels[i].value()
        com = self.comboxes[i].text()
        comi = int(com.replace('COM',''))
        print(f'setting flow to {value} on address {address}')
        newtag = MFCclient(address,self.host, self.port, connid=self.connid, com=comi).writeName(value)
        self.userTags[i].setText(newtag)

    def setFlowAll(self):
        if not self.running:
            return
        for i in self.enabledMFCs:
            self.setFlow(i)

    def setControlMode(self,i):
        if not self.running:
            return
        value = self.controlBoxes[i].currentIndex()
        #text = self.controlBoxes[i].currentText()
        #value = int(text.split(';')[0])
        address = self.addressLabels[i].value()
        print(f'setting address {address} to control mode {value}')
        
        newmode = MFCclient(address, self.host,self.port, connid=self.connid).writeControlMode(value)
        self.controlBoxes[i].setCurrentIndex(newmode)

    def repoll(self):
        self.host = self.hostInput.text()
        self.port = self.portInput.value()
        plot = self.plotBox.isChecked()
        try:
            mfc = MFCclient(1,self.host,self.port, connid=self.connid)
            mfc.readAddresses()
        except:
            print(f"couldn't connect to bronkhorstServer at {self.host}:{self.port}")
            return
        self.plotBox.setChecked(False)
        self.connectMFCs()
        self.disableWidgets()
        self.plotBox.setChecked(plot)
        self.running = False

    def setFluidIndex(self,i):
        if not self.running:
            return
        value = self.fluidBoxes[i].value()
        address = self.addressLabels[i].value()
        print(f'setting address {address} to fluid {value}')
        newfluid = MFCclient(address,self.host,self.port, connid=self.connid).writeFluidIndex(value)
        newfluidIndex = newfluid['Fluidset index']
        self.fluidBoxes[i].setValue(newfluidIndex)
    
    def wink(self,i):
        address = self.addressLabels[i].value()
        MFCclient(address,self.host,self.port, connid=self.connid).wink()

    def setSlope(self,i):
        if not self.running:
            return
        value = self.slopeBoxes[i].value()
        address = self.addressLabels[i].value()
        print(f'setting slope to {value} on address {address}')
        newslope = MFCclient(address,self.host,self.port,connid=self.connid).writeSlope(value)
        self.slopeBoxes[i].setValue(newslope)
        
    def closeEvent(self,event:QtCore.QEvent):
        print('closing')
        if self.running:
            self.stopConnect()
        logger.info('mfcgui closed normally')
        super().closeEvent(event)
        event.accept()
    def closefromthread(self):
        logging.error('mfcgui error in thread')
        super().close()
       
import sys       
def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = Ui_MainWindow()
    ui.setupUi()
    ui.show()
    sys.exit(app.exec())
