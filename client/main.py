import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 65432))
while True:
    inp = input()
    s.sendall(inp.encode('utf-8'))
    data = s.recv(1024)
    print(data.decode('utf-8'))