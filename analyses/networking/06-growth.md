# 6. Growing beyond the original assumptions

[Previous: names and applications](05-names-and-applications.md) · [Course index](README.md) · [Next: Linux](07-linux.md)

## The problem: growth stresses several resources at once

An address format, a routing table, and an administrative system can each run
out of room in different ways. “The Internet needed more addresses” explains
part of the story, but not all the choices that followed.

Earlier IPv4 allocation used address classes with coarse size boundaries. A site
could need far more than one class provided but far fewer than the next offered.
CIDR, documented in 1993, replaced those rigid boundaries with explicit prefix
lengths and supported aggregation of routes. It addressed address allocation
pressure and routing-table growth together.
[Historical RFC 1519](https://www.rfc-editor.org/rfc/rfc1519.html)

Suppose an operator reaches four contiguous `/24` networks through one neighbor:

```text
10.20.0.0/24   10.20.1.0/24   10.20.2.0/24   10.20.3.0/24
                         ↓
                    10.20.0.0/22
```

The aggregate summarizes the same address space. It is useful only where its
forwarding promise is valid. If one more-specific destination needs a different
path, it may require an exception; prefixes are compact claims about reachability.

## Exercise: aggregate and find the boundary

```bash
python3 - <<'PY'
from ipaddress import collapse_addresses, ip_network
networks = [ip_network(f"10.20.{i}.0/24") for i in range(4)]
print(*collapse_addresses(networks))
networks.append(ip_network("10.20.4.0/24"))
print(*collapse_addresses(networks))
PY
```

Expect `10.20.0.0/22`, then `10.20.0.0/22 10.20.4.0/24`. The fifth subnet cannot
be merged into that `/22`; expanding to a `/21` would also claim three additional
`/24`s. There are no side effects to clean up.

## Who tells a router what it can reach?

So far we supplied routes by hand. A routing protocol automates exchanging and
selecting reachability information. **Forwarding** applies the resulting state
to packets; **routing** is the process that produces that state.

Within an administrative network, a protocol such as OSPF can distribute
link-state information and compute paths using configured costs. This is not
the same operation as resolving a hostname or learning a MAC address.
[OSPFv2, RFC 2328](https://www.rfc-editor.org/rfc/rfc2328.html)

Between independently administered networks, BGP exchanges reachability and
path attributes. An **autonomous system** is an administrative routing domain
with a routing policy. Policy matters because operators have different
relationships and objectives; the globally selected path is not simply the
geographically shortest one. BGP's AS path also helps detect routing loops.
[BGP-4, RFC 4271](https://www.rfc-editor.org/rfc/rfc4271)

This administrative boundary explains why the Internet has no single routing
brain. Our lab's static routes let us study forwarding without deploying those
control protocols. It is a small routed internetwork, not a simulation of the
global BGP system.

## NAT bought time and changed the connection model

Network Address Translation was proposed in 1994 as a way to reuse addresses
while limiting demand for globally unique IPv4 space. Rewriting addresses at a
boundary meant a site's internal addressing could differ from what the outside
network saw. This introduced translation state and complications for protocols
that carry addresses inside their payloads.
[Historical RFC 1631](https://www.rfc-editor.org/rfc/rfc1631.html)

Private IPv4 ranges are `10.0.0.0/8`, `172.16.0.0/12`, and `192.168.0.0/16`.
Different organizations may reuse them; they are not intended to be globally
routed between enterprises. Our lab uses part of `10.0.0.0/8` inside isolated
namespaces. Private addressing does not itself imply filtering or translation.
[RFC 1918](https://www.rfc-editor.org/rfc/rfc1918.html)

Many home routers use **NAPT**, commonly called NAT: they translate transport
ports as well as addresses, allowing several internal connections to share one
external address. A mapping might look like:

```text
internal source          translated source       destination
10.10.1.2:51000     →     10.10.2.1:62000     →    10.10.2.2:8000
```

Return traffic is translated back using stored state. Unsolicited inbound
connections need an appropriate mapping or other arrangement. Routing still
chooses the next hop; filtering still decides what is permitted. NAT is neither
of those functions. [Traditional NAT, RFC 3022](https://www.rfc-editor.org/rfc/rfc3022.html)

The example's translated address is private too. NAT is a rewriting mechanism;
the mechanism does not require a public address in a disconnected lab.

## IPv6 changes the address budget

IPv6 uses 128-bit addresses. Its late-1990s specification and the later RFC 8200
standard describe a revised Internet-layer protocol, not an extra field bolted
onto an IPv4 packet. IPv6 uses a fixed base header and extension headers, and
routers do not fragment packets in transit. IPv4-only and IPv6-only peers cannot
communicate directly just because their addresses name the same machine; dual
stack, translation, or tunneling must provide an appropriate path.
[Historical RFC 2460](https://www.rfc-editor.org/rfc/rfc2460.html),
[IPv6 standard, RFC 8200](https://www.rfc-editor.org/rfc/rfc8200.html)

IPv6 Neighbor Discovery uses ICMPv6 for tasks including neighbor address
resolution and router discovery. It replaces IPv4 ARP's role and adds related
functions; it is not “ARP with longer addresses.” Router advertisements can
provide information used in address configuration and default-router selection.
We will set static IPv6 routes to keep the first experiment explicit.
[RFC 4861](https://www.rfc-editor.org/rfc/rfc4861)

More address space removes the scarcity pressure behind much address sharing.
It does not remove the need for routing policy, sensible filtering, naming, or
operational care.

## Protocol evolution continues above IP

TCP's ordered stream can delay later bytes while a missing earlier range is
recovered. QUIC, standardized in 2021, runs over UDP and implements reliable
streams, congestion control, and integrated cryptographic protection. Independent
streams reduce cross-stream delivery blocking, though they can still share a
congested path. Connection IDs help separate connection identity from a fixed
address/port pair. UDP provides an envelope; QUIC supplies substantial transport
behavior above it. [RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html)

HTTP/3 maps HTTP onto QUIC. This is why “HTTPS always means TCP” is no longer an
adequate model. Our exercises deliberately choose HTTP over TCP where that is
the mechanism being studied. [RFC 9114](https://www.rfc-editor.org/rfc/rfc9114.html)

## Checkpoint: distinguish the responses to growth

| Mechanism | Pressure it addresses | Cost or remaining problem |
|---|---|---|
| CIDR and aggregation | Coarse allocation and route-table growth | Aggregates must reflect real reachability |
| DNS delegation | Central coordination of names | Caches and distributed failures |
| NAT/NAPT | IPv4 address reuse and sharing | Translation state and harder inbound connectivity |
| IPv6 | Address space and Internet-layer redesign | Deployment and interoperability work |
| BGP | Reachability between policy domains | Policy complexity and trust in advertisements |

We have enough universal vocabulary to understand what Linux is doing. Next we
connect these abstractions to actual interfaces, processes, and kernel state.
