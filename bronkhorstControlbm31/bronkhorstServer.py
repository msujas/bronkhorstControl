import socket
from bronkhorstControlbm31.bronkhorst import MFC, startMfc
import subprocess
import os, pathlib
import argparse

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




def run(port = PORT):
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
    f.write(args.com)
    f.close()
    com = f'COM{args.com}'
    PORT = int(args.port)
    print(f'port: {PORT}')
    host = args.local_remote
    mfcMain = startMfc(com)
    #nodes = mfcMain.master.get_nodes()
    #addresses = [n['address'] for n in nodes]

    if host == 'local':
        HOST = 'localhost'
    elif host == 'remote':
        HOST = getIP()
    else:
        print('usage bronkorstServer [host]')
        print('host must must be "local", "remote" or nothing (local)')
        return
    print(HOST)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        s.bind((HOST, PORT))
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

if __name__ == '__main__':
    run()