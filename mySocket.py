import socket
import subprocess
def getIP():
    p = subprocess.run('ipconfig',text=True,capture_output=True)
    ipaddressline = [line for line in p.stdout.split('\n') if 'IPv4 Address' in line][0]
    ipaddress = ipaddressline.split(' ')[-1]
    return ipaddress

localhost = True
if localhost:
    HOST = "localhost"  # Standard loopback interface address (localhost)
else:
    HOST = getIP()
PORT = 65432  # Port to listen on (non-privileged ports are > 1023)

def add2(a :int,b:int):
    return a + b

close = False
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
                print(strdata)
                conn.sendall(data)
                if strdata == 'close':
                    close = True
                    break
        if close:
            break