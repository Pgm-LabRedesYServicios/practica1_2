from select import select
from socket import create_connection, socket
from sys import argv, exit, stdin


def main():
    # Parse arguments
    if len(argv) != 3:
        print(f"Usage\n\t{argv[0]} <address> <port>")
        exit(1)

    try:
        # Parse arguments into server address
        server_address = (argv[1], int(argv[2]))
        # Try to connect to the server
        conn = create_connection(server_address)
    except ValueError as e:
        print(f"Error while trying to parse arguments {e}")
        exit(1)
    except OSError as e:
        print(f"Failed to connect to server {e}")
        exit(1)

    fd_map = {
        conn.fileno(): conn,
        stdin.fileno(): stdin
    }

    while True:
        l, m, n = select(fd_map, [], [])

        for fd in l:
            if fd == stdin.fileno():
                handle_stdin(conn)
            elif fd == conn.fileno():
                handle_server(conn)


def handle_stdin(server_conn: socket):
    msg = input()
    server_conn.send(msg.encode())


def handle_server(server_conn: socket):
    msg = server_conn.recv(4096)
    if len(msg) == 0:
        print("The server disconnected")
        server_conn.close()
        exit(1)

    print(msg.decode())


if __name__ == "__main__":
    main()
