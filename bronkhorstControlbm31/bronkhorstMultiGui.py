from PyQt6 import QtCore,QtWidgets, QtGui
import pandas as pd
from .bronkhorstClient import MFCclient
from .guiLayout import guiLayout, formatLayouts
from .bronkhorstGui import parseArguments
import time
from .plotters import clientlogdir
import logging

logger = logging.getLogger()

class MultiWorker():
    outputs = QtCore.pyqtSignal(pd.DataFrame)
    def __init__(self,hosts,ports, waittime = 1):
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
            dfAll = pd.concat([self.dfs[i] for i in self.dfs], axis=0)
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

class MultiServerGui(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.centralWidget = QtWidgets.QWidget()
        self.centralWidget.setObjectName("centralWidget")
        self.setWindowTitle('bronkhorst multi server GUI')
        self.maxMFCs = parseArguments()
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
        guiLayout(self)
        self.hostBoxes = {}
        self.portBoxes = {}
        for i in range(self.maxMFCs):
            self.hostBoxes[i] = QtWidgets.QLineEdit()
            self.hostBoxes[i].setObjectName(f'hostBoxes{i}')
            self.hostBoxes[i].setEnabled(False)
            self.gridLayout.addWidget(self.hostBoxes[i], self.rows['host'],i+1)

            self.portBoxes[i] = QtWidgets.QLineEdit()
            self.portBoxes[i].setObjectName(f'hostBoxes{i}')
            self.portBoxes[i].setEnabled(False)
            self.gridLayout.addWidget(self.portBoxes[i], self.rows['port'],i+1)
        
        self.hostBoxLabel = QtWidgets.QLabel()
        self.hostBoxLabel.setObjectName('hostBoxLabel')
        self.hostBoxLabel.setText('host name')
        self.leftLayout.addWidget(self.hostBoxLabel, self.rows['host'], 0)

        self.portBoxLabel = QtWidgets.QLabel()
        self.portBoxLabel.setObjectName('portBoxLabel')
        self.portBoxLabel.setText('port')
        self.leftLayout.addWidget(self.portBoxLabel, self.rows['port'],0)

        formatLayouts(self)

        self.centralWidget.setLayout(self.outerLayout)
        self.setCentralWidget(self.centralWidget)
        QtCore.QMetaObject.connectSlotsByName(self)

    def setClientLogDir(self):
        pass
    def repoll(self):
        pass
    def wink(self, index):
        pass
    def setControlMode(self,index):
        pass
    def setFluidIndex(self,index):
        pass
    def setSlope(self,index):
        pass
    def setFlow(self,index):
        pass
    def setUserTag(self,index):
        pass

import sys
def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = MultiServerGui()
    ui.show()
    sys.exit(app.exec())