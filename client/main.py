import socket
from time import sleep

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 65432))
s.sendall(b"Hello, world")
while True:
    data = s.recv(1024)
    print(f"Received {data!r}")
    sleep(2)