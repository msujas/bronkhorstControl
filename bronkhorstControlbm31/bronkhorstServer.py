import socket
from bronkhorstControlbm31.bronkhorst import MFC, startMfc, configfile
import os
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

    args = parser.parse_args()
    f = open(configfile,'w')
    f.write(str(args.com))
    f.close()
    com = f'COM{args.com}'
    PORT = args.port
    print(f'MFCs on {com}')
    print(f'port: {PORT}')
    host = args.host
    
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
    return com, PORT, host, acceptedHosts

def run(port = PORT):
    com, port, host, acceptedHosts = getArgs()
    if not acceptedHosts:
        ahstring = 'all'
    else:
        ahstring = ','.join(acceptedHosts)
        acceptedIPs = [socket.gethostbyname(h) for h in acceptedHosts]
    print(f'accepted hosts: {ahstring}')
    print('running single client server')
    mfcMain = startMfc(com)
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
                        print(strdata)
                        result = MFC(address, mfcMain, com).strToMethod(strdata)
                        result += '!'
                        
                    except (ValueError, KeyError):
                        byteResult = b'invalid input!'
                    byteResult = bytes(str(result),encoding = 'utf-8')
                    print(f'sending data to {addr}')
                    conn.sendall(byteResult)

def accept_wrapper(sock,sel):
    conn,addr =sock.accept()
    conn.setblocking(False)
    print(f'Accepted connection from {addr}')
    data = types.SimpleNamespace(addr=addr,inb = b'',outb = b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn,events,data=data)

def service_connection(key,mask,sel,mfc, acceptedHosts = None):
    sock = key.fileobj
    data = key.data

    bytemessage = b''
    def closeConnection():
        print(f'closing connection to {data.addr}')
        sel.unregister(sock)
        sock.close()
    if acceptedHosts:
        acceptedIPs = [socket.gethostbyname(h) for h in acceptedHosts]
        hostName = data.addr[0]
        if hostName not in acceptedHosts and hostName not in acceptedIPs:
            print('host name not in accepted hosts')
            closeConnection()
            return
    if mask & selectors.EVENT_READ:
        try:
            recvData = sock.recv(1024)
        except (ConnectionAbortedError, ConnectionResetError):
            print(f'connection lost with client: {data.addr}')
            recvData = b''
        if recvData:
            print(recvData)
            data.outb += recvData
            strmessage = data.outb.decode()
            try:
                address = int(strmessage.split(';')[0])
                mfc.address = address
                mainmessage = mfc.strToMethod(strmessage)
                #endmessageMarker = '!'
                fullmessage = f'{mainmessage}!'
                bytemessage += bytes(fullmessage,encoding='utf-8')
            except (ValueError, KeyError):
                bytemessage = b'invalid message!'
            except ConnectionResetError:
                print(f'connection lost with client: {data.addr}')
                bytemessage = b''
                closeConnection()
        else:
            closeConnection()
    if mask & selectors.EVENT_WRITE:

        if bytemessage:
            print(f'sending data to {data.addr}')
            try:
                sent = sock.send(bytemessage)
                bytemessage = bytemessage[sent:]
            except ConnectionResetError:
                print(f'connection lost with client: {data.addr}')
                bytemessage = b''
                closeConnection()

def multiServer():
    com,port, host, acceptedHosts = getArgs()
    
    if not acceptedHosts:
        ahstring = 'all'
    else:
        ahstring = ','.join(acceptedHosts)
    print(f'accepted hosts: {ahstring}')
    mfcMain = startMfc(com)
    mfc = MFC(0,mfcMain)
    sel = selectors.DefaultSelector()
    print('running multiServer')
    s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen()
    s.setblocking(False)
    sel.register(s,selectors.EVENT_READ,data=None)

    try:
        while True:
            events = sel.select(timeout=10)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj,sel)
                else:
                    service_connection(key, mask,sel,mfc, acceptedHosts)
    except KeyboardInterrupt:
        print("caught keyboard interrupt, exiting")
    finally:
        sel.close()

if __name__ == '__main__':
    run()