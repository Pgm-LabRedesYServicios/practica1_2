#!/usr/bin/env python
"""ff"""

import ipaddress
import sys
from select import select
from socket import AF_INET, create_connection, socket

import capnp
import msgs_capnp

EXIT_OK = 0
EXIT_ERR = 1


class Peer:
    sock: socket
    host: int
    port: int

    def __init__(self, sock: socket, host: str, port: int):
        self.sock = sock
        self.port = port
        self.host = int.from_bytes(
            ipaddress.IPv4Address(host).packed,
            byteorder='big',
            signed=False
        )

    def send_msg(self):
        pass


def encode_peer(peer: Peer) -> bytearray:
    """
    Allocates a peer struct and fills it with the peer info
    """
    peer_msg = msgs_capnp.PeerAddr.new_message()
    peer_msg.ip = peer.host
    peer_msg.port = peer.port

    return peer_msg


def send_peers(conn: socket, peers: list[Peer]):
    """
    Given a new peer connection and a list of peers it sends it in the correct
    format to the peer
    """
    addrs = msgs_capnp.ServerRpcMsg.new_message()
    addrs_list = addrs.init('addrs', len(peers))
    for i in range(len(peers)):
        addrs_list[i] = encode_peer(peers[i])

    encoded_msg = addrs.to_bytes()

    conn.send(len(encoded_msg).to_bytes(4, byteorder='big', signed=False))
    conn.send(encoded_msg)


def handle_new_peer(conn: socket, host: str, port: int, peers: list[Peer], select_map: dict[int, socket]):
    send_peers(conn, peers)
    peer = Peer(conn, host, port)
    peers.append(peer)
    select_map[conn.fileno()] = conn


def handle_msg(sock: socket, peers: list[Peer], select_map: dict[int, socket]):
    # TODO: Detect closed connections and dispatch
    data = sock.recv(2048)
    if len(data) == 0:
        print(f"[i] - {sock} disconnected")
        del select_map[sock.fileno()]


def main():
    if len(sys.argv) != 2:
        print(f"Usage:\n\t{sys.argv[0]} <port>")
        sys.exit(EXIT_ERR)

    # This is a dummy to start testing
    # TODO: Find a way to make it a dict
    # peers: dict[ipaddress.IPv4Address, int] = dict()
    peers: list[Peer] = []

    # Try to bind and listen to the given port
    sock = socket(AF_INET)
    try:
        print(f"[i] Binding to {sys.argv[1]}")
        sock.bind(('0.0.0.0', int(sys.argv[1])))
        print(f"[i] Listening on {sys.argv[1]}")
        sock.listen(5)
        sock.setblocking(False)
    except ValueError:
        print(f"The value {sys.argv[1]} is not a valid port number")
        sys.exit(EXIT_ERR)
    except OSError as e:
        print(e)
        sys.exit(EXIT_ERR)

    print("[i] Waiting for connections")
    select_map = {}
    select_map[sock.fileno()] = sock

    while(True):
        selected, x, y = select(select_map, [], [])
        for s in selected:
            if s == sock.fileno():
                conn, (host, port) = sock.accept()
                print(f"[i] + New connection from {host}:{port}")
                handle_new_peer(conn, host, port, peers, select_map)
            else:
                f = select_map[s]
                handle_msg(f, peers, select_map)

    sock.close()
    print(peers)


if __name__ == "__main__":
    main()
