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

def strToFloat(string):
    try:
        x = float(string)
        return x
    except:
        return string

paramDF = getParamDF()
def startMfc(com = 'COM1'):
    mfcMain = propar.instrument(com)
    return mfcMain
#mfcMain = propar.instrument('COM1')
#nodes = mfcMain.master.get_nodes()
class MFC():
    def __init__(self,address, mfcMain):
        self.address = address
        self.mfcMain = mfcMain
    def __str__(self):
        return self.readName()
    def getNumbers(self,name):
        proc_nr = paramDF.loc[name]['proc_nr']
        parm_nr = paramDF.loc[name]['parm_nr']
        parm_type = paramDF.loc[name]['parm_type']
        return proc_nr, parm_nr, parm_type
    def readParam(self,name):
        proc_nr, parm_nr, parm_type = self.getNumbers(name)
        parValue = self.mfcMain.master.read(self.address,proc_nr,parm_nr,parm_type)
        print(parValue)
        return parValue
    def writeParam(self,name, value):
        proc_nr, parm_nr, parm_type = self.getNumbers(name)
        x = self.mfcMain.master.write(self.address,proc_nr,parm_nr,parm_type,value)
        return x
    def writeSetpoint(self,value):
        return self.writeParam('fSetpoint',value)
    def readSetpoint(self):
        sp = self.readParam('fSetpoint')
        return sp
    def readFlow(self):
        flowRate = self.readParam('fMeasure')
        return flowRate
    def readName(self):
        name = self.readParam('User tag')
        print(name)
        return name
    def getAddresses(self):
        nodes = self.mfcMain.master.get_nodes()
        self.addresses = [n['address'] for n in nodes]
        addressesString = ' '.join([str(a) for a in self.addresses])
        return addressesString
    def strToMethod(self,inputString):
        stringSplit = inputString.split()
        address = stringSplit[0]
        methodName = stringSplit[1]
        args = stringSplit[2:]
        for i in range(len(args)):
            args[i] = strToFloat(args[i])
        methodDct = {'readName': self.readName, 'readParam':self.readParam,
                     'readSetpoint':self.readSetpoint, 'writeSetpoint':self.writeSetpoint,
                     'writeParam':self.writeParam, 'readFlow':self.readFlow,
                     'getAddresses': self.getAddresses}
        method = methodDct[methodName]
        val = method(*args)
        return val
    
class MFCMain():
    def __init__(self,mfcmain):
        self.mfcmain = mfcmain
        self.getAddresses()
    def getAddresses(self):
        nodes = self.mfcMain.master.get_nodes()
        self.addresses = [n['address'] for n in nodes]
        #print(self.addresses)
        return self.addresses
    def pollAll(self):
        self.getAddresses()
        params = ['fMeasure', 'fSetpoint']
        df = pd.DataFrame(columns=params)
        for a in self.addresses:
            userTag = MFC(a).readName()
            values = []
            for p in params:
                values.append(self.readParam(p,a))
            df.loc[userTag] = values
        self.paramDf = df
        #print(self.paramDf)
        return df



