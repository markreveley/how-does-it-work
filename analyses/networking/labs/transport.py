#!/usr/bin/env python3
"""Small, deliberately inspectable TCP and UDP exercises; standard library only."""

import argparse
import socket


def tcp_server(args):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((args.host, args.port))
        listener.listen(1)
        print(f"TCP listening on {args.host}:{args.port}", flush=True)
        while True:
            connection, peer = listener.accept()
            with connection:
                connection.settimeout(10)
                print(f"peer: {peer}", flush=True)
                pending = b""
                try:
                    while True:
                        chunk = connection.recv(3)
                        if not chunk:
                            if pending:
                                print(f"incomplete record at EOF: {pending!r}", flush=True)
                            break
                        print(f"recv chunk: {chunk!r}", flush=True)
                        pending += chunk
                        while b"\n" in pending:
                            record, pending = pending.split(b"\n", 1)
                            print(f"complete record: {record!r}", flush=True)
                            connection.sendall(record.upper() + b"\n")
                        if len(pending) > 4096:
                            print("record too long; closing", flush=True)
                            break
                except (TimeoutError, ConnectionError) as error:
                    print(f"connection ended: {error}", flush=True)


def tcp_client(args):
    with socket.create_connection((args.host, args.port), timeout=3) as connection:
        connection.sendall(b"one\ntwo\n")
        connection.shutdown(socket.SHUT_WR)
        with connection.makefile("rb") as stream:
            for record in stream:
                print(f"reply: {record!r}")


def udp_server(args):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((args.host, args.port))
        print(f"UDP listening on {args.host}:{args.port}", flush=True)
        received = 0
        while True:
            payload, peer = sock.recvfrom(4096)
            received += 1
            if args.drop_every and received % args.drop_every == 0:
                print(f"application discards: {payload!r}", flush=True)
                continue
            print(f"echo: {payload!r}", flush=True)
            sock.sendto(payload, peer)


def udp_client(args):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(0.3)
        # connect selects a peer; it does not perform a UDP handshake.
        sock.connect((args.host, args.port))
        for sequence in range(1, args.count + 1):
            payload = str(sequence).encode("ascii")
            sock.send(payload)
            try:
                reply = sock.recv(4096)
                print(f"sent {sequence}, received {reply!r}")
            except socket.timeout:
                print(f"sent {sequence}, timeout: outcome unknown")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("tcp-server", "tcp-client", "udp-server", "udp-client"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--drop-every", type=int, default=0)
    parser.add_argument("--count", type=int, default=6)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or args.count < 1 or args.drop_every < 0:
        parser.error("use a port in 1..65535, a positive count, and nonnegative drop-every")
    try:
        {"tcp-server": tcp_server, "tcp-client": tcp_client,
         "udp-server": udp_server, "udp-client": udp_client}[args.mode](args)
    except KeyboardInterrupt:
        print("\nstopped")
    except OSError as error:
        parser.exit(1, f"network error: {error}\n")


if __name__ == "__main__":
    main()
