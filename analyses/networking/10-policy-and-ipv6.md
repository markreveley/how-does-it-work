# 10. Policy, translation, and IPv6

[Previous: loss and MTU](09-loss-and-mtu.md) · [Course index](README.md) · [Next: capstone](11-capstone.md)

## The problem: possible delivery is not permission

The early best-effort internetwork agreement answers how a packet might reach
its destination. Operators also need to decide which traffic they will carry.
Filtering and connection tracking add policy and state around that forwarding
mechanism. Linux's Netfilter infrastructure provides packet-processing hooks;
nftables provides rule expression and administration, succeeding several older
tool interfaces. [Netfilter nftables project](https://www.netfilter.org/projects/nftables/)

Begin with a fresh topology so earlier delay and MTU experiments do not affect
your conclusions. Stop all lab servers and captures before resetting:

```bash
sudo bash labs/network.sh down
sudo bash labs/network.sh up
sudo ip netns exec hdw-r sysctl -w net.ipv4.ip_forward=1
```

In **Terminal A**, start a new lab HTTP server:

```bash
policy_site=$(mktemp -d)
printf 'Policy lab response.\n' > "$policy_site/index.html"
sudo ip netns exec hdw-s python3 -m http.server 8000 --bind 10.10.2.2 --directory "$policy_site"
```

## Experiment A: permit a route but reject a service

A simplified routed packet path is:

```text
arrival → prerouting → routing decision ─┬→ input → local process
                                       └→ forward → postrouting → output link

local process → output → postrouting → output link
```

Input is for traffic addressed to this stack; forward is for traffic passing
through it. Filtering the router's input chain would not express our intended
policy for traffic from client to server. Hook names describe processing points;
a table is a container for rules, not a physical network device.
[nftables chain documentation](https://wiki.nftables.org/wiki-nftables/index.php/Configuring_chains)

**Terminal B:**

```bash
sudo ip netns exec hdw-r nft -f - <<'NFT'
table inet lesson {
    chain forward {
        type filter hook forward priority 0; policy accept;
        ip saddr 10.10.1.2 ip daddr 10.10.2.2 tcp dport 8000 counter reject with tcp reset
    }
}
NFT
sudo ip netns exec hdw-c ping -n -c 2 -W 1 10.10.2.2
sudo ip netns exec hdw-c curl --noproxy '*' --connect-timeout 2 --max-time 5 http://10.10.2.2:8000/
sudo ip netns exec hdw-r nft list table inet lesson
```

Predict: ping succeeds, curl fails quickly, and the rule's counter increases.
An active rejection can resemble a closed service to the client. The counter
and packet capture provide the missing evidence about where the rejection arose.

Replace only this lab chain's rules with a silent drop:

```bash
sudo ip netns exec hdw-r nft flush chain inet lesson forward
sudo ip netns exec hdw-r nft add rule inet lesson forward ip saddr 10.10.1.2 ip daddr 10.10.2.2 tcp dport 8000 counter drop
sudo ip netns exec hdw-c curl --noproxy '*' --connect-timeout 2 --max-time 5 http://10.10.2.2:8000/
```

Now curl should time out. A timeout alone cannot distinguish deliberate dropping
from packet loss, a broken return path, or an unresponsive peer. Delete the lab
table and verify HTTP works again:

```bash
sudo ip netns exec hdw-r nft delete table inet lesson
sudo ip netns exec hdw-c curl --noproxy '*' --connect-timeout 2 --max-time 5 http://10.10.2.2:8000/
```

This is a targeted demonstration, not a production firewall policy. We neither
set a default-deny policy nor account for every service this router might need.

## Experiment B: translate the source and observe who the server sees

First remove the server's default route again. Without translation, the server
cannot return traffic to `10.10.1.2`:

```bash
sudo ip -n hdw-s route del default
sudo ip netns exec hdw-c curl --noproxy '*' --connect-timeout 2 --max-time 5 http://10.10.2.2:8000/
```

Now configure source NAT on the router's server-facing egress:

```bash
sudo ip netns exec hdw-r nft -f - <<'NFT'
table ip lesson_nat {
    chain postrouting {
        type nat hook postrouting priority 100; policy accept;
        ip saddr 10.10.1.0/24 oifname "right" counter snat to 10.10.2.1
    }
}
NFT
sudo ip netns exec hdw-c curl --noproxy '*' --connect-timeout 2 --max-time 5 http://10.10.2.2:8000/
sudo ip netns exec hdw-r conntrack -L -p tcp
```

Expect a response even though the server still lacks a route to the client's
subnet. The server sees source `10.10.2.1`, which is directly reachable on its
own link. The router stores the translation and reverses it on replies. Compare
the HTTP server's access log before and after NAT, and capture TCP port 8000 on
`left` and `right` to see the source address change.

For stateful NAT, the first packet establishes a mapping; later packets follow
that state. A NAT-chain counter is therefore not a complete count of every
packet translated in an established flow. SNAT uses a specified source address;
masquerading chooses an appropriate interface address, useful when that address
changes. [nftables NAT documentation](https://wiki.nftables.org/wiki-nftables/index.php/Performing_Network_Address_Translation_(NAT))

`conntrack` exposes the tracked original and reply tuples. Entries can outlive
an individual HTTP request. This is why changing a NAT rule does not necessarily
change an existing connection's mapping immediately.
[conntrack manual](https://www.netfilter.org/projects/conntrack-tools/conntrack-manpage.html)

The contrast explains NAT's historical appeal and its cost: the server no longer
needs a route to each internal client address, but it also does not see that
client's original source identity in IP. Applications may need other explicit
identity mechanisms.

Restore ordinary routing and remove only the lab's translation state:

```bash
sudo ip -n hdw-s route add default via 10.10.2.1
sudo ip netns exec hdw-r nft delete table ip lesson_nat
sudo ip netns exec hdw-r conntrack -F
sudo ip netns exec hdw-c curl --noproxy '*' --connect-timeout 2 --max-time 5 http://10.10.2.2:8000/
```

The flush is scoped to the isolated router namespace. Stop the HTTP server in
Terminal A and remove its directory with `rm -r -- "$policy_site"` there.

## Experiment C: repeat the route with IPv6

We will use addresses from the documentation prefix `2001:db8::/32` entirely
inside the disconnected lab. They must not be treated as assigned public
addresses. [RFC 3849](https://www.rfc-editor.org/rfc/rfc3849.html)

```text
hdw-c                         hdw-r                            hdw-s
2001:db8:1::2/64 ── 2001:db8:1::1/64  2001:db8:2::1/64 ── 2001:db8:2::2/64
```

Configure the addresses once:

```bash
sudo ip -n hdw-c -6 address add 2001:db8:1::2/64 dev eth0
sudo ip -n hdw-r -6 address add 2001:db8:1::1/64 dev left
sudo ip -n hdw-r -6 address add 2001:db8:2::1/64 dev right
sudo ip -n hdw-s -6 address add 2001:db8:2::2/64 dev eth0
sudo ip -n hdw-c -6 route add default via 2001:db8:1::1
sudo ip -n hdw-s -6 route add default via 2001:db8:2::1
sudo ip netns exec hdw-r sysctl -w net.ipv6.conf.all.forwarding=1
sudo ip -n hdw-c -6 address show dev eth0
sudo ip -n hdw-r -6 address show
sudo ip -n hdw-s -6 address show dev eth0
```

Wait until the new addresses no longer show `tentative`; IPv6 normally checks for
duplicate addresses before using them. If an address says `dadfailed`, investigate
the duplicate rather than continuing. If IPv6 is disabled in your VM, record that
environment limitation and enable it in the disposable VM before this exercise.
[IPv6 address configuration, RFC 4862](https://www.rfc-editor.org/rfc/rfc4862.html)

**Terminal A:**

```bash
sudo ip netns exec hdw-r tcpdump -l -n -i left icmp6
```

**Terminal B:**

```bash
sudo ip -n hdw-c -6 neigh flush dev eth0
sudo ip netns exec hdw-c ping -6 -n -c 3 -W 2 2001:db8:2::2
sudo ip -n hdw-c -6 neigh show
```

Look for Neighbor Solicitation and Neighbor Advertisement, then Echo traffic.
The conceptual questions are the same: which next hop, which local neighbor,
which return route? The on-wire neighbor mechanism is different from ARP.
Stop the capture when finished.

For an application test, in Terminal A create another scratch directory and
bind a server to the server's IPv6 address:

```bash
ipv6_site=$(mktemp -d)
printf 'Hello over IPv6.\n' > "$ipv6_site/index.html"
sudo ip netns exec hdw-s python3 -m http.server 8000 --bind 2001:db8:2::2 --directory "$ipv6_site"
```

In Terminal B:

```bash
sudo ip netns exec hdw-c curl --noproxy '*' -g -6 --connect-timeout 2 --max-time 5 'http://[2001:db8:2::2]:8000/'
```

Brackets separate the IPv6 literal from the URL's port; `-g` disables curl's URL
globbing. Expect your text without any NAT rule. Stop the server and remove its
scratch directory with `rm -r -- "$ipv6_site"` in Terminal A.

## Checkpoint and cleanup

Explain why routing, filtering, and translation are three different operations
even when the same Linux machine performs all of them. Your evidence should
include a successful ping with blocked HTTP, a changed source address after NAT,
and a routed IPv6 response with no translation.

Run `sudo bash labs/network.sh down` when finished. The final chapter gives you
a repeatable method for diagnosing failures without guessing at configuration.
