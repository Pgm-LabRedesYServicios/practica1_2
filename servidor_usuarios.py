#!/usr/bin/env python
"""ff"""

import ipaddress
import sys
from socket import AF_INET, htons, socket

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


def main():
    if len(sys.argv) != 2:
        print(f"Usage:\n\t{sys.argv[0]} <port>")
        sys.exit(EXIT_ERR)

    peers: dict[ipaddress.IPv4Address, int] = dict()

    sock = socket(AF_INET)
    try:
        print(f"[i] Binding to {sys.argv[1]}")
        sock.bind(('0.0.0.0', int(sys.argv[1])))
        print(f"[i] Listening on {sys.argv[1]}")
        sock.listen(5)
        print("[i] Waiting for connections")
        conn, addr = sock.accept()
    except ValueError:
        print(f"The value {sys.argv[1]} is not a valid port number")
        sys.exit(EXIT_ERR)
    except OSError as e:
        print(e)
        sys.exit(EXIT_ERR)

    try:
        addrs = msgs_capnp.ServerRpcMsg.new_message()
        addrs_list = addrs.init('addrs', 1)

        peer1 = msgs_capnp.PeerAddr.new_message()
        peer1.ip = int.from_bytes(ipaddress.IPv4Address(
            "127.0.0.1").packed, byteorder='big', signed=False)
        peer1.port = 4433
        addrs_list[0] = peer1

        encoded_msg = addrs.to_bytes()

        conn.send(len(encoded_msg).to_bytes(4, byteorder='big', signed=False))
        conn.send(encoded_msg)

    finally:
        conn.close()
        sock.close()

    print(peers)


if __name__ == "__main__":
    main()
