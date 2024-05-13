import socket
from bronkhorst import MFC

HOST = 'localhost'
PORT = 61245
def run(HOST=HOST, PORT=PORT):
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
                    address = int(strdata.split()[0])
                    print(strdata)
                    result = MFC(address).strToMethod(strdata)
                    conn.sendall(result)
                    if strdata == 'close':
                        close = True
                        break
            if close:
                break
if __name__ == '__main__':
    run()