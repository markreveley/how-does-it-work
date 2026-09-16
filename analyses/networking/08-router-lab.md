# 8. Build a small routed network

[Previous: Linux](07-linux.md) · [Course index](README.md) · [Next: loss and MTU](09-loss-and-mtu.md)

## Mini-project 3: two links and a router

The original internetworking problem was joining networks without replacing their
internals. We can recreate its forwarding mechanism with two virtual Ethernet
links and a Linux stack that participates in both.

```text
namespace hdw-c            namespace hdw-r             namespace hdw-s
client                    router                      server

eth0 ─── veth pair ─── left     right ─── veth pair ─── eth0
10.10.1.2/24   10.10.1.1/24     10.10.2.1/24   10.10.2.2/24
default via 10.10.1.1                         default via 10.10.2.1
```

No virtual interface connects this topology to the VM's external network. The
router's two subnets appear automatically as connected routes when we assign
addresses. Each endpoint gets a default route toward the router. The router
has forwarding disabled initially so we can observe the difference between
having two interfaces and actually forwarding traffic.

Read the short [setup script](labs/network.sh) before running it:

```bash
cat labs/network.sh
sudo bash labs/network.sh up
sudo ip netns list
```

The script refuses to overwrite existing lab state or namespaces. On a setup
failure it cleans up namespaces it already created. At any point, stop foreground
lab commands and run `sudo bash labs/network.sh down` to remove its recorded
namespaces, interfaces, routes, and remaining namespace processes.

The setup's core operations are ordinary commands. For example, this line
creates a virtual cable with one endpoint in the client and one in the router:

```text
ip -n hdw-c link add eth0 type veth peer name left netns hdw-r
```

This is an excerpt for reading; do not run it again after setup. `ip -n NAME`
operates on that namespace. `ip netns exec NAME COMMAND` runs a process using
that namespace's network stack. Both forms keep the following operations scoped
to our lab. [ip-netns manual](https://man7.org/linux/man-pages/man8/ip-netns.8.html)

## Experiment A: an address is not forwarding

```bash
sudo ip -n hdw-c -br address
sudo ip -n hdw-r -4 route
sudo ip -n hdw-c route get 10.10.2.2
sudo ip netns exec hdw-c ping -n -c 2 -W 1 10.10.1.1
sudo ip netns exec hdw-c ping -n -c 2 -W 1 10.10.2.2
```

Predict: the gateway ping works, the server ping fails. The client knows a route,
and both router interfaces exist, but the router is not yet acting as a transit
forwarder. The failed ping intentionally returns a nonzero exit status; run
these exercises interactively rather than combining expected failures with
`set -e`.

Enable forwarding **inside the router namespace**:

```bash
sudo ip netns exec hdw-r sysctl -w net.ipv4.ip_forward=1
sudo ip netns exec hdw-c ping -n -c 2 -W 1 10.10.2.2
```

Now replies should arrive. The sysctl selects whether this network stack forwards
IPv4 packets between interfaces. It does not supply missing routes or override
filtering. [Kernel IP sysctl documentation](https://docs.kernel.org/networking/ip-sysctl.html)

## Experiment B: watch the local envelopes change

**Terminal A**, capture the router's client-facing link:

```bash
sudo ip netns exec hdw-r tcpdump -l -n -e -vv -i left 'arp or icmp'
```

**Terminal B:**

```bash
sudo ip -n hdw-c neigh flush dev eth0
sudo ip netns exec hdw-c ping -n -c 1 -W 1 10.10.2.2
sudo ip -n hdw-c neigh show
```

Expect an ARP request for **10.10.1.1**, followed by IP traffic addressed to
**10.10.2.2**. The client cache should contain its gateway, not the remote
server. `-e` shows link-layer addresses; `-n` avoids name lookup; `-vv` includes
more IP detail. Stop the capture with Ctrl-C.

Repeat Terminal A on `right`, then in Terminal B flush the router's neighbor
entry on that link and send another ping:

```bash
sudo ip -n hdw-r neigh flush dev right
sudo ip netns exec hdw-c ping -n -c 1 -W 1 10.10.2.2
```

For the Echo Request, compare both captures:

| Field | Client-facing link | Server-facing link |
|---|---|---|
| Source/destination IP | `10.10.1.2 → 10.10.2.2` | Same pair |
| Source MAC | Client `eth0` | Router `right` |
| Destination MAC | Router `left` | Server `eth0` |
| TTL | Initial value | One less |

The actual MAC addresses and initial TTL are observations to record, not constants
to memorize. IPv4's header checksum also changes when TTL changes. This is the
local/global address distinction from chapter 2 made visible.

If you see “bad checksum” on locally generated traffic in other captures, consider
checksum offload before concluding that the wire carried corrupt traffic. Capture
position and interface offloads influence what software sees.
[tcpdump manual](https://man7.org/linux/man-pages/man8/tcpdump.8.html)

## Experiment C: trace the hop and its limit

```bash
sudo ip netns exec hdw-c traceroute -n -I -m 4 -w 1 10.10.2.2
sudo ip netns exec hdw-c ping -n -c 1 -W 1 -t 1 10.10.2.2
```

Traceroute should show the router, then the server. The TTL-one ping should
receive Time Exceeded from the router rather than an Echo Reply from the server.
Do not treat this failed ping as a regression: exhausting the hop budget is
the point of the test.

## Experiment D: put an application across the route

**Terminal A:**

```bash
lab_site=$(mktemp -d)
printf 'Hello across two links.\n' > "$lab_site/index.html"
sudo ip netns exec hdw-s python3 -m http.server 8000 --bind 10.10.2.2 --directory "$lab_site"
```

**Terminal B:**

```bash
sudo ip netns exec hdw-s ss -lnt
sudo ip netns exec hdw-c curl --noproxy '*' --connect-timeout 2 --max-time 5 http://10.10.2.2:8000/
```

Expect the text. In a third terminal, capture `tcp port 8000` on either router
interface and repeat the request. Identify a SYN, a SYN-ACK, and application
traffic. Stop all captures and the server when finished, then remove its scratch
directory with `rm -r -- "$lab_site"` in Terminal A.

## Experiment E: break only the return path

Predict the failure before deleting the server's default route:

```bash
sudo ip -n hdw-s route del default
sudo ip netns exec hdw-c ping -n -c 2 -W 1 10.10.2.2
sudo ip -n hdw-s route get 10.10.1.2
```

The route lookup on the server should report unreachable. Capture ICMP on its
`eth0` if you want to see whether requests reach the interface. Depending on
reverse-path validation settings, an incoming request may also be discarded
before reaching the echo responder. Either way, the server lacks the route
needed for this exchange.

Restore it and retest:

```bash
sudo ip -n hdw-s route add default via 10.10.2.1
sudo ip netns exec hdw-c ping -n -c 2 -W 1 10.10.2.2
```

**Project success:** show the two different Ethernet envelopes, an unchanged IP
destination, a decremented TTL, a successful HTTP request, and the effect of
removing a return route. Explain each observation using the earlier chapters.

Keep the topology for chapter 9, or use `sudo bash labs/network.sh down`. To
resume from a clean state, run `up` and enable router IPv4 forwarding again.
