import socket

HOST = "172.29.159.70"
PORT = 65432
close = False
while True:
    message = input('send message:')
    s= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall(bytes(message,encoding='utf-8'))
    data = s.recv(1024)
    print(data)
    s.close()
    if message == 'close':
        break