#!/usr/bin/env python
"""ff"""

import io
import ipaddress
import sys
from select import select
from socket import AF_INET, SOCK_STREAM, create_connection, socket
from sys import stdin

import capnp
import msgs_capnp

EXIT_OK = 0
EXIT_ERR = 1

incoming_port: int = 0
counter: int = 0


class PeerId():
    """
    A socket ID object that is hashable
    """
    inner: bytearray

    def __init__(self, host: bytes, port: bytes):
        self.inner = bytearray()
        self.inner += host
        self.inner += port

    def __hash__(self):
        num = int.from_bytes(self.inner, byteorder='big', signed=False)
        return num

    def __repr__(self):
        return f"{self.__hash__()}"


class Peer:
    """
    A peer object with its corresponding socket connection
    """
    in_sock: socket
    out_sock: socket
    peer_id: PeerId

    def __init__(
            self,
            peer_id: PeerId,
            in_sock: socket = None,
            out_sock: socket = None
    ):
        """
        Create a peer given the peer_id
        """
        self.peer_id = peer_id

        if in_sock is not None:
            self.in_sock = in_sock
        if out_sock is not None:
            self.out_sock = out_sock

    def __hash__(self):
        return self.peer_id.__hash__()

    def __repr__(self):
        return f"Peer(id: {self.peer_id.__hash__()})"

    def send_msg(self):
        pass


class Server:
    """
    A server object connection
    """
    sock: socket
    buff: bytearray

    def __init__(self, addr: str, port: str):
        self.buff = bytearray(0)
        try:
            self.sock = create_connection((addr, int(port)))
        except ValueError as e:
            print(f"[x] Error while trying to parse arguments: {e}")
            sys.exit(EXIT_ERR)
        except OSError as e:
            print(f"[x] Error while trying to connect to server: {e.strerror}")
            sys.exit(EXIT_ERR)

    def send_port(self):
        """
        Once connected to the server, advertise which port this peer is
        listening on
        """
        global incoming_port

        port_msg = msgs_capnp.PeerListeningPort.new_message()
        port_msg.port = incoming_port
        self.sock.send(port_msg.to_bytes())

    def get_peers(self) -> dict[int, Peer]:
        """
        Once connected to the server, get the connected peers and connect to
        them
        """
        # The first message received is a 4 bytes tag containing the size of
        # the message
        msg = self.sock.recv(4)
        if len(msg) == 0:
            print("[x] Connection unexpectedly died")
            exit(EXIT_ERR)

        # Count and size are declared here for clarity
        #
        # The size is the size received
        # The count is the bytes received afterwards, used to check if the
        # received message is complete
        count = 0
        size = 0

        try:
            size = int.from_bytes(msg, byteorder='big', signed=False)
        except ValueError as e:
            print(f"[x] Error while reading size, corrupted message {e}")

        while count != size:
            msg = self.sock.recv(4096)
            count += len(msg)
            if len(msg) == 0:
                break
            else:
                self.buff += msg

        # If we received less bytes than the server said it was going to send,
        # we assume that the connection was aborted and terminate
        if count != size:
            print("[x] Connection unexpectedly died")
            exit(EXIT_ERR)

        sockets: dict[int, Peer] = {}

        # Deserialize the message and connect to the peers sent by the server
        addrs = msgs_capnp.ServerRpcMsg.from_bytes(self.buff)

        # Craft port message to advertise to peers
        port_msg = msgs_capnp.PeerListeningPort.new_message()
        port_msg.port = incoming_port
        wire_msg = port_msg.to_bytes()
        for addr in addrs.addrs:
            host = ipaddress.IPv4Address(addr.ip).exploded
            port = addr.port

            peer_id_host = addr.ip.to_bytes(4, byteorder='big', signed=False)
            peer_id_port = addr.port.to_bytes(2, byteorder='big', signed=False)
            peer_id = PeerId(peer_id_host, peer_id_port)

            print(f"[i] Connecting to {host}:{port}")
            try:
                conn = create_connection((host, port))
                conn.send(wire_msg)
                sockets[conn.fileno()] = Peer(peer_id, out_sock=conn)
            except OSError as e:
                print(
                    f"[-] Error: Cannot connect to {host}:{port}, {e.strerror}"
                )

        return sockets


def handle_conn(
        sock: socket,
        select_map: dict[int, socket]
):
    """
    Handles a new connection, registering its socket and creating its
    corresponding outbound connection if it doesn't exist
    """
    global incoming_port
    global counter

    msg = sock.recv(4096)

    if msg == "":
        print("[x] Error while reading from new connection")

    select_map[sock.fileno()] = sock


def handle_msg(
        sock: socket,
        select_map: dict[int, socket]
):
    """
    Handles peer messages, either unregistering peers or printing its content
    """
    msg = sock.recv(4096)

    if len(msg) == 0:
        host, port = sock.getpeername()
        del select_map[sock.fileno()]
        print(f"[i] - {host}:{port} Disconnected")
    else:
        print(msg.decode())


def handle_stdin(
        s: io.TextIOWrapper,
        select_map: dict[int, socket],
        listening: int
):
    """
    Handles stdin input and dispatches it to its corresponding function
    depending on the command
    """
    msg = s.readline()
    trimmed = msg.strip()
    command, args = input_parse(trimmed)
    if command == "text":
        for p in select_map:
            if p != 0 and p != listening:
                sock = select_map[p]
                sock.send(args.encode())


def input_parse(text: str) -> tuple[str, str]:
    """
    Parses an input string into a command and a list of the arguments that it
    takes
    """
    ret: tuple[str, str] = ("", "")

    if text[0] == '/':
        # If the string starts with a / it is a command
        com, _, rest = text.partition(' ')
        ret = (com, rest)
    elif text[0] == '\\' and text[1] == '/':
        # If the string starts with a \ and it is followed by / it is a message
        # with an escaped /
        text.removeprefix('\\')
        ret = ('text', text)
    else:
        # Else it is just a message
        ret = ('text', text)

    return ret


def main():
    global incoming_port

    if len(sys.argv) != 3:
        print(f"Usage:\n\t{sys.argv[0]} <host> <port>")
        exit(1)

    # Bind to random socket and listen to incoming messages
    sock = socket(AF_INET, SOCK_STREAM)
    sock.bind(("", 0))
    sock.listen(8)
    sock.setblocking(False)
    incoming_port = sock.getsockname()[1]

    # Connect to server
    server = Server(sys.argv[1], sys.argv[2])
    # Advertise port
    server.send_port()
    # Get peers
    out_peers = server.get_peers()

    # A hashmap from socketid to socket
    select_map = {}
    select_map[sock.fileno()] = sock
    select_map |= map(lambda k: (k[0], k[1].out_sock), out_peers.items())

    # Register stdin
    select_map[stdin.fileno()] = stdin

    while True:
        selected, x, y = select(select_map, [], [])
        for s in selected:
            if s == sock.fileno():
                conn, (host, port) = sock.accept()
                print(f"[i] + {host}:{port} Connected")
                handle_conn(conn, select_map)
            elif s == stdin.fileno():
                handle_stdin(stdin, select_map, sock.fileno())
            else:
                f = select_map[s]
                handle_msg(f, select_map)


if __name__ == "__main__":
    main()
