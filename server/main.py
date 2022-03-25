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


def handle_client_connection(conn, addr):
    rec = conn.recv(1024)
    print('received: ' + str(rec))
    while conn:
        conn.sendall(b"test")


def handle_incoming_requests(socket):
    while True:
        conn, addr = socket.accept()
        threading.Thread(target=handle_client_connection,
                         args=(conn, addr)).start()
        print(f'[NEW CONNECTION] {addr[0]} connected at port {addr[1]}')
        print(f'[ACTIVE CONNECTIONS] {threading.activeCount() - 1}')


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
