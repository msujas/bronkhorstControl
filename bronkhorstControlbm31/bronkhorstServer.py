import socket
from bronkhorstControlbm31.bronkhorst import MFC, startMfc, configfile
import os, pathlib
import argparse
import selectors, types
import subprocess
import logging
from .verbose import Verbose

logger = logging.getLogger()
homedir = pathlib.Path.home()
logdir = 'bronkhorstLogger'
fulllogdir = f'{homedir}/{logdir}'
os.makedirs(fulllogdir,exist_ok=True)
logfile = f'{homedir}/{logdir}/bronkhorstServer.log'

DEBUG = False
def dprint(*args,**kwargs):
    if DEBUG:
        print(*args,**kwargs)

HOST = 'localhost'
PORT = 61245
com = 'COM1'

def getIP():
    p = subprocess.run('ipconfig',capture_output=True,text=True)
    ipLine = [l for l in p.stdout.split('\n') if 'IPv4 Address' in l][0]
    ip = ipLine.split()[-1]
    return ip

def isValidIP(ipaddress):
    try:
        hostname = socket.gethostbyaddr(ipaddress)[0].split('.')[0]
        return hostname.lower() == socket.gethostname().lower()
    except:
        return False
    

if not os.path.exists(os.path.dirname(configfile)):
    os.makedirs(os.path.dirname(configfile))

def getArgs(port=PORT):
    parser = argparse.ArgumentParser()
    parser.add_argument('host',nargs='?', default='local', help = ('can be "local" (localhost), "remote" (host name), '
                                            '"remoteip" (ip address), or the IP address of the host. The last two options are '
                                            'due to complications which may arise from a host having multiple connections'))

    if not os.path.exists(configfile):
        defaultCom = 1
    else:
        f = open(configfile,'r')
        defaultCom = f.read()
        f.close()
    parser.add_argument('-c','--com', default=defaultCom, help=('COM port (as number, e.g. -c 1) where MFCs are connected to. '
                                                                'If unsure, check in Device Manager under Ports. Default is last used'))
    parser.add_argument('-p','--port',default=port, type=int, help= ('port number. There is a default, but you can choose. Anything from '
                                                                '49152-65535 should be fine'))
    parser.add_argument('-a','--accepted-hosts', default = None, type = str, help= ('list of comma separated hosts that can be'
                                                                                    'accepted (default - accept all). E.g. -a pc1,pc2'))
    parser.add_argument('-d','--debug', action='store_true')
    parser.add_argument('-v','--verbose',default= 0, type=  int, help = 'verbose level, integer. -1 -> 1, default 0')

    args = parser.parse_args()
    f = open(configfile,'w')
    f.write(str(args.com))
    f.close()
    com = f'COM{args.com}'
    PORT = args.port
    print(f'MFCs on {com}')
    print(f'port: {PORT}')
    host = args.host
    debug = args.debug
    vlevel = args.verbose
    acceptedHosts = None
    if args.accepted_hosts:
        acceptedHosts = args.accepted_hosts.split(',')
    
    if host == 'local':
        host = 'localhost'
    elif host == 'remote':
        host = socket.gethostname()
    elif host == 'remoteip':
        host = getIP() #added this option as connection may not work with host name if host has multiple connections
    elif isValidIP(host):
        pass
    else:
        print('usage bronkorstServer [host]')
        print('host must must be "local", "remote", "remoteip" or nothing (local)')
        return
    print(host)
    return com, PORT, host, acceptedHosts, debug, vlevel
def run(port = PORT):
    com, port, host, acceptedHosts, debug,vlevel = getArgs()
    
    if not acceptedHosts:
        ahstring = 'all'
    else:
        ahstring = ','.join(acceptedHosts)
        acceptedIPs = [socket.gethostbyname(h) for h in acceptedHosts]
    print(f'accepted hosts: {ahstring}')
    print('running single client server')
    mfcMain = startMfc(com)
    mfc = MFC(0,mfcMain, vlevel=vlevel)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                hostName = addr[0]
                if acceptedHosts and hostName not in acceptedHosts and hostName not in acceptedIPs:
                    print(f'{hostName} not in accepted hosts, closing connection')
                    continue
                print(f"Connected by {addr}")
                while True:
                    try:
                        data = conn.recv(1024)
                    except (ConnectionAbortedError, ConnectionResetError):
                        print('connection lost with client')
                        data = b''
                    if not data:
                        break
                    strdata = data.decode()
                    try:
                        address = int(strdata.split(';')[0])
                        mfc.address = address
                        print(strdata)
                        result = mfc.strToMethod(strdata)
                        result += '!'
                        
                    except (ValueError, KeyError):
                        byteResult = b'invalid input!'
                    resultsplit = result
                    while len(resultsplit) > 1024:
                        resultsplit = resultsplit[:1024]
                        byteResult = bytes(str(resultsplit),encoding = 'utf-8')
                        print(f'sending data to {addr}')
                        conn.sendall(byteResult)

