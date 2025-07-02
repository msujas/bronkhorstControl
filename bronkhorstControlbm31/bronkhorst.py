import propar
import pandas as pd
import pathlib, os, json

homedir = pathlib.Path.home()
configfile = f'{homedir}/bronkhorstServerConfig/comConfg.log'

def getParamDF():
    paramDF = pd.DataFrame(columns=['dde_nr','proc_nr','parm_nr','parm_type'])
    db = propar.database().get_all_parameters()
    for dct in db:
        parmName = dct['parm_name']
        ddeNr = dct['dde_nr']
        procNr = dct['proc_nr']
        parmNr = dct['parm_nr']
        parmType = dct['parm_type']
        paramDF.loc[parmName] = [ddeNr,procNr,parmNr,parmType]
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


class MFC():
    def __init__(self,address, mfcMain):
        self.address = address
        self.mfcMain = mfcMain
        self.com = mfcMain.comport
        self.pollparams = ['User tag', 'Control mode', 'Fluid name', 'Fluidset index','fMeasure', 'fSetpoint', 
                  'Measure', 'Setpoint', 'Valve output']
        self.ddenrs = paramDF['dde_nr'].loc[self.pollparams].values
        self.getAddresses()
        #self.pollparamList = propar.database().get_parameters(self.ddenrs)
    def __str__(self):
        return self.readName()
    def getCom(self, com=None):
        if not com and os.path.exists(configfile):
            f = open(configfile,'r')
            comno = f.read()
            f.close()
            return f'COM{comno}'
        return com
    def getNumbers(self,name):
        proc_nr = paramDF.loc[name]['proc_nr']
        parm_nr = paramDF.loc[name]['parm_nr']
        parm_type = paramDF.loc[name]['parm_type']
        return proc_nr, parm_nr, parm_type
    def getddes(self,*names):
        return paramDF['dde_nr'].loc[list(names)].values

    def readParam(self,name, address = None):
        if address == None:
            address = self.address
        proc_nr, parm_nr, parm_type = self.getNumbers(name)
        parValue = self.mfcMain.master.read(address,proc_nr,parm_nr,parm_type)
        return parValue
    def readParams(self,ddeList, address=None):
        if not address:
            address = self.address
        paramdctlist = propar.database().get_parameters(ddeList)
        datalist = propar.instrument(self.com, address=address).read_parameters(paramdctlist)
        datadct = {}
        datadct['address'] = address
        for d in datalist:
            datadct[d['parm_name']] = d['data']
        return datadct
    def readParams_names(self, *names,address=None):
        ddes = self.getddes(*names)
        return self.readParams(ddes,address=address)
    def readParams_namesAllAddress(self,*names):
        datadct_all = {}
            
        for c,a in enumerate(self.addresses):
            dct = self.readParams_names(*names, address=a)
            for par in dct:
                if c == 0:
                    datadct_all[par] = []
                datadct_all[par].append(dct[par])
        return datadct_all
    
    def readParams_allAddsPars(self):
        return self.readParams_namesAllAddress(*self.pollparams)

    def writeParam(self,name, value):
        proc_nr, parm_nr, parm_type = self.getNumbers(name)
        x = self.mfcMain.master.write(self.address,proc_nr,parm_nr,parm_type,value)
        return x
    def writeSetpoint(self,value):
        name = self.readName()
        value = float(value)
        print(f'setting {name} to {value} ml/min')
        x =  self.writeParam('fSetpoint',value)
        return self.readSetpoint()
        
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
    def writeName(self,name):
        x = self.writeParam('User tag',name)
        newname = self.readName()
        return newname
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
        newvalue = self.readControlMode()
        return newvalue
    def readFluidType(self):
        name = self.readName()
        fluiddct = self.readParams_names('Fluidset index', 'Fluid name')
        print(fluiddct)
        return fluiddct
    
    def writeFluidIndex(self,value):
        value = int(value)
        x = self.writeParam('Fluidset index',value)
        newIndex = self.readFluidType()
        return newIndex
    def readValve(self):
        value = self.readParam('Valve output')
        valve = value/2**24
        return valve
    def testMessage(self):
        return 'a'*1000 + 'b'*1000
    
    def pollAll(self):
        datadct = {}
        for par in ['address']+self.pollparams:
            datadct[par] = []
        for a in self.addresses:
            datadcttmp = self.readParams(self.ddenrs, a)
            for par in datadcttmp:
                datadct[par].append(datadcttmp[par])
        df = pd.DataFrame.from_dict(datadct)
        df['Measure'] = df['Measure'].apply(lambda x: x*100/32000)
        df['Setpoint'] = df['Setpoint'].apply(lambda x: x*100/32000)
        df['Valve output'] = df['Valve output'].apply(lambda x: x/2**24)
        df = df.rename({'Measure':'Measure_pct', 'Setpoint':'Setpoint_pct'}, axis = 1)
        return df
    def pollAllServer(self):
        df = self.pollAll()
        print(df)
        dfstring = ';'.join(df.columns)
        for i in df.index.values:
            dfstring += '\n'
            dfstring += ';'.join([str(x) for x in df.loc[i]])
        return dfstring
    
    def readMeasure_pct(self):
        m = self.readParam('Measure')
        m_pct = m*100/32000
        return m_pct
    def readSetpoint_pct(self):
        sp = self.readParam('Setpoint')
        sp_pct = sp*100/32000
        return sp_pct
    def writeSetpoint_pct(self,value_pct):
        value = int(value_pct*32000/100)
        self.writeParam('Setpoint', value)
        return self.readSetpoint_pct()
        
    def wink(self):
        if not self.com:
            print('com needs to be defined to run this')
            return
        return propar.instrument(self.com, self.address).wink()
    def strToMethod(self,inputString):
        stringSplit = inputString.split(';')
        #address = stringSplit[0]
        methodName = stringSplit[1]
        args = stringSplit[2:]
        methodDct = {'readName': self.readName, 'readParam':self.readParam,
                     'readSetpoint':self.readSetpoint, 'writeSetpoint':self.writeSetpoint,
                     'writeParam':self.writeParam, 'readFlow':self.readFlow,
                     'getAddresses': self.getAddresses, 'pollAll':self.pollAllServer,
                     'readControlMode': self.readControlMode, 'writeControlMode': self.writeControlMode,
                     'readFluidType':self.readFluidType, 'writeFluidIndex':self.writeFluidIndex,
                     'writeName':self.writeName, 'readMeasure_pct': self.readMeasure_pct,
                     'readSetpoint_pct': self.readSetpoint_pct, 'wink':self.wink,
                     'readValve': self.readValve, 'readParams_names':self.readParams_names,
                     'readParams_allAddsPars':self.readParams_allAddsPars,'testMessage':self.testMessage}
        method = methodDct[methodName]
        val = method(*args)
        if type(val) == dict:
            return json.dumps(val)
        return val

    




