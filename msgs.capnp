@0xbc45f87ce1b13606;

struct PeerAddr {
  ip @0 :UInt32;
  port @1 :UInt16;
}

struct ServerRpcMsg {
  addrs @0 :List(PeerAddr);
}

struct PeerListeningPort {
  port @0 :UInt16;
}

struct PeerMsg {
  type @0 :Type;
  content :union {
    text @1 :Text;
    file :group {
      filename @2 :Text;
      content @3 :Data;
    }
  }

  enum Type {
    text @0;
    file @1;
  }
}
