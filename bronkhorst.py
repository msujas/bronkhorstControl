import propar
import pandas as pd

def getParamDF():
    paramDF = pd.DataFrame(columns=['proc_nr','parm_nr','parm_type'])
    db = propar.database().get_all_parameters()
    for dct in db:
        parmName = dct['parm_name']
        procNr = dct['proc_nr']
        parmNr = dct['parm_nr']
        parmType = dct['parm_type']
        paramDF.loc[parmName] = [procNr,parmNr,parmType]
    return paramDF

paramDF = getParamDF()

print(paramDF)

print(paramDF.loc['User tag'])
class MFC():
    def __init__(self,address):
        self.address = address
        self.paramDF = getParamDF()
        self.mfc = propar.instrument('COM1')
    def getNumbers(self,name):
        proc_nr = self.paramDF.loc[name]['proc_nr']
        parm_nr = self.paramDF.loc[name]['parm_nr']
        parm_type = self.paramDF.loc[name]['parm_type']
        return proc_nr, parm_nr, parm_type
    def readParam(self,name):
        proc_nr, parm_nr, parm_type = self.getNumbers(name)
        print(self.mfc.master.read(self.address,proc_nr,parm_nr,parm_type))
    def writeParam(self,name):
        proc_nr, parm_nr, parm_type = self.getNumbers(name)
        self.mfc.master.write(self.address,proc_nr,parm_nr,parm_type)
    def writeSetpoint(self):
        self.writeParam('fSetpoint')
    def readSetpoint(self):
        self.readParam('fSetpoint')
    def readFlow(self):
        self.readParam('fMeasure')

'''   
mfc1 = MFC(1)
mfc2 = MFC(2)
mfc3 = MFC(3)
mfc4 = MFC(4)
mfc5 = MFC(5)
'''
