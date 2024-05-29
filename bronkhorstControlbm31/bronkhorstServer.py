import socket
from bronkhorstControlbm31.bronkhorst import MFC, startMfc
import os, pathlib
import argparse
import selectors, types

HOST = 'localhost'
PORT = 61245
com = 'COM1'

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
        host = socket.gethostname()
    else:
        print('usage bronkorstServer [host]')
        print('host must must be "local", "remote" or nothing (local)')
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
    bytemessage = b''
    if mask & selectors.EVENT_READ:
        try:
            recvData = sock.recv(1024)
        except ConnectionAbortedError:
            recvData = b''
        if recvData:
            print(recvData)
            data.outb += recvData
            strmessage = data.outb.decode()
            if strmessage == 'close':

                bytemessage += b'close!'

                print(f'closing connection to {data.addr}')
                sel.unregister(sock)
                sock.close()
            else:
                address = int(strmessage.split(';')[0])
                mainmessage = MFC(address,mfcMain).strToMethod(strmessage)
                #endmessageMarker = '!'
                fullmessage = f'{mainmessage}!'
                bytemessage += bytes(fullmessage,encoding='utf-8')
        else:
            print(f'closing connection to {data.addr}')
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:

        if bytemessage and strmessage != 'close':
            print(f'sending {bytemessage} to {data.addr}')
            sent = sock.send(bytemessage)
            bytemessage = bytemessage[sent:]

    return bytemessage


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
                    bytemessage = service_connection(key, mask,sel,mfcMain)
                    if bytemessage.decode() == 'close!':
                        sel.close()
                        return
    except KeyboardInterrupt:
        print("caught keyboard interrupt, exiting")
    finally:
        sel.close()


if __name__ == '__main__':
    run()