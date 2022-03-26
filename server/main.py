import socket
import threading

HOST = "127.0.0.1"
PORT = 65432
ENC_TYPE = 'utf-8'
MESSAGE_SIZE = 1024
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


class Command():
    HELP = 'help'
    LIST = 'ls'
    GET = 'get'
    PUT = 'put'
    PWD = 'pwd'
    MKDIR = 'mkdir'
    CD = 'cd'
    DELETE = 'delete'
    RENAME = 'rename'

    def __init__(self, cmd):
        self.type, self.args = Command.split_command(cmd)

    def split_command(cmd):
        first_space = cmd.find(' ')
        if first_space < 0:
            return cmd, ''
        return cmd[:first_space], cmd[first_space + 1:]


class ClientThread(threading.Thread):
    def __init__(self, conn, addr, *args):
        self.conn = conn
        self.addr = addr
        threading.Thread.__init__(self, args=args)

    def run(self):
        global ENC_TYPE, active_connections

        print_lock.acquire()
        print(COLORS['YELLOW'] +
              f'[NEW CONNECTION] {self.addr[0]} connected at port {self.addr[1]}' +
              COLORS['RESET'])
        print_lock.release()

        while True:
            message = self.conn.recv(MESSAGE_SIZE).decode(ENC_TYPE)
            if not message:
                break
            print_lock.acquire()
            print(COLORS['CYAN'] +
                  f'[{self.addr[0]}:{self.addr[1]}] "{message}"' +
                  COLORS['RESET'])
            print_lock.release()

            cmd = Command(message)
            if cmd.type == Command.HELP:
                self.help()
            elif cmd.type == Command.LIST:
                pass
            elif cmd.type == Command.GET:
                pass
            elif cmd.type == Command.PUT:
                pass
            elif cmd.type == Command.PWD:
                pass
            elif cmd.type == Command.MKDIR:
                pass
            elif cmd.type == Command.CD:
                pass
            elif cmd.type == Command.DELETE:
                pass
            elif cmd.type == Command.RENAME:
                pass

        self.close_connection()

    def close_connection(self):
        active_connections -= 1
        print_lock.acquire()
        print(COLORS['RED'] +
              f'[CONNECTION LOST] {self.addr[0]}:{self.addr[1]} disconnected' +
              COLORS['RESET'])
        print(COLORS['GREEN'] +
              f'[ACTIVE CONNECTIONS] {active_connections}' +
              COLORS['RESET'])
        print_lock.release()
        self.conn.close()

    def help(self):
        print("requested help")


def handle_incoming_requests(socket):
    global active_connections

    while True:
        conn, addr = socket.accept()
        ClientThread(conn, addr).start()

        active_connections += 1

        print_lock.acquire()
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
