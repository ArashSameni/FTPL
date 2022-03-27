import socket
import shlex

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
    RENAME   Rename file/directory
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


def handle_get_command(client_socket, cmd):
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

    client_socket.sendall(f'get {remote_file_name}'.encode(ENC_TYPE))
    port = 0
    result = client_socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
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
    result = client_socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
    print_result(result)


def handle_commands(client_socket):
    while True:
        print(COLORS['WHITE'] + '[COMMAND]    ', end='')
        inp = input().strip()
        if inp.lower() == 'help':
            print(COLORS['CYAN'] + HELP_MESSAGE + COLORS['RESET'])
            continue
        if inp.lower() == 'exit':
            client_socket.close()
            exit(0)

        try:
            cmd = Command(inp)
            if cmd.type == 'get':
                handle_get_command(client_socket, cmd)
            else:
                client_socket.sendall(cmd.text().encode(ENC_TYPE))
                data = client_socket.recv(MESSAGE_SIZE).decode(ENC_TYPE)
                print_result(data)

        except:
            print_colorful('[ERROR]', 'Bad command', 'RED')


def main():
    print_colorful('[CONNECTING]', 'Connecting to server...', 'YELLOW')
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    print_colorful(
        '[CONNECTED]', f'Successfully connected to {HOST}:{PORT}', 'GREEN')

    print(COLORS['CYAN'] + HELP_MESSAGE + COLORS['RESET'])

    handle_commands(client_socket)


if __name__ == '__main__':
    main()
