# 3. Joining unlike networks

[Previous: links](02-links.md) · [Course index](README.md) · [Next: transport](04-transport.md)

## The problem: a successful network is still only one network

ARPANET, packet radio, and satellite networks had different operating conditions.
Making them interoperate by requiring every network to adopt identical internals
would have limited who could join. The alternative was a common internetwork
agreement, with gateways connecting independently designed networks. ARPANET's
January 1, 1983 transition from NCP to TCP/IP was an important deployment milestone,
not the moment every networking idea appeared fully formed.
[Participant history](https://www.internetsociety.org/internet/history-internet/brief-history-internet/)

IP supplies a common packet format and source/destination addressing. Its basic
service is best-effort datagram delivery: packets can be lost, duplicated, or
arrive out of order. IPv4 uses 32-bit addresses. Routers forward packets toward
destinations, while each underlying link carries the packet using its own rules.
IPv4's foundational specification explicitly leaves reliability and sequencing
outside IP's scope. [RFC 791, sections 1–2](https://www.rfc-editor.org/rfc/rfc791.html)

This is a useful engineering trade: a small shared contract can connect many
different networks. Applications needing stronger delivery guarantees can build
them above that contract. The later architectural discussion of the **end-to-end
principle** explains why some correctness checks still belong at endpoints even
when lower layers also help. [RFC 1958](https://www.rfc-editor.org/rfc/rfc1958.html)

## Layers describe responsibilities

For a simple unencrypted HTTP/1.1 request over Ethernet:

```text
Ethernet frame
└── IP packet
    └── TCP segment
        └── some bytes from an HTTP message
```

The nesting is called **encapsulation**. It does not mean one application message
always fits into one packet. A TCP segment may contain part of a message, several
small messages, or only control information.

You may encounter a seven-layer OSI model. It is useful vocabulary, but the
Internet was not assembled by filling in seven boxes in order. For this course,
ask four practical questions: local link delivery, internetwork delivery,
process-to-process transport, and application meaning. The Internet host
requirements document uses these link, Internet, transport, and application
groupings. [RFC 1122, section 1.1.3](https://www.rfc-editor.org/rfc/rfc1122.html)

## Prefixes tell us which destinations travel together

Consider our future lab:

```text
client                   router                    server
10.10.1.2/24 ── 10.10.1.1/24  10.10.2.1/24 ── 10.10.2.2/24
      link A                                     link B
```

The `/24` says that 24 leading bits form the prefix. In `10.10.1.0/24`, the first
three octets identify the prefix and eight bits remain. This ordinary IPv4
subnet has 256 addresses, with `.0` as its network address and `.255` as its
broadcast address. Do not generalize “subtract two” to every prefix: `/31`
point-to-point links and `/32` host routes have other uses.
[The `/31` exception, RFC 3021](https://www.rfc-editor.org/rfc/rfc3021.html)

A simplified client route table might say:

| Destination prefix | Action |
|---|---|
| `10.10.1.0/24` | Deliver directly on link A |
| `10.10.2.0/24` | Send via `10.10.1.1` on link A |
| `0.0.0.0/0` | Send other destinations via a default gateway, if configured |

Within the selected routing table, a **longest-prefix match** chooses the most
specific matching route. `/24` beats `/0`. The **next hop** is the immediate
recipient selected by that route; the final IP destination can be much farther
away. A default route is simply the least specific IPv4 prefix, not a special
connection to an all-knowing Internet service. Linux can additionally select
tables using policy rules; this course begins with the ordinary main table.
[ip-route manual](https://man7.org/linux/man-pages/man8/ip-route.8.html)

On a normal routed path, the client retains the server's destination IP address
while addressing the first frame to its gateway. The router removes that local
envelope, chooses its next output, and creates the next link's envelope. The
reply needs a usable route back. A valid outward route alone is insufficient.

## Exercise: make prefix arithmetic concrete

Predict which route each destination matches:

```bash
python3 - <<'PY'
from ipaddress import ip_address, ip_network
routes = [ip_network(p) for p in ("0.0.0.0/0", "10.10.0.0/16", "10.10.2.0/24")]
for value in ("10.10.2.2", "10.10.9.4", "192.0.2.8"):
    address = ip_address(value)
    match = max((p for p in routes if address in p), key=lambda p: p.prefixlen)
    print(address, "->", match)
subnet = ip_network("10.10.2.0/24")
print("mask:", subnet.netmask, "total addresses:", subnet.num_addresses)
PY
```

Expected matches: `/24`, `/16`, and `/0`, followed by mask `255.255.255.0` and
256 addresses. Add a `10.10.2.2/32` route. Why does only the first lookup change?
No traffic is sent and nothing needs cleanup.

## Failure needs a vocabulary too

Forwarding loops are possible. IPv4's TTL field limits a packet's lifetime;
ordinary forwarding decrements it at each router. ICMP provides control/error
messages, including Time Exceeded and Destination Unreachable. ICMP Echo
Request/Reply powers `ping`. ICMP carries operational information, not an
application's web response. [RFC 792](https://www.rfc-editor.org/rfc/rfc792.html)

`traceroute` sends probes with increasing TTLs and examines replies. Its output
shows responding interfaces along observed probes, not a guaranteed complete
path diagram. Asterisks can mean filtering, loss, or rate limiting; they do not
by themselves prove forwarding stopped. We will run it on a controlled path.

Another mismatch comes from packet sizes. A link's **MTU** bounds the size of
the IP packet it can carry without link-specific complications. A path can have
a smaller MTU than the sender's first link. IPv4 fragmentation and path MTU
discovery are responses to that mismatch. With the Don't Fragment flag set,
an oversized packet can trigger an ICMP fragmentation-needed response so the
sender learns to use smaller packets. [RFC 1191](https://www.rfc-editor.org/rfc/rfc1191)

## Checkpoint

**Does IP promise to repair a lost packet?** No. Choosing that narrow service
made it easier to connect unlike networks, but moves recovery elsewhere.

**Does a successful ping prove a website works?** It demonstrates that these
ICMP requests and replies succeeded. The website additionally depends on a
listening process, transport, possibly name resolution and TLS, and application
behavior. Each is a separate hypothesis to test.
