from PyQt6 import QtWidgets, QtCore
from functools import partial
from .bronkhorstServer import PORT, HOST
from .plotters import clientlogdir, getLogFile, logHeader, logMFCs
from .bronkhorstClient import MFCclient
import os, time, logging
logger = logging.getLogger()
import numpy as np
import matplotlib.pyplot as plt

class CommonFunctions():
    def lockFluidIndexes(self):
        for i in self.enabledMFCs:
            self.fluidBoxes[i].setEnabled(not self.lockFluidIndex.isChecked())

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

    def updateConfigDct(self):
        self.configDct = {}
        widetList = [self.logDirectory]
        for w in widetList:
            self.configDct[w.objectName()] = {'widget': w ,'value':w.text()}
    def writeConfig(self):
        self.updateConfigDct()
        string = ''
        for item in self.configDct:
            string += f'{item};{self.configDct[item]['value']}\n'
        f = open(self.configfile,'w')
        f.write(string)
        f.close()
    def readConfig(self):
        if not os.path.exists(self.configfile):
            return
        self.updateConfigDct()
        f = open(self.configfile,'r')
        data = f.read()
        f.close()
        for line in data.split('\n'):
            if not line:
                continue
            name, value = line.split(';')
            self.configDct[name]['widget'].setText(value)
        self.updateConfigDct()
        if not os.path.exists(self.logDirectory.text()):
            print('stored log directory doesn\'t exist, setting to default')
            self.logDirectory.setText(clientlogdir)
            self.writeConfig()
    def updateMFCs(self,df):
        if len(df.columns) == 0:
            self.stopConnect()
            self.disableWidgets()
            return
        checkValue = self.runningIndicator.isChecked()
        self.runningIndicator.setChecked(not checkValue)
        for i in df.index.values:
            try:
                newSetpoint = df.loc[i]['fSetpoint']
                newControlMode = df.loc[i]['Control mode']
                newFluidIndex = df.loc[i]['Fluidset index']
                self.addressLabels[i].setValue(df.loc[i]['address'])
                self.setpointBoxes[i].setValue(newSetpoint)
                self.measureBoxes[i].setValue(df.loc[i]['fMeasure'])
                self.valveBoxes[i].setValue(df.loc[i]['Valve output'])
                self.setpointpctBoxes[i].setValue(df.loc[i]['Setpoint_pct'])
                self.measurepctBoxes[i].setValue(df.loc[i]['Measure_pct'])
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
                newslope = df.loc[i]['Setpoint slope']
                if newslope != self.originalSlopes[i]:
                    self.slopeBoxes[i].setValue(newslope)
                    self.originalSlopes[i] = newslope

            except TypeError as e:
                print(df)
                logger.warning(e)
                return
            except Exception as e:
                print(df)
                logger.exception(e)
                raise e
            
        measDiff = np.max(np.abs(df['fMeasure'].values - self.fmeas))
        spChange = (df['fSetpoint'].values != self.fsp).any()
        if time.time() - self.tlog > 30 or measDiff > 0.2 or spChange:
            self.headerstring = logMFCs(self.logfile,df,self.headerstring)
            self.tlog = time.time()
            self.fmeas = df['fMeasure'].values
            self.fsp = df['fSetpoint'].values
        if self.plot and self.running:
            self.plotter.plotAllSingle(df)
            
    def stopConnect(self):
        self.worker.stop()
        self.thread.quit()
        self.worker.deleteLater()
        if self.plot:
            plt.close()
        self.thread.wait()
        self.running = False

    def guiLayout(self):
        self.xspacing = 90
        self.yspacing = 25

        self.spinboxsizex = 100
        
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

        self.plotBox = QtWidgets.QCheckBox()
        self.plotBox.setObjectName('plotBox')
        self.plotBox.setText('plot data?')
        self.plotBox.setEnabled(True)
        self.plotBox.setChecked(True)
        self.bottomLayout.addWidget(self.plotBox)

        self.hostInput = QtWidgets.QLineEdit()
        self.hostInput.setObjectName('hostInput')
        self.hostInput.setMinimumWidth(120)
        self.hostInput.setText(HOST)
        self.bottomLayout.addWidget(self.hostInput, 0, 1)

        self.hostLabel = QtWidgets.QLabel()
        self.hostLabel.setObjectName('hostLabel')
        self.hostLabel.setText('host name')
        self.bottomLayout.addWidget(self.hostLabel,1,1)

        self.portLabel = QtWidgets.QLabel()
        self.portLabel.setObjectName('portLabel')
        self.portLabel.setText('port value')
        self.bottomLayout.addWidget(self.portLabel,1,2)

        self.pollTimeBox = QtWidgets.QDoubleSpinBox()
        self.pollTimeBox.setObjectName('pollTimeBox')
        self.pollTimeBox.setValue(0.5)
        self.pollTimeBox.setMinimum(0.1)
        self.pollTimeBox.setMaximum(5)
        self.pollTimeBox.setDecimals(1)
        self.pollTimeBox.setSingleStep(0.1)
        self.bottomLayout.addWidget(self.pollTimeBox,0,3)

        self.pollLabel = QtWidgets.QLabel()
        self.pollLabel.setObjectName('pollLabel')
        self.pollLabel.setText('poll time')
        self.bottomLayout.addWidget(self.pollLabel,1,3)

        self.lockFluidIndex = QtWidgets.QCheckBox()
        self.lockFluidIndex.setObjectName('lockFluidIndex')
        self.lockFluidIndex.setText('lock fluid index')
        self.lockFluidIndex.setChecked(False)
        self.bottomLayout.addWidget(self.lockFluidIndex, 2,1)

        self.logDirectory = QtWidgets.QLineEdit()
        self.logDirectory.setObjectName('logDirectory')
        self.logDirectory.setText(clientlogdir)
        self.bottomLayout.addWidget(self.logDirectory, 2,2,1,2)
        self.logDirectory.setEnabled(False)
        self.logDirectory.setStyleSheet('color: black; background-color: white')

        self.logDirButton = QtWidgets.QPushButton()
        self.logDirButton.setObjectName('logDirButton')
        self.logDirButton.setText('...')
        self.logDirButton.setMaximumWidth(50)
        self.bottomLayout.addWidget(self.logDirButton, 2,4)
        self.logDirButton.clicked.connect(self.setClientLogDir)

        self.logLabel = QtWidgets.QLabel()
        self.logLabel.setObjectName('logLabel')
        self.logLabel.setText('log directory')
        self.bottomLayout.addWidget(self.logLabel,3,2)

        self.repollButton = QtWidgets.QPushButton()
        self.repollButton.setObjectName('repollButton')
        self.repollButton.setText('update MFC addresses')
        self.bottomLayout.addWidget(self.repollButton,3,0)
        self.repollButton.clicked.connect(self.repoll)

        self.winkLabel = QtWidgets.QLabel()
        self.winkLabel.setObjectName('winkLabel')
        self.winkLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.winkLabel,self.rows['wink'],0)

        self.addressLabel = QtWidgets.QLabel()
        self.addressLabel.setObjectName('addressLabel')
        self.addressLabel.setText('address')
        self.addressLabel.adjustSize()
        self.addressLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.addressLabel, self.rows['address'],0)

        self.spLabel = QtWidgets.QLabel()
        self.spLabel.setObjectName('spLabel')
        self.spLabel.setText('setpoint')
        self.spLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.spLabel,self.rows['setpoint'],0)

        self.measureLabel = QtWidgets.QLabel()
        self.measureLabel.setObjectName('measureLabel')
        self.measureLabel.setText('measure')
        self.measureLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.measureLabel,self.rows['measure'],0)

        self.sppctLabel = QtWidgets.QLabel()
        self.sppctLabel.setObjectName('sppctLabel')
        self.sppctLabel.setText('setpoint(%)')
        self.sppctLabel.adjustSize()
        self.sppctLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.sppctLabel,self.rows['setpointpct'],0)

        self.measurepctLabel = QtWidgets.QLabel()
        self.measurepctLabel.setObjectName('measurepctLabel')
        self.measurepctLabel.setText('measure(%)')
        self.measurepctLabel.adjustSize()
        self.measurepctLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.measurepctLabel,self.rows['measurepct'],0)

        self.valveLabel = QtWidgets.QLabel()
        self.valveLabel.setObjectName('valveLabel')
        self.valveLabel.setText('valve output')
        self.valveLabel.adjustSize()
        self.valveLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.valveLabel,self.rows['valve'],0)

        self.controlLable = QtWidgets.QLabel()
        self.controlLable.setObjectName('controlLable')
        self.controlLable.setText('control mode')
        self.controlLable.adjustSize()
        self.controlLable.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.controlLable,self.rows['controlMode'],0)

        self.fluidLabel = QtWidgets.QLabel()
        self.fluidLabel.setObjectName('fluidLabel')
        self.fluidLabel.setText('fluid index')
        self.fluidLabel.adjustSize()
        self.fluidLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.fluidLabel,self.rows['fluidIndex'],0)

        self.fluidNameLabel = QtWidgets.QLabel()
        self.fluidNameLabel.setObjectName('fluidNameLabel')
        self.fluidNameLabel.setText('fluid name')
        self.fluidNameLabel.adjustSize()
        self.fluidNameLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.fluidNameLabel,self.rows['fluidName'],0)

        
        self.slopeLabel = QtWidgets.QLabel()
        self.slopeLabel.setObjectName('slopeLabel')
        self.slopeLabel.setText('slope(ms/(ml/min))')
        self.slopeLabel.adjustSize()
        self.slopeLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.slopeLabel, self.rows['slope'],0)
        

        self.writespLabel = QtWidgets.QLabel()
        self.writespLabel.setObjectName('writespLabel')
        self.writespLabel.setText('write setpoint')
        self.writespLabel.adjustSize()
        self.writespLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.writespLabel,self.rows['writesp'],0)

        self.userTagLabel = QtWidgets.QLabel()
        self.userTagLabel.setObjectName('userTagLabel')
        self.userTagLabel.setText('user tag')
        self.userTagLabel.adjustSize()
        self.userTagLabel.setMinimumHeight(self.yspacing)
        self.leftLayout.addWidget(self.userTagLabel,self.rows['usertag'],0)

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
        self.slopeBoxes = {}

        self.enabledMFCs = []

        self.running = False
        for i in range(self.maxMFCs):
            self.winkbuttons[i] = QtWidgets.QPushButton()
            self.winkbuttons[i].setText('wink')
            self.winkbuttons[i].setObjectName(f'winkbuttons{i}')
            self.winkbuttons[i].setMaximumWidth(self.spinboxsizex)
            self.winkbuttons[i].setMinimumHeight(self.yspacing)
            self.winkbuttons[i].setEnabled(False)
            self.gridLayout.addWidget(self.winkbuttons[i], self.rows['wink'],i+1)
            self.winkbuttons[i].clicked.connect(partial(self.wink,i))

            self.addressLabels[i] = QtWidgets.QSpinBox()
            self.addressLabels[i].setObjectName(f'addressLabel{i}')
            self.addressLabels[i].setMinimum(-1)
            self.addressLabels[i].setMaximum(99)
            self.addressLabels[i].setValue(-1)
            self.addressLabels[i].setMaximumWidth(self.spinboxsizex)
            self.addressLabels[i].setMinimumHeight(self.yspacing)
            self.addressLabels[i].setEnabled(False)
            self.gridLayout.addWidget(self.addressLabels[i], self.rows['address'], i+1)

            self.setpointBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.setpointBoxes[i].setObjectName(f'setpointBox{i}')
            self.setpointBoxes[i].setEnabled(False)
            self.setpointBoxes[i].setKeyboardTracking(False)
            self.setpointBoxes[i].setStyleSheet('color: black;')
            self.setpointBoxes[i].setMaximum(200)
            self.setpointBoxes[i].setMinimumHeight(self.yspacing)
            self.setpointBoxes[i].setMaximumWidth(self.spinboxsizex)
            self.gridLayout.addWidget(self.setpointBoxes[i], self.rows['setpoint'], i+1)

            self.measureBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.measureBoxes[i].setObjectName(f'measureBox{i}')
            self.measureBoxes[i].setEnabled(False)
            self.measureBoxes[i].setStyleSheet('color: black;')
            self.measureBoxes[i].setMaximum(200)
            self.measureBoxes[i].setMinimumHeight(self.yspacing)
            self.measureBoxes[i].setMaximumWidth(120)
            self.gridLayout.addWidget(self.measureBoxes[i], self.rows['measure'],i+1)

            self.setpointpctBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.setpointpctBoxes[i].setObjectName(f'setpointpctBox{i}')
            self.setpointpctBoxes[i].setEnabled(False)
            self.setpointpctBoxes[i].setStyleSheet('color: black;')
            self.setpointpctBoxes[i].setMaximum(200)
            self.setpointpctBoxes[i].setMinimumHeight(self.yspacing)
            self.setpointpctBoxes[i].setMaximumWidth(self.spinboxsizex)
            self.gridLayout.addWidget(self.setpointpctBoxes[i],self.rows['setpointpct'],i+1)

            self.measurepctBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.measurepctBoxes[i].setObjectName(f'measurepctBox{i}')
            self.measurepctBoxes[i].setEnabled(False)
            self.measurepctBoxes[i].setStyleSheet('color: black;')
            self.measurepctBoxes[i].setMaximum(200)
            self.measurepctBoxes[i].setMinimumHeight(self.yspacing)
            self.measurepctBoxes[i].setMaximumWidth(self.spinboxsizex)
            self.gridLayout.addWidget(self.measurepctBoxes[i], self.rows['measurepct'],i+1)

            self.valveBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.valveBoxes[i].setObjectName(f'valveBox{i}')
            self.valveBoxes[i].setEnabled(False)
            self.valveBoxes[i].setStyleSheet('color: black;')
            self.valveBoxes[i].setMaximumWidth(self.spinboxsizex)
            self.valveBoxes[i].setMinimumHeight(self.yspacing)
            self.gridLayout.addWidget(self.valveBoxes[i], self.rows['valve'],i+1)

            self.controlBoxes[i] = QtWidgets.QComboBox()
            self.controlBoxes[i].setObjectName(f'controlBoxes{i}')
            self.controlBoxes[i].setEnabled(False)
            self.controlBoxes[i].setMaximumWidth(self.spinboxsizex)
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
            self.gridLayout.addWidget(self.controlBoxes[i], self.rows['controlMode'],i+1)

            self.fluidBoxes[i] = QtWidgets.QSpinBox()
            self.fluidBoxes[i].setObjectName(f'fluidBoxes{i}')
            self.fluidBoxes[i].setEnabled(False)
            self.fluidBoxes[i].setStyleSheet('color: black;')
            self.fluidBoxes[i].setMaximum(20)
            self.fluidBoxes[i].setMinimumHeight(self.yspacing)
            self.fluidBoxes[i].setMaximumWidth(self.spinboxsizex)
            self.fluidBoxes[i].setKeyboardTracking(False)
            self.fluidBoxes[i].valueChanged.connect(partial(self.setFluidIndex,i))
            self.gridLayout.addWidget(self.fluidBoxes[i], self.rows['fluidIndex'],i+1)

            self.fluidNameBoxes[i] = QtWidgets.QLabel()
            self.fluidNameBoxes[i].setObjectName(f'fluidNameBoxes{i}')
            self.fluidNameBoxes[i].setMinimumHeight(self.yspacing)
            self.fluidNameBoxes[i].setMaximumWidth(self.spinboxsizex)
            self.gridLayout.addWidget(self.fluidNameBoxes[i], self.rows['fluidName'],i+1)

            self.slopeBoxes[i] = QtWidgets.QSpinBox()
            self.slopeBoxes[i].setObjectName(f'slopeBoxes{i}')
            self.slopeBoxes[i].setMinimumHeight(self.yspacing)
            self.slopeBoxes[i].setMaximumWidth(self.spinboxsizex)
            self.slopeBoxes[i].setMinimum(0)
            self.slopeBoxes[i].setMaximum(30000)
            self.slopeBoxes[i].setValue(0)
            self.slopeBoxes[i].setSingleStep(100)
            self.slopeBoxes[i].setEnabled(False)
            self.slopeBoxes[i].setKeyboardTracking(False)
            self.slopeBoxes[i].valueChanged.connect(partial(self.setSlope,i))
            self.gridLayout.addWidget(self.slopeBoxes[i], self.rows['slope'],i+1)

            self.writeSetpointBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.writeSetpointBoxes[i].setObjectName(f'writeSetpointBox{i}')
            self.writeSetpointBoxes[i].setEnabled(False)
            self.writeSetpointBoxes[i].setStyleSheet('color: black;')
            self.writeSetpointBoxes[i].setMaximum(200)
            self.writeSetpointBoxes[i].setKeyboardTracking(False)
            self.writeSetpointBoxes[i].valueChanged.connect(partial(self.setFlow, i))
            self.writeSetpointBoxes[i].setMaximumWidth(self.spinboxsizex)
            self.writeSetpointBoxes[i].setMinimumHeight(self.yspacing)
            self.gridLayout.addWidget(self.writeSetpointBoxes[i],self.rows['writesp'],i+1)

            self.userTags[i] = QtWidgets.QLineEdit()
            self.userTags[i].setObjectName(f'userTag{i}')
            self.userTags[i].setEnabled(False)
            self.userTags[i].returnPressed.connect(partial(self.setUserTag, i))
            self.userTags[i].setMaximumWidth(self.spinboxsizex)
            self.userTags[i].setMinimumHeight(self.yspacing)
            self.gridLayout.addWidget(self.userTags[i],self.rows['usertag'],i+1)

    def formatLayouts(self):
        self.group.setLayout(self.gridLayout)
        
        self.scrollArea.setWidget(self.group)
        self.scrollArea.setMinimumHeight(int(self.yspacing*1.35*len(self.rows)))

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

    def disableWidgets(self):
        self.running = False
        self.startButton.setText('connect MFCs')
        self.hostInput.setEnabled(True)
        self.portInput.setEnabled(True)
        self.pollTimeBox.setEnabled(True)
        self.plotBox.setEnabled(True)
        self.repollButton.setEnabled(True)
        self.enabledMFCs = []
        for i in range(self.maxMFCs):
            self.writeSetpointBoxes[i].setEnabled(False)
            self.controlBoxes[i].setEnabled(False)
            self.fluidBoxes[i].setEnabled(False)
            self.userTags[i].setEnabled(False)
            self.winkbuttons[i].setEnabled(False)
            self.addressLabels[i].setStyleSheet('color: gray;')
            self.slopeBoxes[i].setEnabled(False)

