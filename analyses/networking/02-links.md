# 2. Delivering on one link

[Previous: packets](01-packets.md) · [Course index](README.md) · [Next: IP](03-internetworking.md)

## The problem: several machines share a medium

Early Ethernet at Xerox PARC connected nearby computers over a shared cable.
Metcalfe and Boggs's 1976 paper describes a system in which stations contend for
the medium, detect interference, and retry after randomized delays. This made a
local network possible without a central scheduler choosing every transmission.
The shared-medium setting explains the original importance of collisions.
[Original Ethernet paper](https://www.cl.cam.ac.uk/teaching/1920/CompNet/files/p395-metcalfe.pdf)

A modern full-duplex switched Ethernet link has a different arrangement: each
endpoint can transmit and receive simultaneously, and the old shared-cable
collision mechanism is not the explanation for ordinary congestion. Output
queues can still fill. Wi-Fi shares radio airtime and has its own medium-access
rules; an Ethernet cable is not an accurate model of all its behavior.

A **link** provides local delivery between attached interfaces. A **frame** is
the unit that a link technology carries. In an Ethernet frame, a destination
address identifies the intended local recipient, a source address identifies
the sender, and a type field identifies what the payload contains. An error
check helps detect corruption. Detecting an error does not prove successful
application processing at the far end.

## Addresses need a scope

An ordinary Ethernet **MAC address** is 48 bits, usually written as six hexadecimal
octets, such as `02:00:00:00:00:01`. Here an octet is eight bits. MAC addresses
belong to link interfaces; they can be locally assigned or changed. Treating one
as an immutable identity for an entire computer will lead you astray.

An Ethernet **switch** learns which source MAC addresses appear on its ports.
For a known destination, it forwards toward the learned port. Broadcasts and
unknown destinations generally need wider forwarding within the relevant VLAN.
A **VLAN** creates a separate logical layer-2 domain on shared infrastructure.
Linux's bridge implements Ethernet switching and exposes a forwarding database
for those learned addresses. [Linux bridge documentation](https://docs.kernel.org/networking/bridge.html)

```text
host A ──┐
         switch ── router interface ── a different network
host B ──┘
```

The switch's job here is delivery within a link-layer domain. A router's job is
forwarding IP packets between networks. One physical appliance can perform both
jobs, which is why household equipment names often blur the distinction.

## Why ARP exists

Suppose A knows that the next IP recipient is `10.10.1.1`, but Ethernet needs a
MAC address. Encoding IP over Ethernet creates a translation problem.

ARP, specified in 1982, resolves an IPv4 protocol address to a local hardware
address. A request asks, in effect, who owns a particular IPv4 address. On
Ethernet that request is broadcast; the owner normally replies with its address.
The sender caches the mapping. ARP is local to the link and provides no general
cryptographic proof of ownership. [RFC 826](https://www.rfc-editor.org/rfc/rfc826.html)

```text
A:       Who has 10.10.1.1? Tell 10.10.1.2.
router:  10.10.1.1 is at 02:00:00:00:00:01.
A:       sends an Ethernet frame to 02:00:00:00:00:01
```

Crucial detail: if A is sending to a remote server, it resolves the **router's**
local address, not the remote server's MAC. The IP destination remains the remote
server. Each routed Ethernet hop replaces the surrounding link-layer envelope.
We will watch that happen in [chapter 8](08-router-lab.md).

## Exercise: inspect without changing anything

On macOS:

```bash
ifconfig
arp -an
```

On Linux:

```bash
ip -br link
ip -4 neigh show
```

Look for interface names, link addresses, and cached neighbors. An empty neighbor
cache is a valid result; these commands do not require it to contain entries.
Virtual interfaces and VPNs can make the listing longer than the number of
physical network sockets on your machine. Do not expect every interface to use
Ethernet addressing.

Write down one observation and its limit. For example: “My cache contains a
mapping for the gateway” establishes cached local addressing information. It
does not establish that the gateway currently forwards packets, that DNS works,
or that a remote server accepts connections. These commands make no changes.

## Checkpoint

**Why not use MAC addresses across the Internet?** A flat address does not
naturally describe where a destination belongs in an enormous collection of
networks. Also, the Internet must span technologies that do not use Ethernet
frames at all. We need an addressing and forwarding agreement above local links.

**Does a switch learn the Internet's routes by observing MAC addresses?** No.
Its forwarding database describes local layer-2 reachability. Route selection
uses a different set of information.

The historical lesson is that local delivery and global reachability solve
different problems. The next chapter introduces the agreement that joins them.
