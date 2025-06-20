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
        self.MainWindow.resize(800, 350)
        self.MainWindow.setWindowTitle('Bronkhorst GUI')
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.maxMFCs, self.waittime = parseArguments()
        self.box1x = 70
        self.box1y = 20
        self.xspacing = 90
        self.yspacing = 35

        self.startButton = QtWidgets.QPushButton(self.centralwidget)
        self.startButton.setObjectName('startButton')
        self.startButton.setGeometry(QtCore.QRect(self.box1x-int(self.yspacing*1), self.box1y+int(self.yspacing*8), 120, 30))
        self.startButton.setText('connect MFCs')
        #self.startButton.adjustSize()

        self.hostInput = QtWidgets.QLineEdit(self.centralwidget)
        self.hostInput.setObjectName('hostInput')
        self.hostInput.setGeometry(QtCore.QRect(self.box1x+self.xspacing,self.box1y+self.yspacing*8, 100,20))
        self.hostInput.setText(HOST)

        self.hostLabel = QtWidgets.QLabel(self.centralwidget)
        self.hostLabel.setObjectName('hostLabel')
        self.hostLabel.setGeometry(QtCore.QRect(self.box1x+int(self.xspacing*1.1),self.box1y+int(self.yspacing*8.7), 100,20))
        self.hostLabel.setText('host name')

        self.portInput = QtWidgets.QSpinBox(self.centralwidget)
        self.portInput.setObjectName('portInput')
        self.portInput.setGeometry(QtCore.QRect(self.box1x+int(self.xspacing*2.2),self.box1y+int(self.yspacing*8), 100,20))
        self.portInput.setMaximum(2**16)
        self.portInput.setMinimum(8000)
        self.portInput.setValue(PORT)

        self.portLabel = QtWidgets.QLabel(self.centralwidget)
        self.portLabel.setObjectName('portLabel')
        self.portLabel.setGeometry(QtCore.QRect(self.box1x+int(self.xspacing*2.3),self.box1y+int(self.yspacing*8.7), 100,20))
        self.portLabel.setText('port value')

        self.addressLabel = QtWidgets.QLabel(self.centralwidget)
        self.addressLabel.setObjectName('addressLabel')
        self.addressLabel.setGeometry(QtCore.QRect(self.box1x-int(self.xspacing*0.7), self.box1y, 50,20))
        self.addressLabel.setText('addresses')
        self.addressLabel.adjustSize()

        self.spLabel = QtWidgets.QLabel(self.centralwidget)
        self.spLabel.setObjectName('spLabel')
        self.spLabel.setGeometry(QtCore.QRect(self.box1x-int(self.xspacing*0.6), self.box1y+self.yspacing, 50,20))
        self.spLabel.setText('setpoint')

        self.measureLabel = QtWidgets.QLabel(self.centralwidget)
        self.measureLabel.setObjectName('measureLabel')
        self.measureLabel.setGeometry(QtCore.QRect(self.box1x-int(self.xspacing*0.6), self.box1y+self.yspacing*2, 50,20))
        self.measureLabel.setText('measure')

        self.sppctLabel = QtWidgets.QLabel(self.centralwidget)
        self.sppctLabel.setObjectName('sppctLabel')
        self.sppctLabel.setGeometry(QtCore.QRect(self.box1x-int(self.xspacing*0.7), self.box1y+self.yspacing*3, 50,20))
        self.sppctLabel.setText('setpoint(%)')
        self.sppctLabel.adjustSize()

        self.measurepctLabel = QtWidgets.QLabel(self.centralwidget)
        self.measurepctLabel.setObjectName('measurepctLabel')
        self.measurepctLabel.setGeometry(QtCore.QRect(self.box1x-int(self.xspacing*0.7), self.box1y+self.yspacing*4, 50,20))
        self.measurepctLabel.setText('measure(%)')
        self.measurepctLabel.adjustSize()

        self.valveLabel = QtWidgets.QLabel(self.centralwidget)
        self.valveLabel.setObjectName('valveLabel')
        self.valveLabel.setGeometry(QtCore.QRect(self.box1x-int(self.xspacing*0.6), self.box1y+int(self.yspacing*4.8), 50,20))
        self.valveLabel.setText('valve\noutput')
        self.valveLabel.adjustSize()

        self.writespLabel = QtWidgets.QLabel(self.centralwidget)
        self.writespLabel.setObjectName('writespLabel')
        self.writespLabel.setGeometry(QtCore.QRect(self.box1x-int(self.xspacing*0.6), self.box1y+int(self.yspacing*5.8), 50,20))
        self.writespLabel.setText('write\nsetpoint')
        self.writespLabel.adjustSize()

        self.userTagLabel = QtWidgets.QLabel(self.centralwidget)
        self.userTagLabel.setObjectName('userTagLabel')
        self.userTagLabel.setGeometry(QtCore.QRect(self.box1x-int(self.xspacing*0.6), self.box1y+int(self.yspacing*7), 50,20))
        self.userTagLabel.setText('user tag')
        self.userTagLabel.adjustSize()

        '''
        self.writesppctLabel = QtWidgets.QLabel(self.centralwidget)
        self.writesppctLabel.setObjectName('writesppctLabel')
        self.writesppctLabel.setGeometry(QtCore.QRect(self.box1x-int(self.xspacing*0.7), self.box1y+int(self.yspacing*6.8), 50,20))
        self.writesppctLabel.setText('write\nsetpoint(%)')
        self.writesppctLabel.adjustSize()
        '''

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
            self.addressLabels[i] = QtWidgets.QSpinBox(self.centralwidget)
            self.addressLabels[i].setObjectName(f'addressLabel{i}')
            self.addressLabels[i].setMinimum(-1)
            self.addressLabels[i].setMaximum(99)
            self.addressLabels[i].setValue(-1)
            self.addressLabels[i].setGeometry(QtCore.QRect(self.box1x+self.xspacing*i, self.box1y, 20, 20))
            self.addressLabels[i].setEnabled(False)

            self.setpointBoxes[i] = QtWidgets.QDoubleSpinBox(self.centralwidget)
            self.setpointBoxes[i].setObjectName(f'setpointBox{i}')
            self.setpointBoxes[i].setGeometry(QtCore.QRect(self.box1x+self.xspacing*i, self.box1y+self.yspacing, 50, 20))
            self.setpointBoxes[i].setEnabled(False)
            self.setpointBoxes[i].setKeyboardTracking(False)
            self.setpointBoxes[i].setStyleSheet('color: black;')
            self.setpointBoxes[i].setMaximum(100)

            self.measureBoxes[i] = QtWidgets.QDoubleSpinBox(self.centralwidget)
            self.measureBoxes[i].setObjectName(f'measureBox{i}')
            self.measureBoxes[i].setGeometry(QtCore.QRect(self.box1x+self.xspacing*i, self.box1y+self.yspacing*2, 50, 20))
            self.measureBoxes[i].setEnabled(False)
            self.measureBoxes[i].setStyleSheet('color: black;')
            self.measureBoxes[i].setMaximum(100)

            self.setpointpctBoxes[i] = QtWidgets.QDoubleSpinBox(self.centralwidget)
            self.setpointpctBoxes[i].setObjectName(f'setpointpctBox{i}')
            self.setpointpctBoxes[i].setGeometry(QtCore.QRect(self.box1x+self.xspacing*i, self.box1y+self.yspacing*3, 50, 20))
            self.setpointpctBoxes[i].setEnabled(False)
            self.setpointpctBoxes[i].setStyleSheet('color: black;')
            self.setpointpctBoxes[i].setMaximum(100)

            self.measurepctBoxes[i] = QtWidgets.QDoubleSpinBox(self.centralwidget)
            self.measurepctBoxes[i].setObjectName(f'measurepctBox{i}')
            self.measurepctBoxes[i].setGeometry(QtCore.QRect(self.box1x+self.xspacing*i, self.box1y+self.yspacing*4, 50, 20))
            self.measurepctBoxes[i].setEnabled(False)
            self.measurepctBoxes[i].setStyleSheet('color: black;')
            self.measurepctBoxes[i].setMaximum(100)

            self.valveBoxes[i] = QtWidgets.QDoubleSpinBox(self.centralwidget)
            self.valveBoxes[i].setObjectName(f'valveBox{i}')
            self.valveBoxes[i].setGeometry(QtCore.QRect(self.box1x+self.xspacing*i, self.box1y+self.yspacing*5, 50, 20))
            self.valveBoxes[i].setEnabled(False)
            self.valveBoxes[i].setStyleSheet('color: black;')

            self.writeSetpointBoxes[i] = QtWidgets.QDoubleSpinBox(self.centralwidget)
            self.writeSetpointBoxes[i].setObjectName(f'writeSetpointBox{i}')
            self.writeSetpointBoxes[i].setGeometry(QtCore.QRect(self.box1x+self.xspacing*i, self.box1y+self.yspacing*6, 50, 20))
            self.writeSetpointBoxes[i].setEnabled(False)
            self.writeSetpointBoxes[i].setStyleSheet('color: black;')
            self.writeSetpointBoxes[i].setMaximum(100)
            self.writeSetpointBoxes[i].setKeyboardTracking(False)
            self.writeSetpointBoxes[i].valueChanged.connect(partial(self.setFlow, i))

            self.userTags[i] = QtWidgets.QLineEdit(self.centralwidget)
            self.userTags[i].setObjectName(f'userTag{i}')
            self.userTags[i].setGeometry(QtCore.QRect(self.box1x+self.xspacing*i, self.box1y+self.yspacing*7, 80, 20))
            self.userTags[i].setEnabled(False)
            #self.userTags[i].setKeyboardTracking(False)
            self.userTags[i].returnPressed.connect(partial(self.setUserTag, i))

            '''
            self.writeSetpointpctBoxes[i] = QtWidgets.QDoubleSpinBox(self.centralwidget)
            self.writeSetpointpctBoxes[i].setObjectName(f'writeSetpointpctBox{i}')
            self.writeSetpointpctBoxes[i].setGeometry(QtCore.QRect(self.box1x+self.xspacing*i, self.box1y+self.yspacing*7, 50, 20))
            self.writeSetpointpctBoxes[i].setEnabled(False)
            self.writeSetpointpctBoxes[i].setStyleSheet('color: black;')
            self.writeSetpointpctBoxes[i].setMaximum(100)
            self.writeSetpointpctBoxes[i].setKeyboardTracking(False)
            self.writeSetpointBoxes[i].valueChanged.connect(partial(self.setFlowPct, i))
            '''
            
        
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
        #print(df)
        
        self.enabledMFCs = []
        self.originalUserTags = {}
        for i in df.index.values:
            self.writeSetpointBoxes[i].setValue(df.loc[i]['fSetpoint'])
            #self.writeSetpointpctBoxes[i].setValue(df.loc[i]['Setpoint_pct'])
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
    '''
    def setFlowPct(self,i):
        #function does not exist yet
        if not self.running:
            return
        value = self.writeSetpointpctBoxes[i].value()
        address = self.addressLabels[i].value()
        MFCclient(address, self.host, self.port).writeSetpointPct(value)
    '''

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