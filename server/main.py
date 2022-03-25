from ast import arg
import socket
import threading

HOST = "127.0.0.1"
PORT = 65432
COLORS = {
    "BLACK": "\u001b[30;1m",
    "RED": "\u001b[31;1m",
    "GREEN": "\u001b[32;1m",
    "YELLOW": "\u001b[33;1m",
    "BLUE": "\u001b[34;1m",
    "MAGENTA": "\u001b[35;1m",
    "CYAN": "\u001b[36;1m",
    "WHITE": "\u001b[37;1m",
    "RESET": "\u001b[0m",
}

active_connections = 0
print_lock = threading.Lock()


class ClientThread(threading.Thread):
    def __init__(self, conn, addr, *args):
        self.conn = conn
        self.addr = addr
        threading.Thread.__init__(self, args=args)

    def run(self):
        print_lock.acquire()
        print("Starting " + str(self.addr))
        print_lock.release()


def handle_incoming_requests(socket):
    global active_connections

    while True:
        conn, addr = socket.accept()
        ClientThread(conn, addr).start()

        active_connections += 1

        print_lock.acquire()
        print(COLORS['YELLOW'] +
              f'[NEW CONNECTION] {addr[0]} connected at port {addr[1]}' +
              COLORS['RESET'])
        print(COLORS['GREEN'] +
              f'[ACTIVE CONNECTIONS] {active_connections}' +
              COLORS['RESET'])
        print_lock.release()


def main():
    print(COLORS['RED'] +
          f'[STARTING SERVER] Starting server...' +
          COLORS['RESET'])
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(COLORS['GREEN'] +
          f'[SERVER STARTED] Server is listening on {HOST}:{PORT}' +
          COLORS['RESET'])

    handle_incoming_requests(server_socket)


if __name__ == '__main__':
    main()
