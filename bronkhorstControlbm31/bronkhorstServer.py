import socket
from bronkhorstControlbm31.bronkhorst import MFC, startMfc
import subprocess
import os, pathlib
import argparse
import selectors, types

HOST = 'localhost'
PORT = 61245
com = 'COM1'

def getIP():
    p = subprocess.run('ipconfig',text=True,capture_output=True)
    ipaddressline = [line for line in p.stdout.split('\n') if 'IPv4 Address' in line][0]
    ipaddress = ipaddressline.split(' ')[-1]
    return ipaddress


homedir = pathlib.Path.home()
configfile = f'{homedir}/bronkhorstServerConfig/comConfg.log'
if not os.path.exists(os.path.dirname(configfile)):
    os.makedirs(os.path.dirname(configfile))

def getParsers(port=PORT):
    parser = argparse.ArgumentParser()
    parser.add_argument('local_remote',nargs='?', default='local')

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
    host = args.local_remote
    if host == 'local':
        host = 'localhost'
    elif host == 'remote':
        host = getIP()
    else:
        print('usage bronkorstServer [host]')
        print('host must must be "local", "remote" or nothing (local)')
        return
    print(host)
    return com, port, host

def run(port = PORT):

    mfcMain = startMfc(com)
    #nodes = mfcMain.master.get_nodes()
    #addresses = [n['address'] for n in nodes]
    com, port, host = getParsers()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        s.bind((host, port))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    strdata = data.decode()
                    if strdata == 'close':
                        print(strdata)
                        return
                    address = int(strdata.split(';')[0])
                    print(strdata)
                    result = MFC(address, mfcMain).strToMethod(strdata)
                    print(result)
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
    if mask & selectors.EVENT_READ:
        recvData = sock.recv(1024)
        print(recvData)
        if recvData:
            data.outb += recvData
            strmessage = data.outb.decode()
            address = int(strmessage.split(';')[0])
            mainmessage = MFC(address,mfcMain).strToMethod(strmessage)
            #endmessageMarker = '!'
            fullmessage = f'{mainmessage}!'
            bytemessage = bytes(fullmessage,encoding='utf-8')
        else:
            print(f'closing connection to {data.addr}')
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:

        if bytemessage:
            print(f'echoing {bytemessage} to {data.addr}')
            sent = sock.send(bytemessage)
            bytemessage = bytemessage[sent:]


def multiServer(HOST = 'localhost', PORT=PORT):
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