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
        self.sock = create_connection((addr, int(port)))

    def get_peers(self) -> list[socket]:
        msg = self.sock.recv(4)
        if len(msg) == 0:
            print("Connection unexpectedly died")
            exit(EXIT_ERR)

        size = int.from_bytes(msg, byteorder='big', signed=False)
        count = 0

        while count != size:
            msg = self.sock.recv(4096)
            count += len(msg)
            if len(msg) == 0:
                break
            else:
                self.buff += msg

        if count != size:
            print("Connection unexpectedly died")
            exit(EXIT_ERR)

        addrs = msgs_capnp.ServerRpcMsg.from_bytes(self.buff)
        sockets: list[socket] = []
        for addr in addrs.addrs:
            host = ipaddress.IPv4Address(addr.ip).exploded
            port = addr.port
            print(f"[i] Connecting to {host}:{port}")
            conn = create_connection((host, port))
            sockets.append(conn)


        return sockets


def main():
    if len(sys.argv) != 3:
        exit(1)

    server = Server(sys.argv[1], sys.argv[2])
    peers = server.get_peers()
    print(peers)


if __name__ == "__main__":
    main()
