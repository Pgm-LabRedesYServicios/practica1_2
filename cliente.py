import socket
import sys

messages = [
    'This is the message. ',
    'It will be sent ',
    'in parts.',
]
server_address = ('localhost', 10000)

# Parse arguments
if len(sys.argv) != 3:
    print("Usage\n\t{sys.argv[0]} <address> <port>")

try:
    server_address[0] = sys.argv[1]
    server_address[1] = int(sys.argv[2])
except ValueError as e:
    print(f"Error while trying to parse arguments {e}")
    sys.exit(1)


# Create a TCP/IP socket
socks = [
    socket.socket(socket.AF_INET, socket.SOCK_STREAM),
    socket.socket(socket.AF_INET, socket.SOCK_STREAM),
]

# Connect the socket to the port where the server is listening
print('connecting to {} port {}'.format(*server_address), file=sys.stderr)
for s in socks:
    s.connect(server_address)

# Se envia una parte del mensaje a la vez a traves de cada conector y lee todas
# las respuestas disposibles despues de escribir nuevos datos
for message in messages:
    outgoing_data = message.encode()

    # Send messages on both sockets
    for s in socks:
        print(f"{s.getsockname()}: sending {outgoing_data}", file=sys.stderr)
        s.send(outgoing_data)

    # Read responses on both sockets
    for s in socks:
        data = s.recv(1024)
        print(f"{s.getsockname()}: received {data}", file=sys.stderr)
        if not data:
            print('closing socket', s.getsockname(), file=sys.stderr)
            s.close()