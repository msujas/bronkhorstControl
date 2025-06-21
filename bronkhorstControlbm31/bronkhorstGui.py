from PyQt6 import QtWidgets, QtCore, QtGui
import argparse
import time
import pandas as pd
if __name__ == '__main__':
    from bronkhorstClient import MFCclient
    from bronkhorstServer import HOST, PORT
else:
    from .bronkhorstClient import MFCclient
    from .bronkhorstServer import HOST, PORT
from functools import partial


def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m','--maxMFCs', default=10, type=int, help='maximum number of MFCs that might be needed (default 10)')
    parser.add_argument('-w', '--waittime',default=1, type = int, help = 'wait time between polling')
    args = parser.parse_args()
    maxMFCs = args.maxMFCs
    waittime = args.waittime
    if not waittime:
        waittime = 1
    return maxMFCs, waittime

class Worker(QtCore.QThread):
    outputs = QtCore.pyqtSignal(pd.DataFrame)
    def __init__(self, host, port, waittime = 1):
        super(Worker,self).__init__()
        self.host = host
        self.port = port
        self.waittime = waittime
    def run(self):
        while True:
            try:
                df = MFCclient(1,self.host,self.port).pollAll()
            except (OSError, AttributeError, ConnectionResetError):
                print("connection to server lost. Exiting")
                self.outputs.emit(pd.DataFrame())
                return
            self.outputs.emit(df)
            time.sleep(self.waittime)
    def stop(self):
        self.terminate()

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.MainWindow = MainWindow
        self.MainWindow.setObjectName("MainWindow")
        self.MainWindow.resize(800, 450)
        self.MainWindow.setWindowTitle('Bronkhorst GUI')
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.maxMFCs, self.waittime = parseArguments()
        self.box1x = 70
        self.box1y = 20
        self.xspacing = 90
        self.yspacing = 35

        spinboxsizex = 100

        rows = {'address':0,
                'setpoint':1,
                'measure':2,
                'setpointpct':3,
                'measurepct':4,
                'valve':5,
                'writesp':6,
                'usertag':7}

        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        self.outerLayout = QtWidgets.QVBoxLayout()

        self.group = QtWidgets.QGroupBox()

        self.gridLayout = QtWidgets.QGridLayout()

        self.bottomLayout = QtWidgets.QGridLayout()
        self.bottomLayout.setVerticalSpacing(0)
        
        
        self.startButton = QtWidgets.QPushButton(self.centralwidget)
        self.startButton.setObjectName('startButton')
        self.startButton.setMinimumWidth(150)
        self.startButton.setText('connect MFCs')
        self.bottomLayout.addWidget(self.startButton,0,0)

        self.hostInput = QtWidgets.QLineEdit(self.centralwidget)
        self.hostInput.setObjectName('hostInput')
        self.hostInput.setMinimumWidth(120)
        self.hostInput.setText(HOST)
        self.bottomLayout.addWidget(self.hostInput, 0, 1)

        self.hostLabel = QtWidgets.QLabel(self.centralwidget)
        self.hostLabel.setObjectName('hostLabel')
        self.hostLabel.setText('host name')
        self.bottomLayout.addWidget(self.hostLabel,1,1)


        self.portInput = QtWidgets.QSpinBox(self.centralwidget)
        self.portInput.setObjectName('portInput')
        self.portInput.setMinimumWidth(120)
        self.portInput.setMaximum(2**16)
        self.portInput.setMinimum(8000)
        self.portInput.setValue(PORT)
        self.bottomLayout.addWidget(self.portInput,0,2)

        self.portLabel = QtWidgets.QLabel(self.centralwidget)
        self.portLabel.setObjectName('portLabel')
        self.portLabel.setText('port value')
        self.bottomLayout.addWidget(self.portLabel,1,2)

        self.addressLabel = QtWidgets.QLabel()
        self.addressLabel.setObjectName('addressLabel')
        self.addressLabel.setText('addresses')
        self.addressLabel.adjustSize()
        self.gridLayout.addWidget(self.addressLabel, rows['address'],0)

        self.spLabel = QtWidgets.QLabel()
        self.spLabel.setObjectName('spLabel')
        self.spLabel.setText('setpoint')
        self.gridLayout.addWidget(self.spLabel,rows['setpoint'],0)

        self.measureLabel = QtWidgets.QLabel()
        self.measureLabel.setObjectName('measureLabel')
        self.measureLabel.setText('measure')
        self.gridLayout.addWidget(self.measureLabel,rows['measure'],0)

        self.sppctLabel = QtWidgets.QLabel()
        self.sppctLabel.setObjectName('sppctLabel')
        self.sppctLabel.setText('setpoint(%)')
        self.sppctLabel.adjustSize()
        self.gridLayout.addWidget(self.sppctLabel,rows['setpointpct'],0)

        self.measurepctLabel = QtWidgets.QLabel()
        self.measurepctLabel.setObjectName('measurepctLabel')
        self.measurepctLabel.setText('measure(%)')
        self.measurepctLabel.adjustSize()
        self.gridLayout.addWidget(self.measurepctLabel,rows['measurepct'],0)

        self.valveLabel = QtWidgets.QLabel()
        self.valveLabel.setObjectName('valveLabel')
        self.valveLabel.setText('valve output')
        self.valveLabel.adjustSize()
        self.gridLayout.addWidget(self.valveLabel,rows['valve'],0)

        self.writespLabel = QtWidgets.QLabel()
        self.writespLabel.setObjectName('writespLabel')
        self.writespLabel.setText('write setpoint')
        self.writespLabel.adjustSize()
        self.gridLayout.addWidget(self.writespLabel,rows['writesp'],0)

        self.userTagLabel = QtWidgets.QLabel()
        self.userTagLabel.setObjectName('userTagLabel')
        self.userTagLabel.setText('user tag')
        self.userTagLabel.adjustSize()
        self.gridLayout.addWidget(self.userTagLabel,rows['usertag'],0)


        

        self.addressLabels = {}
        self.setpointBoxes = {}
        self.measureBoxes = {}
        self.setpointpctBoxes = {}
        self.measurepctBoxes = {}
        self.valveBoxes = {}
        self.writeSetpointBoxes = {}
        self.writeSetpointpctBoxes = {}
        self.userTags = {}

        self.running = False
        for i in range(self.maxMFCs):
            self.addressLabels[i] = QtWidgets.QSpinBox()
            self.addressLabels[i].setObjectName(f'addressLabel{i}')
            self.addressLabels[i].setMinimum(-1)
            self.addressLabels[i].setMaximum(99)
            self.addressLabels[i].setValue(-1)
            self.addressLabels[i].setMaximumWidth(spinboxsizex)
            self.addressLabels[i].setEnabled(False)
            self.gridLayout.addWidget(self.addressLabels[i], rows['address'], i+1)

            self.setpointBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.setpointBoxes[i].setObjectName(f'setpointBox{i}')
            self.setpointBoxes[i].setEnabled(False)
            self.setpointBoxes[i].setKeyboardTracking(False)
            self.setpointBoxes[i].setStyleSheet('color: black;')
            self.setpointBoxes[i].setMaximum(100)
            self.setpointBoxes[i].setMaximumWidth(spinboxsizex)
            self.gridLayout.addWidget(self.setpointBoxes[i], rows['setpoint'], i+1)

            self.measureBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.measureBoxes[i].setObjectName(f'measureBox{i}')
            self.measureBoxes[i].setEnabled(False)
            self.measureBoxes[i].setStyleSheet('color: black;')
            self.measureBoxes[i].setMaximum(100)
            self.measureBoxes[i].setMaximumWidth(120)
            self.gridLayout.addWidget(self.measureBoxes[i], rows['measure'],i+1)

            self.setpointpctBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.setpointpctBoxes[i].setObjectName(f'setpointpctBox{i}')
            self.setpointpctBoxes[i].setEnabled(False)
            self.setpointpctBoxes[i].setStyleSheet('color: black;')
            self.setpointpctBoxes[i].setMaximum(100)
            self.setpointpctBoxes[i].setMaximumWidth(spinboxsizex)
            self.gridLayout.addWidget(self.setpointpctBoxes[i],rows['setpointpct'],i+1)

            self.measurepctBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.measurepctBoxes[i].setObjectName(f'measurepctBox{i}')
            self.measurepctBoxes[i].setEnabled(False)
            self.measurepctBoxes[i].setStyleSheet('color: black;')
            self.measurepctBoxes[i].setMaximum(100)
            self.measurepctBoxes[i].setMaximumWidth(spinboxsizex)
            self.gridLayout.addWidget(self.measurepctBoxes[i], rows['measurepct'],i+1)

            self.valveBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.valveBoxes[i].setObjectName(f'valveBox{i}')
            self.valveBoxes[i].setEnabled(False)
            self.valveBoxes[i].setStyleSheet('color: black;')
            self.valveBoxes[i].setMaximumWidth(spinboxsizex)
            self.gridLayout.addWidget(self.valveBoxes[i], rows['valve'],i+1)

            self.writeSetpointBoxes[i] = QtWidgets.QDoubleSpinBox()
            self.writeSetpointBoxes[i].setObjectName(f'writeSetpointBox{i}')
            self.writeSetpointBoxes[i].setEnabled(False)
            self.writeSetpointBoxes[i].setStyleSheet('color: black;')
            self.writeSetpointBoxes[i].setMaximum(100)
            self.writeSetpointBoxes[i].setKeyboardTracking(False)
            self.writeSetpointBoxes[i].valueChanged.connect(partial(self.setFlow, i))
            self.writeSetpointBoxes[i].setMaximumWidth(spinboxsizex)
            self.gridLayout.addWidget(self.writeSetpointBoxes[i],rows['writesp'],i+1)

            self.userTags[i] = QtWidgets.QLineEdit()
            self.userTags[i].setObjectName(f'userTag{i}')
            self.userTags[i].setEnabled(False)
            self.userTags[i].returnPressed.connect(partial(self.setUserTag, i))
            self.userTags[i].setMaximumWidth(spinboxsizex)
            self.gridLayout.addWidget(self.userTags[i],rows['usertag'],i+1)
 
        self.group.setLayout(self.gridLayout)
        self.scrollArea.setWidget(self.group)
        self.scrollArea.setFixedHeight(self.yspacing*8)
        self.outerLayout.addWidget(self.scrollArea)
        
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
            df = MFCclient(1,self.host,self.port).pollAll()
        except OSError as e:
            print("couldn't find server. Try starting it or checking host and port settings")
            raise OSError(e)
        
        self.enabledMFCs = []
        self.originalUserTags = {}
        for i in df.index.values:
            self.writeSetpointBoxes[i].setValue(df.loc[i]['fSetpoint'])
            self.enabledMFCs.append(i)
            self.originalUserTags[i] = df.loc[i]['User tag']
            self.userTags[i].setText(self.originalUserTags[i])
        self.updateMFCs(df)

    def updateMFCs(self,df):
        if len(df.columns) == 0:
            self.disableWidgets()
            return
        for i in df.index.values:
            self.addressLabels[i].setValue(df.loc[i]['address'])
            self.addressLabels[i].setStyleSheet('color: black;')
            self.setpointBoxes[i].setValue(df.loc[i]['fSetpoint'])
            self.measureBoxes[i].setValue(df.loc[i]['fMeasure'])
            self.valveBoxes[i].setValue(df.loc[i]['Valve output'])
            self.setpointpctBoxes[i].setValue(df.loc[i]['Setpoint_pct'])
            self.measurepctBoxes[i].setValue(df.loc[i]['Measure_pct'])
            self.writeSetpointBoxes[i].setEnabled(True)
            newUserTag = df.loc[i]['User tag']
            if newUserTag != self.originalUserTags[i]:
                self.userTags[i].setText(df.loc[i]['User tag'])
                self.originalUserTags[i] = newUserTag
            self.userTags[i].setEnabled(True)

    def connectLoop(self):
        if not self.running:
            self.host = self.hostInput.text()
            self.port = self.portInput.value()
            
            try:
                self.connectMFCs()
            except OSError:
                print("couldn't find server. Try starting it or checking host and port settings")
                return
            self.running = True
            self.startButton.setText('stop connection')
            self.thread = Worker(self.host,self.port, self.waittime)
            self.thread.start()
            self.thread.outputs.connect(self.updateMFCs)
        else:
            self.stopConnect()
            self.disableWidgets()

    def stopConnect(self):
        self.thread.terminate()
    
    def disableWidgets(self):
        self.running = False
        self.startButton.setText('connect MFCs')
        for i in range(self.maxMFCs):
            self.writeSetpointBoxes[i].setEnabled(False)

    def setFlow(self,i):
        if not self.running:
            return
        value = self.writeSetpointBoxes[i].value()
        address = self.addressLabels[i].value()
        print(f'setting flow to {value} on address {address}')
        MFCclient(address,self.host, self.port).writeSetpoint(value)

    def setUserTag(self,i):
        if not self.running:
            return
        value = self.userTags[i].text()
        address = self.addressLabels[i].value()
        print(f'setting flow to {value} on address {address}')
        MFCclient(address,self.host, self.port).writeName(value)

    def setFlowAll(self):
        if not self.running:
            return
        for i in self.enabledMFCs:
            self.setFlow(i)


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