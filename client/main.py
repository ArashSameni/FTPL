import socket
import shlex
import os

HOST = "127.0.0.1"
PORT = 2121
MESSAGE_SIZE = 1024
ENC_TYPE = 'utf-8'
COLORS = {
    "BLACK": "\u001b[30;1m",
    "RED": "\u001b[31;1m",
    "GREEN": "\u001b[32;1m",
    "YELLOW": "\u001b[33;1m",
    "BLUE": "\u001b[34;1m",
    "MAGENTA": "\u001b[35;1m",
    "CYAN": "\u001b[36;1m",
    "WHITE": "\u001b[37m",
    "RESET": "\u001b[0m",
}
HELP_MESSAGE = '''[HELP]
    HELP     List of the known commands
    LIST     List contents of remote directory
    PWD      Print working directory of remote machine
    CD       Change remote working directory
    GET      Receive a file. Example: get remote-file [local-file]
    PUT      Send a file.    Example: put local-file  [remote-file]
    MKDIR    Make directory on the remote machine
    RMDIR    Remove directory on the remote machine
    DELETE   Delete remote file
    RENAME   Rename file.    Example: rename from-name to-name
    CLEAR    Clears the terminal
    EXIT     Terminate ftp session and exit
'''


class Command():
    COMMANDS = ['ls', 'get', 'put', 'pwd',
                'mkdir', 'rmdir', 'cd', 'delete', 'rename']

    def __init__(self, cmd):
        self.type, self.args = Command.split_command(cmd)
        self.type = self.type.lower().replace('list', 'ls')

        if self.type not in Command.COMMANDS:
            raise ValueError()

    def split_command(cmd):
        first_space = cmd.find(' ')
        if first_space < 0:
            return cmd, ''
        return cmd[:first_space], cmd[first_space + 1:]

    def text(self):
        result = self.type
        if self.args:
            result += ' ' + self.args
        return result


def print_colorful(short_desc, text, color):
    SPACE_NEEDED = 13
    spaces = ' ' * (SPACE_NEEDED - len(short_desc))
    print(COLORS[color] + short_desc + spaces + text + COLORS['RESET'])


def print_result(result):
    first_space = result.index(' ')
    status_code = int(result[:first_space])
    message = result[first_space:]

    print('    ', end='')
    if 200 <= status_code < 300:
        print(COLORS['GREEN'], end='')
    elif 100 <= status_code < 200 or 300 <= status_code < 400:
        print(COLORS['YELLOW'], end='')
    else:
        print(COLORS['RED'], end='')

    print(str(status_code) + message + COLORS['RESET'])


class ClientHandler():
    def __init__(self, socket):
        self.socket = socket

    def run(self):
        while True:
            print(COLORS['WHITE'] + '[COMMAND]    ', end='')
            inp = input().strip()
            if inp.lower() == 'help':
                print(COLORS['CYAN'] + HELP_MESSAGE + COLORS['RESET'])
                continue
            if inp.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                continue
            if inp.lower() == 'exit':
                self.socket.close()
                break

            cmd = None
            try:
                cmd = Command(inp)
            except:
                print_colorful('[ERROR]', 'Bad command', 'RED')
                continue
            
            if cmd.type == 'rename' and len(shlex.split(cmd.args)) != 2:
                print_colorful('[ERROR]', "Invalid use of rename command", 'RED')
                continue

            if cmd.type == 'ls':
                self.list()
            elif cmd.type == 'get':
                self.get(cmd)
            elif cmd.type == 'put':
                self.put(cmd)
            else:
                self.send(cmd.text())
                data = self.socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
                print_result(data)

    def list(self):
        self.send('ls')
        port = 0
        result = self.socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
        if result.startswith('200'):
            port = int(result.split(' ')[-1])
        else:
            print_result(result)
            return

        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            data_socket.connect((HOST, port))
        except:
            print_colorful('[ERROR]', "Couldn't connect to server", 'RED')
            return

        print(COLORS['CYAN'], end='')
        data = data_socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
        while data:
            print(data)
            data = data_socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
        print(COLORS['RESET'], end='')

        result = self.socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
        print_result(result)

    def get(self, cmd):
        remote_file_name, local_file_name = '', ''

        args = shlex.split(cmd.args)
        if len(args) == 0 or len(args) > 2:
            print_colorful('[ERROR]', "Invalid use of get command", 'RED')
            return

        remote_file_name = args[0]
        if len(args) == 1:
            local_file_name = remote_file_name.split('/')[-1]
        else:
            local_file_name = args[1]

        self.send(f'get {remote_file_name}')
        port = 0
        result = self.socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
        if result.startswith('200'):
            port = int(result.split(' ')[-1])
        else:
            print_result(result)
            return
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            data_socket.connect((HOST, port))
        except:
            print_colorful('[ERROR]', "Couldn't connect to server", 'RED')
            return

        file = open(local_file_name, 'w')
        data = data_socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
        while data:
            file.write(data)
            data = data_socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
        file.close()
        result = self.socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
        print_result(result)

    def put(self, cmd):
        local_file_name, remote_file_name = '', ''

        args = shlex.split(cmd.args)
        if len(args) == 0 or len(args) > 2:
            print_colorful('[ERROR]', "Invalid use of put command", 'RED')
            return

        local_file_name = args[0]
        if len(args) == 1:
            remote_file_name = local_file_name.split('/')[-1]
        else:
            remote_file_name = args[1]

        if not os.path.isfile(local_file_name):
            print_colorful('[ERROR]', "No such file or directory", 'RED')
            return
        
        self.send(f'put {remote_file_name}')

        port = 0
        result = self.socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
        if result.startswith('200'):
            port = int(result.split(' ')[-1])
        else:
            print_result(result)
            return
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            data_socket.connect((HOST, port))
        except:
            print_colorful('[ERROR]', "Couldn't connect to server", 'RED')
            return

        file = None
        data = ''
        try:
            file = open(local_file_name, 'r')
            data = file.read()
        except:
            print_colorful('[ERROR]', "Permission denied", 'RED')
            return

        data_socket.send(data.encode(ENC_TYPE))
        file.close()
        data_socket.shutdown(socket.SHUT_WR)
        
        result = self.socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
        print_result(result)

    def send(self, message):
        self.socket.sendall(message.encode(ENC_TYPE))

def main():
    print_colorful('[CONNECTING]', 'Connecting to server...', 'YELLOW')
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    print_colorful(
        '[CONNECTED]', f'Successfully connected to {HOST}:{PORT}', 'GREEN')

    print(COLORS['CYAN'] + HELP_MESSAGE + COLORS['RESET'])

    ClientHandler(client_socket).run()


if __name__ == '__main__':
    main()
