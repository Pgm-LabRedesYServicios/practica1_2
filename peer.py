#!/usr/bin/env python
"""ff"""

import ipaddress
import sys
from socket import create_connection, htons, socket

import capnp
import msgs_capnp

EXIT_OK = 0
EXIT_ERR = 1


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

    def get_peers(self) -> set[socket]:
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

        sockets: set[socket] = set()

        # Deserialize the message and connect to the peers sent by the server
        addrs = msgs_capnp.ServerRpcMsg.from_bytes(self.buff)
        for addr in addrs.addrs:
            host = ipaddress.IPv4Address(addr.ip).exploded
            port = addr.port

            print(f"[i] Connecting to {host}:{port}")
            try:
                conn = create_connection((host, port))
                sockets.add(conn)
            except OSError as e:
                print(
                    f"[-] Error: Cannot connect to {host}:{port}, {e.strerror}"
                )

        return sockets


def main():
    if len(sys.argv) != 3:
        exit(1)

    server = Server(sys.argv[1], sys.argv[2])
    peers = server.get_peers()
    print(peers)


if __name__ == "__main__":
    main()
