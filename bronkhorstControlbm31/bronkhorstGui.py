from PyQt6 import QtWidgets, QtCore, QtGui
import argparse
import time
import pandas as pd
#import matplotlib.pyplot as plt
if __name__ == '__main__':
    from bronkhorstClient import MFCclient
    from bronkhorstServer import HOST, PORT, logdir
    from plotters import plotAllSingle, getLogFile, logHeader
else:
    from .bronkhorstClient import MFCclient
    from .bronkhorstServer import HOST, PORT, logdir
    from .plotters import plotAllSingle, getLogFile, logHeader
from functools import partial
import logging
import pathlib, os, time
import socket

homedir = pathlib.Path.home()
#logdir = 'bronkhorstLogger'
fulllogdir = f'{homedir}/{logdir}'
os.makedirs(fulllogdir,exist_ok=True)
logger = logging.getLogger()


def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m','--maxMFCs', default=10, type=int, help='maximum number of MFCs that might be needed (default 10)')
    #parser.add_argument('-w', '--waittime',default=1, type = float, help = 'wait time between polling')
    args = parser.parse_args()
    maxMFCs = args.maxMFCs
    '''
    waittime = args.waittime
    if not waittime:
        waittime = 1
    '''
    return maxMFCs#, waittime

class Worker(QtCore.QObject):
    outputs = QtCore.pyqtSignal(pd.DataFrame)
    def __init__(self, host, port, waittime = 1):
        super(Worker,self).__init__()
        self.host = host
        self.port = port
        self.waittime = waittime
        self.mfc = MFCclient(1,self.host,self.port, connid=f'{socket.gethostname()}GUIthread')
        self.running = True
    def run(self):
        while self.running:
            try:
                df = self.mfc.pollAll()
            except (OSError, AttributeError, ConnectionResetError):
                message = "connection to server lost. Stopping polling"
                print(message)
                logger.warning(message)
                self.outputs.emit(pd.DataFrame())
                return
            except Exception as e:
                logger.exception(e)
                raise e
            self.outputs.emit(df)
            time.sleep(self.waittime)
        print('stopping polling')

    def stop(self):
        self.running = False

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        eventlogfile = f'{homedir}/{logdir}/mfcgui.log'
        logging.basicConfig(filename=eventlogfile, level = logging.INFO, format = '%(asctime)s %(levelname)-8s %(message)s',
                            datefmt = '%Y/%m/%d_%H:%M:%S')
        logger.info('mfcgui opened')
        self.connid = f'{socket.gethostname()}GUI'
        self.MainWindow = MainWindow
        self.MainWindow.setObjectName("MainWindow")
        self.MainWindow.resize(800, 550)
        self.MainWindow.setWindowTitle('Bronkhorst GUI')
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.maxMFCs = parseArguments()
        self.box1x = 70
        self.box1y = 20
        self.xspacing = 90
        self.yspacing = 25
        #self.plot = False

        spinboxsizex = 100

        rows = {'wink':0,
                'address':1,
                'setpoint':2,
                'measure':3,
                'setpointpct':4,
                'measurepct':5,
                'valve':6,
                'controlMode':7,
                'fluidIndex':8,
                'fluidName':9,
                'writesp':10,
                'usertag':11}

        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        self.outerLayout = QtWidgets.QVBoxLayout()

        self.group = QtWidgets.QGroupBox()

        self.topLayout = QtWidgets.QHBoxLayout()
        self.gridLayout = QtWidgets.QGridLayout()
        self.leftLayout = QtWidgets.QGridLayout()
        

        self.bottomLayout = QtWidgets.QGridLayout()
        self.bottomLayout.setVerticalSpacing(0)
        
        
        self.startButton = QtWidgets.QPushButton()
        self.startButton.setObjectName('startButton')
        self.startButton.setMinimumWidth(150)
        self.startButton.setText('connect MFCs')
        self.bottomLayout.addWidget(self.startButton,0,0)

        self.runningIndicator = QtWidgets.QRadioButton()
        self.runningIndicator.setObjectName('runningIndicator')
        self.runningIndicator.setText('blinks when running')
        self.runningIndicator.setChecked(False)
        self.bottomLayout.addWidget(self.runningIndicator,1,0)

        self.hostInput = QtWidgets.QLineEdit()
        self.hostInput.setObjectName('hostInput')
        self.hostInput.setMinimumWidth(120)
        self.hostInput.setText(HOST)
        self.bottomLayout.addWidget(self.hostInput, 0, 1)

        self.hostLabel = QtWidgets.QLabel()
        self.hostLabel.setObjectName('hostLabel')
        self.hostLabel.setText('host name')
        self.bottomLayout.addWidget(self.hostLabel,1,1)


        self.portInput = QtWidgets.QSpinBox()
        self.portInput.setObjectName('portInput')
        self.portInput.setMinimumWidth(120)
        self.portInput.setMaximum(2**16)
        self.portInput.setMinimum(8000)
        self.portInput.setValue(PORT)
        self.bottomLayout.addWidget(self.portInput,0,2)

        self.portLabel = QtWidgets.QLabel()
        self.portLabel.setObjectName('portLabel')
        self.portLabel.setText('port value')
        self.bottomLayout.addWidget(self.portLabel,1,2)

        self.pollTimeBox = QtWidgets.QDoubleSpinBox()
        self.pollTimeBox.setObjectName('pollTimeBox')
        self.pollTimeBox.setValue(1)
        self.pollTimeBox.setMinimum(0.1)
        self.pollTimeBox.setMaximum(5)
        self.pollTimeBox.setDecimals(1)
        self.pollTimeBox.setSingleStep(0.1)
        self.bottomLayout.addWidget(self.pollTimeBox,0,3)

        self.pollLabel = QtWidgets.QLabel()
        self.pollLabel.setObjectName('pollLabel')
        self.pollLabel.setText('poll time')
        self.bottomLayout.addWidget(self.pollLabel,1,3)

        self.winkLabel = QtWidgets.QLabel()
        self.winkLabel.setObjectName('winkLabel')
        self.winkLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.winkLabel,rows['wink'],0)

        self.addressLabel = QtWidgets.QLabel()
        self.addressLabel.setObjectName('addressLabel')
        self.addressLabel.setText('address')
        self.addressLabel.adjustSize()
        self.addressLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.addressLabel, rows['address'],0)

        self.spLabel = QtWidgets.QLabel()
        self.spLabel.setObjectName('spLabel')
        self.spLabel.setText('setpoint')
        self.spLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.spLabel,rows['setpoint'],0)

        self.measureLabel = QtWidgets.QLabel()
        self.measureLabel.setObjectName('measureLabel')
        self.measureLabel.setText('measure')
        self.measureLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.measureLabel,rows['measure'],0)

        self.sppctLabel = QtWidgets.QLabel()
        self.sppctLabel.setObjectName('sppctLabel')
        self.sppctLabel.setText('setpoint(%)')
        self.sppctLabel.adjustSize()
        self.sppctLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.sppctLabel,rows['setpointpct'],0)

        self.measurepctLabel = QtWidgets.QLabel()
        self.measurepctLabel.setObjectName('measurepctLabel')
        self.measurepctLabel.setText('measure(%)')
        self.measurepctLabel.adjustSize()
        self.measurepctLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.measurepctLabel,rows['measurepct'],0)

        self.valveLabel = QtWidgets.QLabel()
        self.valveLabel.setObjectName('valveLabel')
        self.valveLabel.setText('valve output')
        self.valveLabel.adjustSize()
        self.valveLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.valveLabel,rows['valve'],0)

        self.controlLable = QtWidgets.QLabel()
        self.controlLable.setObjectName('controlLable')
        self.controlLable.setText('control mode')
        self.controlLable.adjustSize()
        self.controlLable.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.controlLable,rows['controlMode'],0)

        self.fluidLabel = QtWidgets.QLabel()
        self.fluidLabel.setObjectName('fluidLabel')
        self.fluidLabel.setText('fluid index')
        self.fluidLabel.adjustSize()
        self.fluidLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.fluidLabel,rows['fluidIndex'],0)

        self.fluidNameLabel = QtWidgets.QLabel()
        self.fluidNameLabel.setObjectName('fluidNameLabel')
        self.fluidNameLabel.setText('fluid name')
        self.fluidNameLabel.adjustSize()
        self.fluidNameLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.fluidNameLabel,rows['fluidName'],0)

        self.writespLabel = QtWidgets.QLabel()
        self.writespLabel.setObjectName('writespLabel')
        self.writespLabel.setText('write setpoint')
        self.writespLabel.adjustSize()
        self.writespLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.writespLabel,rows['writesp'],0)

        self.userTagLabel = QtWidgets.QLabel()
        self.userTagLabel.setObjectName('userTagLabel')
        self.userTagLabel.setText('user tag')
        self.userTagLabel.adjustSize()
        self.userTagLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.userTagLabel,rows['usertag'],0)

        self.controlModeDct = {
                "0;Bus/RS232":0 ,
                "1;Analog input":1 ,
                "2;FB/RS232 slave":2 ,
                "3;Valve close":3 ,
                "4;Controller idle":4 ,
                "5;Testing mode":5 ,
                "6;Tuning mode":6 ,
                "7;Setpoint 100%":7 ,
                "8;Valve fully open":8 ,
                "9;Calibration mode":9 ,
                "10;Analog slave":10,
                "11;Keyb. & FLOW-BUS":11,
                "12;Setpoint 0%":12,
                "13;FB, analog slave":13,
                "14;(FPP) Range select":14,
                "15;(FPP) Man.s, auto.e":15,
                "16;(FPP) Auto.s, man.e":16,
                "17;(FPP) Auto.s, auto.e":17,
                "18;RS232":18,
                "19;RS232 broadcast":19,
                "20;Valve steering":20,
                "21;An. valve steering":21}
        
        self.winkbuttons= {}
        self.addressLabels = {}
        self.setpointBoxes = {}
        self.measureBoxes = {}
        self.setpointpctBoxes = {}
        self.measurepctBoxes = {}
        self.valveBoxes = {}
        self.controlBoxes = {}
        self.fluidBoxes = {}
        self.fluidNameBoxes = {}
        self.writeSetpointBoxes = {}
        self.writeSetpointpctBoxes = {}
        self.userTags = {}

        self.running = False
        for i in range(self.maxMFCs):
            self.winkbuttons[i] = QtWidgets.QPushButton()
            self.winkbuttons[i].setText('wink')
            self.winkbuttons[i].setObjectName(f'winkbuttons{i}')
            self.winkbuttons[i].setMaximumWidth(spinboxsizex)
            self.winkbuttons[i].setMinimumHeight(self.yspacing)
            self.winkbuttons[i].setEnabled(False)
            self.gridLayout.addWidget(self.winkbuttons[i], rows['wink'],i+1)
            self.winkbuttons[i].clicked.connect(partial(self.wink,i))

            self.addressLabels[i] = QtWidgets.QSpinBox()
            self.addressLabels[i].setObjectName(f'addressLabel{i}')
            self.addressLabels[i].setMinimum(-1)
            self.addressLabels[i].setMaximum(99)
            self.addressLabels[i].setValue(-1)
            self.addressLabels[i].setMaximumWidth(spinboxsizex)
            self.addressLabels[i].setMinimumHeight(self.yspacing)
            self.addressLabels[i].setEnabled(False)
            self.gridLayout.addWidget(self.addressLabels[i], rows['address'], i+1)

            self.setpointBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.setpointBoxes[i].setObjectName(f'setpointBox{i}')
            self.setpointBoxes[i].setEnabled(False)
            self.setpointBoxes[i].setKeyboardTracking(False)
            self.setpointBoxes[i].setStyleSheet('color: black;')
            self.setpointBoxes[i].setMaximum(200)
            self.setpointBoxes[i].setMinimumHeight(self.yspacing)
            self.setpointBoxes[i].setMaximumWidth(spinboxsizex)
            self.gridLayout.addWidget(self.setpointBoxes[i], rows['setpoint'], i+1)

            self.measureBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.measureBoxes[i].setObjectName(f'measureBox{i}')
            self.measureBoxes[i].setEnabled(False)
            self.measureBoxes[i].setStyleSheet('color: black;')
            self.measureBoxes[i].setMaximum(200)
            self.measureBoxes[i].setMinimumHeight(self.yspacing)
            self.measureBoxes[i].setMaximumWidth(120)
            self.gridLayout.addWidget(self.measureBoxes[i], rows['measure'],i+1)

            self.setpointpctBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.setpointpctBoxes[i].setObjectName(f'setpointpctBox{i}')
            self.setpointpctBoxes[i].setEnabled(False)
            self.setpointpctBoxes[i].setStyleSheet('color: black;')
            self.setpointpctBoxes[i].setMaximum(200)
            self.setpointpctBoxes[i].setMinimumHeight(self.yspacing)
            self.setpointpctBoxes[i].setMaximumWidth(spinboxsizex)
            self.gridLayout.addWidget(self.setpointpctBoxes[i],rows['setpointpct'],i+1)

            self.measurepctBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.measurepctBoxes[i].setObjectName(f'measurepctBox{i}')
            self.measurepctBoxes[i].setEnabled(False)
            self.measurepctBoxes[i].setStyleSheet('color: black;')
            self.measurepctBoxes[i].setMaximum(200)
            self.measurepctBoxes[i].setMinimumHeight(self.yspacing)
            self.measurepctBoxes[i].setMaximumWidth(spinboxsizex)
            self.gridLayout.addWidget(self.measurepctBoxes[i], rows['measurepct'],i+1)

            self.valveBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.valveBoxes[i].setObjectName(f'valveBox{i}')
            self.valveBoxes[i].setEnabled(False)
            self.valveBoxes[i].setStyleSheet('color: black;')
            self.valveBoxes[i].setMaximumWidth(spinboxsizex)
            self.valveBoxes[i].setMinimumHeight(self.yspacing)
            self.gridLayout.addWidget(self.valveBoxes[i], rows['valve'],i+1)

            self.controlBoxes[i] = QtWidgets.QComboBox()
            self.controlBoxes[i].setObjectName(f'controlBoxes{i}')
            self.controlBoxes[i].setEnabled(False)
            #self.controlBoxes[i].setStyleSheet('color: black;')
            self.controlBoxes[i].setMaximumWidth(spinboxsizex)
            self.controlBoxes[i].setMinimumHeight(self.yspacing)
            #for mode in self.controlModeDct:
            #    self.controlBoxes[i].addItem(mode)
            self.controlBoxes[i].addItem("0;Bus/RS232")
            self.controlBoxes[i].addItem("1;Analog input")
            self.controlBoxes[i].addItem("2;FB/RS232 slave")
            self.controlBoxes[i].addItem("3;Valve close")
            self.controlBoxes[i].addItem("4;Controller idle")
            self.controlBoxes[i].addItem("5;Testing mode")
            self.controlBoxes[i].addItem("6;Tuning mode")
            self.controlBoxes[i].addItem("7;Setpoint 100%")
            self.controlBoxes[i].addItem("8;Valve fully open")
            self.controlBoxes[i].addItem("9;Calibration mode")
            self.controlBoxes[i].addItem("10;Analog slave")
            self.controlBoxes[i].addItem("11;Keyb. & FLOW-BUS")
            self.controlBoxes[i].addItem("12;Setpoint 0%")
            self.controlBoxes[i].addItem("13;FB, analog slave")
            self.controlBoxes[i].addItem("14;(FPP) Range select")
            self.controlBoxes[i].addItem("15;(FPP) Man.s, auto.e")
            self.controlBoxes[i].addItem("16;(FPP) Auto.s, man.e")
            self.controlBoxes[i].addItem("17;(FPP) Auto.s, auto.e")
            self.controlBoxes[i].addItem("18;RS232")
            self.controlBoxes[i].addItem("19;RS232 broadcast")
            self.controlBoxes[i].addItem("20;Valve steering")
            self.controlBoxes[i].addItem("21;An. valve steering")
            self.controlBoxes[i].currentIndexChanged.connect(partial(self.setControlMode,i))
            self.gridLayout.addWidget(self.controlBoxes[i], rows['controlMode'],i+1)

            self.fluidBoxes[i] = QtWidgets.QSpinBox()
            self.fluidBoxes[i].setObjectName(f'fluidBoxes{i}')
            self.fluidBoxes[i].setEnabled(False)
            self.fluidBoxes[i].setStyleSheet('color: black;')
            self.fluidBoxes[i].setMaximum(20)
            self.fluidBoxes[i].setMinimumHeight(self.yspacing)
            self.fluidBoxes[i].setMaximumWidth(spinboxsizex)
            self.fluidBoxes[i].setKeyboardTracking(False)
            self.fluidBoxes[i].valueChanged.connect(partial(self.setFluidIndex,i))
            self.gridLayout.addWidget(self.fluidBoxes[i], rows['fluidIndex'],i+1)

            self.fluidNameBoxes[i] = QtWidgets.QLabel()
            self.fluidNameBoxes[i].setObjectName(f'fluidNameBoxes{i}')
            self.fluidNameBoxes[i].setMinimumHeight(self.yspacing)
            self.fluidNameBoxes[i].setMaximumWidth(spinboxsizex)
            self.gridLayout.addWidget(self.fluidNameBoxes[i], rows['fluidName'],i+1)

            self.writeSetpointBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.writeSetpointBoxes[i].setObjectName(f'writeSetpointBox{i}')
            self.writeSetpointBoxes[i].setEnabled(False)
            self.writeSetpointBoxes[i].setStyleSheet('color: black;')
            self.writeSetpointBoxes[i].setMaximum(200)
            self.writeSetpointBoxes[i].setKeyboardTracking(False)
            self.writeSetpointBoxes[i].valueChanged.connect(partial(self.setFlow, i))
            self.writeSetpointBoxes[i].setMaximumWidth(spinboxsizex)
            self.writeSetpointBoxes[i].setMinimumHeight(self.yspacing)
            self.gridLayout.addWidget(self.writeSetpointBoxes[i],rows['writesp'],i+1)

            self.userTags[i] = QtWidgets.QLineEdit()
            self.userTags[i].setObjectName(f'userTag{i}')
            self.userTags[i].setEnabled(False)
            self.userTags[i].returnPressed.connect(partial(self.setUserTag, i))
            self.userTags[i].setMaximumWidth(spinboxsizex)
            self.userTags[i].setMinimumHeight(self.yspacing)
            self.gridLayout.addWidget(self.userTags[i],rows['usertag'],i+1)
 
        self.group.setLayout(self.gridLayout)
        
        self.scrollArea.setWidget(self.group)
        self.scrollArea.setMinimumHeight(self.yspacing*(len(rows)+4))

        self.leftLayout.setVerticalSpacing(0)
        self.scrollArea3 = QtWidgets.QScrollArea()
        self.scrollArea3.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea3.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        

        self.group3 = QtWidgets.QGroupBox()
        self.group3.setLayout(self.leftLayout)
        
        self.group3.setFixedHeight(self.group.height())

        self.scrollArea3.setWidget(self.group3)
        self.scrollArea3.setFixedWidth(self.group3.width())

        self.topLayout.addWidget(self.scrollArea3)
        self.topLayout.addWidget(self.scrollArea)
        
        self.topLayout.setSpacing(0)
        self.outerLayout.addLayout(self.topLayout)
        
        self.group2 = QtWidgets.QGroupBox()
        self.group2.setLayout(self.bottomLayout)
        self.scrollArea2 = QtWidgets.QScrollArea()
        self.scrollArea2.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea2.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea2.setWidget(self.group2)

        self.outerLayout.addWidget(self.scrollArea2)
        self.centralwidget.setLayout(self.outerLayout)
        
        self.MainWindow.setCentralWidget(self.centralwidget)
        QtCore.QMetaObject.connectSlotsByName(self.MainWindow)


        self.startButton.clicked.connect(self.connectLoop)

    def connectMFCs(self):
        self.host = self.hostInput.text()
        self.port = self.portInput.value()
        try:
            df = MFCclient(1,self.host,self.port, connid=self.connid).pollAll()
        except OSError as e:
            #print("couldn't find server. Try starting it or checking host and port settings")
            raise OSError(e)
        '''
        if self.plot:
            plt.ion()
            self.fig, self.ax = plt.subplots(2,2)
            self.tlist = []
            self.measureFlow = {}
            self.measureValve = {}
            for i in df.index.values:
                self.measureFlow[i] = []
                self.measureValve[i] = []
            self.tlog = 0
            self.logfile = getLogFile()
            self.headerString = logHeader(self.logfile, df)
        '''
        self.enabledMFCs = []
        self.originalUserTags = {}
        self.originalControlModes = {}
        self.originalFluidIndexes = {}
        self.originalSetpoints = {}
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
        self.updateMFCs(df)
        logger.info(f'connected to server. Host: {self.host}, port: {self.port}')

    def updateMFCs(self,df):
        if len(df.columns) == 0:
            self.disableWidgets()
            return
        checkValue = self.runningIndicator.isChecked()
        self.runningIndicator.setChecked(not checkValue)
        for i in df.index.values:
            try:
                self.winkbuttons[i].setEnabled(True)
                newSetpoint = df.loc[i]['fSetpoint']
                newControlMode = df.loc[i]['Control mode']
                newFluidIndex = df.loc[i]['Fluidset index']
                self.addressLabels[i].setValue(df.loc[i]['address'])
                self.addressLabels[i].setStyleSheet('color: black;')
                self.setpointBoxes[i].setValue(newSetpoint)
                self.measureBoxes[i].setValue(df.loc[i]['fMeasure'])
                self.valveBoxes[i].setValue(df.loc[i]['Valve output'])
                self.setpointpctBoxes[i].setValue(df.loc[i]['Setpoint_pct'])
                self.measurepctBoxes[i].setValue(df.loc[i]['Measure_pct'])
                self.writeSetpointBoxes[i].setEnabled(True)
                self.controlBoxes[i].setEnabled(True)
                self.fluidBoxes[i].setEnabled(True)
                self.fluidNameBoxes[i].setText(df.loc[i]['Fluid name'])
                
                if newControlMode != self.originalControlModes[i]:
                    self.controlBoxes[i].setCurrentIndex(newControlMode)
                    self.originalControlModes[i] = newControlMode
                
                if newFluidIndex != self.originalFluidIndexes[i]:
                    self.fluidBoxes[i].setValue(newFluidIndex)
                    self.originalFluidIndexes[i] = newFluidIndex
                newUserTag = df.loc[i]['User tag']
                if newUserTag != self.originalUserTags[i]:
                    self.userTags[i].setText(df.loc[i]['User tag'])
                    self.originalUserTags[i] = newUserTag
                if newSetpoint != self.originalSetpoints[i]:
                    self.writeSetpointBoxes[i].setValue(newSetpoint)
                    self.originalSetpoints[i] = newSetpoint
                self.userTags[i].setEnabled(True)
            except TypeError as e:
                print(df)
                logger.warning(e)
                return
            except Exception as e:
                print(df)
                logger.exception(e)
                raise e
        '''
        if self.plot:
            plotAllSingle(df,self.tlist, self.ax, self.measureFlow, self.measureValve, 3600, waittime=0.01, log=True, 
                          logfile=self.logfile, tlog=self.tlog, logInterval=5, headerString=self.headerString)
        '''
    def connectLoop(self):
        if not self.running:
            self.host = self.hostInput.text()
            self.port = self.portInput.value()
            self.waittime = self.pollTimeBox.value()
            try:
                self.connectMFCs()
            except OSError:
                message = f"couldn't find server at host: {self.host}, port: {self.port}. Try starting it or checking host and port settings"
                print(message)
                logger.warning(message)
                return
            except Exception as e:
                logger.exception(e)
                raise e
            self.running = True
            self.startButton.setText('stop connection')
            self.worker = Worker(self.host,self.port, self.waittime)
            self.thread = QtCore.QThread()
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.outputs.connect(self.updateMFCs)
            self.thread.start()
        else:
            self.stopConnect()
            self.disableWidgets()
            logger.info(f'connection closed to server at host: {self.host}, port {self.port}')

    def stopConnect(self):
        self.worker.stop()
        self.thread.quit()
        self.running = False
        self.worker.deleteLater()
    
    def disableWidgets(self):
        self.running = False
        self.startButton.setText('connect MFCs')
        for i in range(self.maxMFCs):
            self.writeSetpointBoxes[i].setEnabled(False)
            self.controlBoxes[i].setEnabled(False)
            self.fluidBoxes[i].setEnabled(False)
            self.userTags[i].setEnabled(False)
            self.winkbuttons[i].setEnabled(False)
        '''
        if self.plot:
            plt.close()
        '''
    def setFlow(self,i):
        if not self.running:
            return
        value = self.writeSetpointBoxes[i].value()
        address = self.addressLabels[i].value()
        print(f'setting flow to {value} on address {address}')
        newflow = MFCclient(address,self.host, self.port, connid=self.connid).writeSetpoint(value)
        self.writeSetpointBoxes[i].setValue(newflow)
        
    def setUserTag(self,i):
        if not self.running:
            return
        value = self.userTags[i].text()
        address = self.addressLabels[i].value()
        print(f'setting flow to {value} on address {address}')
        newtag = MFCclient(address,self.host, self.port, connid=self.connid).writeName(value)
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


def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()