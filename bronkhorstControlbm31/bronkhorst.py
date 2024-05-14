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
    def readParam(self,name, address = None):
        if address == None:
            address = self.address
        proc_nr, parm_nr, parm_type = self.getNumbers(name)
        parValue = self.mfcMain.master.read(address,proc_nr,parm_nr,parm_type)
        return parValue
    def writeParam(self,name, value):
        proc_nr, parm_nr, parm_type = self.getNumbers(name)
        x = self.mfcMain.master.write(self.address,proc_nr,parm_nr,parm_type,value)
        return x
    def writeSetpoint(self,value):
        name = self.readName()
        value = float(value)
        print(f'setting {name} to {value} ml/min')
        return self.writeParam('fSetpoint',value)
    def readSetpoint(self):
        sp = self.readParam('fSetpoint')
        name = self.readName()
        print(f'{name} setpoint {sp} ml/min')
        return sp
    def readFlow(self):
        flowRate = self.readParam('fMeasure')
        name = self.readName()
        print(f'{name} flow {flowRate} ml/min')
        return flowRate
    def readName(self):
        name = self.readParam('User tag')
        return name
    def getAddresses(self):
        nodes = self.mfcMain.master.get_nodes()
        self.addresses = [n['address'] for n in nodes]
        addressesString = ' '.join([str(a) for a in self.addresses])
        return addressesString
    def readAddresses(self):
        return self.getAddresses()
    def readControlMode(self):
        mode = self.readParam('Control mode')
        name = self.readName()
        print(f'{name} control mode: {mode}')
        return mode
    def writeControlMode(self, value):
        value = int(value)
        x = self.writeParam('Control mode', value)
        return x
    def readFluidType(self):
        name = self.readName()
        fluidIndex = self.readParam('Fluidset index')
        fluidName = self.readParam('Fluid name')
        print(f'{name} fluid: {fluidName}, fluid index: {fluidIndex}')
        return fluidName, fluidIndex
    def writeFluidIndex(self,value):
        value = int(value)
        x = self.writeParam('Fluidset index',value)
        self.readFluidType()
        return x
    def strToMethod(self,inputString):
        stringSplit = inputString.split()
        _address = stringSplit[0]
        methodName = stringSplit[1]
        args = stringSplit[2:]
        methodDct = {'readName': self.readName, 'readParam':self.readParam,
                     'readSetpoint':self.readSetpoint, 'writeSetpoint':self.writeSetpoint,
                     'writeParam':self.writeParam, 'readFlow':self.readFlow,
                     'getAddresses': self.getAddresses, 'pollAll':self.pollAll,
                     'readControlMode': self.readControlMode, 'writeControlMode': self.writeControlMode,
                     'readFluidType':self.readFluidType, 'writeFluidIndex':self.writeFluidIndex}
        method = methodDct[methodName]
        val = method(*args)
        return val
    def pollAll(self):
        self.getAddresses()
        params = ['User tag', 'Control mode', 'Fluid name', 'Fluidset index','fMeasure', 'fSetpoint']
        df = pd.DataFrame(columns=['address']+params)
        for a in self.addresses:
            values = [a]
            for p in params:
                values.append(self.readParam(p,a))
            df.loc[a] = values
        df.set_index('address')
        self.paramDf = df
        print(self.paramDf)
        return df
    




