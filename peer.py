#!/usr/bin/env python
"""ff"""

import ipaddress
import sys
from socket import AF_INET, SOCK_STREAM, create_connection, socket
from time import sleep

import capnp
import msgs_capnp

EXIT_OK = 0
EXIT_ERR = 1

incoming_port: int = 0

class Peer:
    sock: socket

    def __init__(self, sock: socket):
        self.sock = sock

    def send_msg(self):
        pass


class Server:
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

            print(f"[i] Connecting to {host}:{port}")
            try:
                conn = create_connection((host, port))
                conn.send(wire_msg)
                sockets[conn.fileno()] = Peer(conn)
            except OSError as e:
                print(
                    f"[-] Error: Cannot connect to {host}:{port}, {e.strerror}"
                )

        return sockets


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
    peers = server.get_peers()

    while True:
        sleep(1)


if __name__ == "__main__":
    main()
