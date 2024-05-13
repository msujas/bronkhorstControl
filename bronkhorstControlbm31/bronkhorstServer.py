import socket
from bronkhorstControlbm31.bronkhorst import MFC, startMfc
import subprocess
import sys
HOST = 'localhost'
PORT = 61245
com = 'COM1'

def getIP():
    p = subprocess.run('ipconfig',text=True,capture_output=True)
    ipaddressline = [line for line in p.stdout.split('\n') if 'IPv4 Address' in line][0]
    ipaddress = ipaddressline.split(' ')[-1]
    return ipaddress



def run(PORT=PORT, com = com):
    mfcMain = startMfc(com)
    args = sys.argv
    if len(args) == 1:
        host = 'local'
    else:
        host = args[1]

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
                    address = int(strdata.split()[0])
                    print(strdata)
                    result = MFC(address, mfcMain).strToMethod(strdata)
                    byteResult = bytes(str(result),encoding = 'utf-8')
                    conn.sendall(byteResult)

if __name__ == '__main__':
    run()