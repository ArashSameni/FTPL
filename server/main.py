import socket
import threading
from time import sleep

HOST = "127.0.0.1"
PORT = 65432

def sayHello(conn):
    rec = conn.recv(1024)
    print('received: ' + str(rec))
    while conn:
        conn.sendall(b"test")
        sleep(2)

def handle_incoming_requests(socket):
    while True:
        conn, addr = socket.accept()
        threading.Thread(target=sayHello, args=(conn,)).start()

if __name__ == 'main':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen()
    handle_incoming_requests(s)