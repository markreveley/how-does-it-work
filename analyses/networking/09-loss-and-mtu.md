# 9. Make the network misbehave

[Previous: router lab](08-router-lab.md) · [Course index](README.md) · [Next: policy and IPv6](10-policy-and-ipv6.md)

## The problem: a working path is not a constant-rate pipe

Chapter 1's queues and chapter 4's congestion feedback are easier to understand
when you control the bottleneck. A virtual network with no deliberate impairment
mostly measures this machine's kernel and CPU. We will add known constraints
and compare results, not call it an Internet speed test.

Start from chapter 8's working topology, with IPv4 forwarding enabled and its
return route restored. If uncertain, stop lab processes, run `down`, then `up`,
and enable forwarding again:

```bash
sudo ip netns exec hdw-r sysctl -w net.ipv4.ip_forward=1
sudo ip netns exec hdw-c ping -n -c 3 -W 1 10.10.2.2
```

## Experiment A: separate latency from capacity

Linux `tc` manages traffic control. A queueing discipline, or **qdisc**, controls
how an interface queues outgoing traffic. `netem` can add artificial delay, loss,
and rate limits. These are egress settings: applying one to the client's `eth0`
affects traffic leaving the client, not everything everywhere.
[tc-netem manual](https://man7.org/linux/man-pages/man8/tc-netem.8.html)

Add 40 ms of delay in each endpoint's outgoing direction:

```bash
sudo ip netns exec hdw-c tc qdisc replace dev eth0 root netem delay 40ms
sudo ip netns exec hdw-s tc qdisc replace dev eth0 root netem delay 40ms
sudo ip netns exec hdw-c ping -n -c 4 -W 2 10.10.2.2
```

Expect roughly **80 ms of additional round-trip time**, with scheduling variation.
The first request can include extra neighbor discovery overhead; compare later
replies as well. A round trip includes the request path and the reply path.

Now add a 10 Mbit/s egress limit to the client while preserving its delay:

```bash
sudo ip netns exec hdw-c tc qdisc replace dev eth0 root netem delay 40ms rate 10mbit
```

**Terminal A:**

```bash
sudo ip netns exec hdw-s iperf3 -s -B 10.10.2.2
```

**Terminal B:**

```bash
sudo ip netns exec hdw-c iperf3 -c 10.10.2.2 -t 10
```

Expect client-to-server TCP throughput on the order of the imposed limit, usually
below it after overhead and startup effects. `netem` is an emulator affected by
kernel timing and offloads, so exact rates and short-interval bursts can vary.
iperf3 reports measured transport throughput; it is not a file download benchmark.
[iperf3 invocation reference](https://software.es.net/iperf/invoking.html)

## Predict how much data must be in flight

With a 10 Mbit/s bottleneck and an 80 ms RTT, the bandwidth-delay product is:

```text
10,000,000 bits/s × 0.080 s = 800,000 bits = 100,000 bytes
```

This is approximately the data needed in flight to keep that idealized path
busy while waiting for acknowledgments. A sender limited to one 1,000-byte unit
per round trip would achieve only about 100 kbit/s. This explains why pipelining
and windows matter even without any packet loss.

Run another iperf transfer. In **Terminal C**, inspect transport state while it
is active:

```bash
sudo ip netns exec hdw-c ss -tin dst 10.10.2.2
```

Find RTT, congestion window (`cwnd`), and retransmission fields if the installed
version displays them. Linux reports `cwnd` in segments; do not read it as bytes.
There may be separate control and data connections for iperf. Compare repeated
observations rather than treating one sample as a complete history.

## Experiment B: recovery has a cost

Introduce random loss on the client's egress and rerun the transfer:

```bash
sudo ip netns exec hdw-c tc qdisc replace dev eth0 root netem delay 40ms rate 10mbit loss 1%
sudo ip netns exec hdw-c iperf3 -c 10.10.2.2 -t 10
sudo ip netns exec hdw-c tc -s qdisc show dev eth0
```

Record throughput, reported retransmissions, and qdisc statistics before and
after loss. Expect more recovery activity and potentially much lower throughput.
Do not expect exactly 1% of application records to disappear: TCP reconstructs
the stream, losses are random, and the impairment acts on kernel packet buffers.
Segmentation offloads can make those buffers differ from physical wire packets.
This simple sender-side emulator is good for qualitative exploration; controlled
transport research requires more careful topology and offload handling.

Repeat with zero loss while leaving delay and rate unchanged. Does the original
range of throughput return? Change one variable at a time so your explanation can
distinguish causation from coincidence. Stop iperf3 in Terminal A afterward.

Remove the two qdiscs:

```bash
sudo ip netns exec hdw-c tc qdisc del dev eth0 root
sudo ip netns exec hdw-s tc qdisc del dev eth0 root
```

If you already removed one, a “No such file” response simply means there was no
custom root qdisc to delete. Do not apply these cleanup commands to a host interface.

## Experiment C: small pings work, larger packets fail

Different networks have always had different packet-size limits. That historical
mismatch remains visible in modern tunnels, VPNs, and paths with smaller MTUs.
Lower the server-side link's MTU at both ends:

```bash
sudo ip -n hdw-r link set right mtu 1280
sudo ip -n hdw-s link set eth0 mtu 1280
sudo ip netns exec hdw-c ping -n -c 2 -W 1 10.10.2.2
sudo ip netns exec hdw-c ping -n -c 2 -W 1 -M do -s 1400 10.10.2.2
sudo ip netns exec hdw-c ping -n -c 2 -W 1 -M do -s 1200 10.10.2.2
```

The small default payload should work. The 1,400-byte payload plus ordinary
20-byte IPv4 and 8-byte ICMP headers makes a 1,428-byte IP packet, too large for
the downstream link. `-M do` requests no fragmentation. Expect fragmentation-needed
feedback or a local message-too-long error after the path limit has been learned.
The 1,200-byte payload fits. [ping manual](https://man7.org/linux/man-pages/man8/ping.8.html)

Capture `icmp` on the router's `left` interface while trying the oversized probe.
Why might the first attempt show an ICMP error while later attempts are rejected
locally? The sender can cache path information. The visible failure location can
change as it learns.

The operational lesson is precise: successful small probes do not prove that
all packet sizes work. Blocking all ICMP can hide useful feedback, including
path-size errors. That can produce a connection which starts but stalls when
larger data moves.

Restore the link sizes:

```bash
sudo ip -n hdw-r link set right mtu 1500
sudo ip -n hdw-s link set eth0 mtu 1500
```

Learned path MTU information may outlive the immediate experiment. A clean
`down`/`up` cycle resets the lab when you want a fresh baseline. Stop captures
first and re-enable router IPv4 forwarding after rebuilding.

## Checkpoint

Explain all three without using “the network is slow” as the complete answer:

- A short request has low throughput but still feels responsive.
- A high-capacity path transfers poorly when the available flight window is small.
- A handshake succeeds while subsequent large packets fail.

The explanations should refer to work size and latency, bandwidth-delay product,
and path MTU respectively. In the next chapter, we introduce a different source
of failure: the network is technically able to carry a packet but policy forbids it.
