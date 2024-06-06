import socket
from bronkhorstControlbm31.bronkhorst import MFC, startMfc
import os, pathlib
import argparse
import selectors, types
import subprocess

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
        if hostname.lower() == socket.gethostname().lower():
            return True
        else:
            return False
    except:
        return False
    
homedir = pathlib.Path.home()
configfile = f'{homedir}/bronkhorstServerConfig/comConfg.log'
if not os.path.exists(os.path.dirname(configfile)):
    os.makedirs(os.path.dirname(configfile))

def getParsers(port=PORT):
    parser = argparse.ArgumentParser()
    parser.add_argument('host',nargs='?', default='local', help = ('can be "local" (localhost), "remote" (host name), '
                                                                   '"remoteip" (ip address), or the IP address of the host'))

    if not os.path.exists(configfile):
        defaultCom = 1
    else:
        f = open(configfile,'r')
        defaultCom = f.read()
        f.close()
    parser.add_argument('-c','--com', default=defaultCom)
    parser.add_argument('-p','--port',default=port)
    args = parser.parse_args()
    f = open(configfile,'w')
    f.write(str(args.com))
    f.close()
    com = f'COM{args.com}'
    PORT = int(args.port)
    print(f'port: {PORT}')
    host = args.host
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
    return com, port, host

def run(port = PORT):

    com, port, host = getParsers()
    mfcMain = startMfc(com)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        s.bind((host, port))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    try:
                        data = conn.recv(1024)
                    except ConnectionAbortedError:
                        data = b''
                    if not data:
                        break
                    strdata = data.decode()
                    try:
                        address = int(strdata.split(';')[0])
                        print(strdata)
                        result = MFC(address, mfcMain).strToMethod(strdata)
                        print(result)
                    except (ValueError, KeyError):
                        byteResult = b'invalid input'
                    byteResult = bytes(str(result),encoding = 'utf-8')
                    conn.sendall(byteResult)


def accept_wrapper(sock,sel):
    conn,addr =sock.accept()
    conn.setblocking(False)
    print(f'Accepted connection from {addr}')
    data = types.SimpleNamespace(addr=addr,inb = b'',outb = b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn,events,data=data)

def service_connection(key,mask,sel,mfcMain):
    sock = key.fileobj
    data = key.data
    bytemessage = b''
    def closeConnection():
        print(f'closing connection to {data.addr}')
        sel.unregister(sock)
        sock.close()
    if mask & selectors.EVENT_READ:
        try:
            recvData = sock.recv(1024)
        except ConnectionAbortedError:
            recvData = b''
        if recvData:
            print(recvData)
            data.outb += recvData
            strmessage = data.outb.decode()
            try:
                address = int(strmessage.split(';')[0])
                mainmessage = MFC(address,mfcMain).strToMethod(strmessage)
                #endmessageMarker = '!'
                fullmessage = f'{mainmessage}!'
                bytemessage += bytes(fullmessage,encoding='utf-8')
            except (ValueError, KeyError):
                closeConnection()
        else:
            closeConnection()
    if mask & selectors.EVENT_WRITE:

        if bytemessage and strmessage != 'close':
            print(f'sending {bytemessage} to {data.addr}')
            sent = sock.send(bytemessage)
            bytemessage = bytemessage[sent:]




def multiServer():
    com,port, host = getParsers()
    
    mfcMain = startMfc(com)
    sel = selectors.DefaultSelector()
    print('running multiServer')
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen()
    s.setblocking(False)
    sel.register(s,selectors.EVENT_READ,data=None)

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj,sel)
                else:
                    service_connection(key, mask,sel,mfcMain)

    except KeyboardInterrupt:
        print("caught keyboard interrupt, exiting")
    finally:
        sel.close()


if __name__ == '__main__':
    run()