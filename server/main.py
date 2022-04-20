from random import randint
import socket
import threading
import os
import pathlib
from time import sleep
import shlex
import sys
sys.tracebacklimit = 0

HOST = "127.0.0.1"
PORT = 2121
MESSAGE_SIZE = 1024
FILES_DIR = str(pathlib.Path(__file__).parent.resolve()) + '/files'
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


def print_colorful(short_desc, text, color):
    SPACE_NEEDED = 21
    spaces = ' ' * (SPACE_NEEDED - len(short_desc))

    print_lock.acquire()
    print(COLORS[color] + short_desc + spaces + text + COLORS['RESET'])
    print_lock.release()


def human_readable_size(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


class Command():
    LIST = 'ls'
    GET = 'get'
    PUT = 'put'
    PWD = 'pwd'
    MKDIR = 'mkdir'
    RMDIR = 'rmdir'
    CD = 'cd'
    DELETE = 'delete'
    RENAME = 'rename'
    PASV = 'pasv'

    def __init__(self, cmd):
        self.type, self.args = Command.split_command(cmd)
        self.data_connection = None

    def split_command(cmd):
        first_space = cmd.find(' ')
        if first_space < 0:
            return cmd, ''
        return cmd[:first_space], cmd[first_space + 1:]


class ClientThread(threading.Thread):
    ENC_TYPE = 'utf-8'

    def __init__(self, conn, addr, *args):
        self.conn = conn
        self.addr = addr
        self.current_directory = ''
        threading.Thread.__init__(self, args=args)

    def run(self):
        print_colorful(
            '[NEW CONNECTION]', f'{self.addr[0]} connected at port {self.addr[1]}', 'YELLOW')

        while True:
            message = self.conn.recv(MESSAGE_SIZE).decode(
                ClientThread.ENC_TYPE)
            if not message:
                break
            print_colorful(f'[{self.addr[0]}:{self.addr[1]}]',
                           f'"{message}"', 'CYAN')

            cmd = Command(message)
            if cmd.type == Command.LIST:
                self.list()
            elif cmd.type == Command.GET:
                self.get(cmd.args)
            elif cmd.type == Command.PUT:
                self.put(cmd.args)
            elif cmd.type == Command.PWD:
                self.pwd()
            elif cmd.type == Command.MKDIR:
                self.mkdir(cmd.args)
            elif cmd.type == Command.RMDIR:
                self.rmdir(cmd.args)
            elif cmd.type == Command.CD:
                self.cd(cmd.args)
            elif cmd.type == Command.DELETE:
                self.delete(cmd.args)
            elif cmd.type == Command.RENAME:
                self.rename(cmd.args)
            elif cmd.type == Command.PASV:
                self.pasv()

        self.close_connection()

    def close_connection(self):
        global active_connections
        active_connections -= 1

        print_colorful('[CONNECTION LOST]',
                       f'{self.addr[0]}:{self.addr[1]} disconnected', 'RED')
        print_colorful('[ACTIVE CONNECTIONS]',
                       str(active_connections), 'GREEN')

        self.conn.close()

    def list(self):
        try:
            current_dir = self.absolute_path()

            self.data_connection.send('[LIST]'.encode(ClientThread.ENC_TYPE))
            sleep(0.001)
            self.data_connection.send('  > .'.encode(ClientThread.ENC_TYPE))
            sleep(0.001)
            if self.current_directory:
                self.data_connection.send(
                    '  > ..'.encode(ClientThread.ENC_TYPE))

            ls = os.listdir(current_dir)
            for fname in ls:
                path_to_file = current_dir + '/' + fname
                if os.path.isdir(path_to_file):
                    self.data_connection.send(
                        f'  > {fname}'.encode(ClientThread.ENC_TYPE))
                elif os.path.isfile(path_to_file):
                    self.data_connection.send(('    %-20s' % fname + human_readable_size(
                        os.path.getsize(path_to_file))).encode(ClientThread.ENC_TYPE))
                sleep(0.001)

            self.data_connection.shutdown(socket.SHUT_WR)
            self.send('226 Directory send OK.')
            print_colorful(
                '[DATA CHANNEL]', f'{self.addr[0]}:{self.addr[1]} directory sent', 'GREEN')
        except:
            self.send('550 Permission denied.')

    def get(self, file_name):
        try:
            to_upload = self.absolute_path(file_name)
            if not pathlib.Path(to_upload).is_file():
                self.send("550 File doesn't exist.")
                return
            self.send('150 Here comes the file')
            file = open(to_upload, 'r')
            self.data_connection.send(
                file.read().encode(ClientThread.ENC_TYPE))
            file.close()
            self.data_connection.shutdown(socket.SHUT_WR)

            self.send('226 Transfer complete.')
            print_colorful(
                '[DATA CHANNEL]', f'{self.addr[0]}:{self.addr[1]} transfer completed', 'GREEN')
        except:
            self.data_connection.shutdown(socket.SHUT_WR)
            self.send('550 Failed to open file.')

    def put(self, file_name):
        try:
            to_download = self.absolute_path(file_name)
            file = open(to_download, 'w')
            data = self.data_connection.recv(
                MESSAGE_SIZE).decode(ClientThread.ENC_TYPE)
            while data:
                file.write(data)
                data = self.data_connection.recv(
                    MESSAGE_SIZE).decode(ClientThread.ENC_TYPE)
            file.close()

            self.send('226 Transfer complete.')
            print_colorful(
                '[DATA CHANNEL]', f'{self.addr[0]}:{self.addr[1]} transfer completed', 'GREEN')
        except:
            self.send('550 Failed to open file.')

    def pwd(self):
        self.send(
            f'257 "/{self.current_directory}" is the current directory')

    def mkdir(self, dir_name):
        try:
            os.mkdir(self.absolute_path(dir_name))
            self.send(
                f'257 /{os.path.join(self.current_directory, dir_name)} created')
        except:
            self.send('550 Failed to make directory.')

    def rmdir(self, dir_name):
        try:
            to_remove = self.absolute_path(dir_name)
            if not pathlib.Path(to_remove).is_dir():
                self.send("550 Directory doesn't exist.")
                return
            os.rmdir(to_remove)
            self.send(
                f'250 Remove directory operation successful.')
        except:
            self.send('550 Remove directory operation failed.')

    def cd(self, dir_path):
        try:
            new_path = self.absolute_path(dir_path)
            if not pathlib.Path(new_path).is_dir():
                self.send("550 Directory doesn't exist.")
                return

            self.current_directory = os.path.normpath(
                os.path.join(self.current_directory, dir_path))
            if self.current_directory == '.':
                self.current_directory = ''

            self.send('250 Directory successfully changed.')
        except:
            self.send('550 Failed to change directory.')

    def delete(self, file_name):
        try:
            to_remove = self.absolute_path(file_name)
            if not pathlib.Path(to_remove).is_file():
                self.send("550 File doesn't exist.")
                return
            os.remove(to_remove)
            self.send(
                f'250 Delete operation successful.')
        except:
            self.send('550 Delete operation failed.')

    def rename(self, args):
        from_name, to_name = shlex.split(args)
        try:
            from_path = self.absolute_path(from_name)
            if not pathlib.Path(from_path).is_file():
                self.send("550 File doesn't exist.")
                return

            os.rename(from_path,
                      self.absolute_path(to_name))
            self.send('250 Rename successful.')
        except:
            self.send('550 RNFR command failed.')

    def pasv(self):
        data_socket = self.create_data_channel()
        port = data_socket.getsockname()[1]
        print_colorful(
            '[DATA CHANNEL]', f'Data channel created at {HOST}:{port}', 'YELLOW')
        self.send(f'200 PORT {port}')
        conn, _ = data_socket.accept()
        data_socket.shutdown(socket.SHUT_WR)
        print_colorful(
            '[DATA CHANNEL]', f'{self.addr[0]}:{self.addr[1]} connected to data channel', 'GREEN')
        self.data_connection = conn

    def create_data_channel(self):
        random_port = randint(3000, 50000)
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                data_socket.bind((HOST, random_port))
                break
            except:
                random_port = randint(3000, 50000)
        data_socket.listen()
        return data_socket

    def absolute_path(self, joining_path=''):
        joined_path = os.path.normpath(os.path.join(
            FILES_DIR, self.current_directory, joining_path))
        if not joined_path.startswith(FILES_DIR):
            raise Exception()

        return joined_path

    def send(self, message):
        self.conn.sendall(message.encode(ClientThread.ENC_TYPE))


def handle_incoming_requests(socket):
    global active_connections

    while True:
        conn, addr = socket.accept()
        ClientThread(conn, addr).start()

        active_connections += 1
        print_colorful('[ACTIVE CONNECTIONS]',
                       str(active_connections), 'GREEN')


def main():
    print_colorful('[STARTING SERVER]', 'Starting server...', 'YELLOW')
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print_colorful('[SERVER STARTED]',
                   f'Server is listening on {HOST}:{PORT}', 'GREEN')

    handle_incoming_requests(server_socket)


if __name__ == '__main__':
    main()