class BronkhorstServer():
    def __init__(self):
        com,self.port, self.host, self.acceptedHosts, self.debug, vlevel = getArgs()
        mfcMain = startMfc(com)
        print('connecting to MFCs...')
        try:
            self.mfc = MFC(0,mfcMain, vlevel=vlevel)
        except Exception as e:
            print(e)
            print(f"couldn't connect to MFCs on {com}. Check connection")
            exit()
        print('connected to MFCs')
        self.v = Verbose(vlevel)
        
    def accept_wrapper(self,sock,sel):
        conn,addr =sock.accept()
        conn.setblocking(False)
        self.v.print(f'Accepted connection from {addr}',plevel=1)
        data = types.SimpleNamespace(addr=addr,inb = b'',outb = b'')
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        sel.register(conn,events,data=data)

    def service_connection(self,key,mask,sel):
        sock = key.fileobj
        data = key.data
        #logger.debug(f'accepted connection from {data.addr}')
        connectionLostMessage = f'connection lost with client: {data.addr}'
        #data.outb = b''
        def closeConnection():
            self.v.print(f'closing connection to {data.addr}', plevel=1)
            sel.unregister(sock)
            sock.close()
        if self.acceptedHosts:
            acceptedIPs = [socket.gethostbyname(h) for h in self.acceptedHosts]
            hostName = data.addr[0]
            if hostName not in self.acceptedHosts and hostName not in acceptedIPs:
                print('host name not in accepted hosts')
                closeConnection()
                return
        if mask & selectors.EVENT_READ:
            try:
                recvData = sock.recv(1024)
                
            except (ConnectionAbortedError, ConnectionResetError):
                
                print(connectionLostMessage)
                logger.info(connectionLostMessage)
                recvData = b''
            if recvData:
                self.v.print(recvData,plevel=1)
                data.inb += recvData
                while b'!' in data.inb:
                    bmessage, data.inb = data.inb.split(b'!',1)
                    dprint(f'message received {bmessage!r}')
                    strmessage = bmessage.decode()
                    if not strmessage:
                        continue
                    try:
                        address = int(strmessage.split(';')[0])
                        self.mfc.address = address
                        mainmessage = self.mfc.strToMethod(strmessage)
                        #endmessageMarker = '!'
                        fullmessage = f'{mainmessage}!'
                        dprint(f'return message: {fullmessage}')
                        data.outb += bytes(fullmessage,encoding='utf-8')
                    except (ValueError, KeyError):
                        data.outb += f'invalid message: {bmessage!r}!'.encode()
                    except ConnectionResetError:
                        print(f'connection lost with client: {data.addr}')
                        data.outb = b''
                        closeConnection()
                        return
                
            else:
                logger.debug(f'no data received from {data.addr}')
                closeConnection()
                return
            dprint('finished reading')
        if mask & selectors.EVENT_WRITE and data.outb:
            self.v.print(f'sending data to {data.addr}', plevel=1)
            try:
                dprint(f'sending {data.outb!r}')
                sent = sock.send(data.outb)
                data.outb = data.outb[sent:]
                #logger.debug(f'data sent to {data.addr}')
            except ConnectionResetError:
                print(connectionLostMessage)
                logger.info(connectionLostMessage)
                data.outb = b''
                closeConnection()
                return
        wanted = selectors.EVENT_READ | (selectors.EVENT_WRITE if data.outb else 0)
        dprint(f'end: mask={mask} registered={key.events} wanted={wanted} outb={data.outb!r}')
        if wanted != key.events: 
            sel.modify(sock, wanted, data = data)
        dprint('service_connection done')

    def multiServer(self):
        
        loglevel = logging.INFO
        if self.debug:
            loglevel = logging.DEBUG
        logging.basicConfig(filename=logfile, level = loglevel, format = '%(asctime)s %(levelname)-8s %(message)s',
                            datefmt = '%Y/%m/%d_%H:%M:%S')
        logger.info('server started')
        
        allhosts = []
        if not self.acceptedHosts:
            ahstring = 'all'
        else:
            ahstring = ','.join(self.acceptedHosts)
        print(f'accepted hosts: {ahstring}')

        sel = selectors.DefaultSelector()
        print('running multiServer')
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        s.listen()
        #s.settimeout(5)
        s.setblocking(False)
        sel.register(s,selectors.EVENT_READ,data=None)

        try:
            while True:
                events = sel.select(timeout=1)
                for key, mask in events:
                    dprint(f'event: fd={key.fileobj.fileno()} mask={mask} data = {key.data is not None}')
                    if key.data is None:
                        self.accept_wrapper(key.fileobj,sel)
                    else:
                        hostname = socket.gethostbyaddr(key.data.addr[0])
                        if not hostname in allhosts:
                            allhosts.append(hostname)
                            logger.info(f'new client {hostname}')
                            self.v.print(f'connection from {hostname}')
                        self.service_connection(key, mask,sel)
                dprint('iter')
        except KeyboardInterrupt:
            logger.info('keyboard interupt')
            print("caught keyboard interrupt, exiting")
        except Exception as e:
            logger.exception(e)
            raise e
        finally:
            sel.close()

def runMulti():
    BronkhorstServer().multiServer()