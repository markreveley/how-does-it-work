# 11. A debugging capstone

[Previous: policy and IPv6](10-policy-and-ipv6.md) · [Course index](README.md)

## Mini-project 4: write a network incident notebook

The history has left us with separate mechanisms because they solve separate
problems. That separation is useful when something fails: you can gather evidence
at one boundary without assuming every other boundary works.

Rebuild the chapter 8 topology and enable router IPv4 forwarding. Run its HTTP
server again with the scratch directory and cleanup procedure from that chapter.
Verify one successful request. Then introduce each fault below independently,
repair it, and establish the baseline again before moving on.

For every incident, record:

```text
Symptom:
First hypothesis:
Command and observation that distinguish it from another hypothesis:
Packet path or application phase where the failure occurs:
Smallest repair:
Evidence that the repair worked:
Which historical design choice made these separate failure modes possible:
```

## Fault 1: the listener is in the wrong place

Stop the server and restart it in `hdw-s` bound to `127.0.0.1`, using the same
scratch directory. Compare these requests:

```bash
sudo ip netns exec hdw-s curl --noproxy '*' --max-time 3 http://127.0.0.1:8000/
sudo ip netns exec hdw-c curl --noproxy '*' --connect-timeout 2 --max-time 5 http://10.10.2.2:8000/
sudo ip netns exec hdw-s ss -lntp
```

**Explain before repairing:** the process exists, but the socket is bound only
to that namespace's loopback address. A packet addressed to `10.10.2.2` does not
match it. Restart with `--bind 10.10.2.2`, then retest. Reconfiguring DNS or NAT
would not correct this listener mismatch.

## Fault 2: a plausible but wrong next hop

Replace the client's default gateway with an unused address on the same link:

```bash
sudo ip -n hdw-c route replace default via 10.10.1.254
sudo ip -n hdw-c route get 10.10.2.2
sudo ip netns exec hdw-c curl --noproxy '*' --connect-timeout 2 --max-time 5 http://10.10.2.2:8000/
sudo ip -n hdw-c neigh show
```

**Explain before repairing:** route selection can succeed while neighbor
resolution fails. Capture ARP on the client and look for requests for `.254`.
Depending on timing, the neighbor state may be `INCOMPLETE` or `FAILED`.

Restore the correct gateway:

```bash
sudo ip -n hdw-c route replace default via 10.10.1.1
sudo ip netns exec hdw-c curl --noproxy '*' --connect-timeout 2 --max-time 5 http://10.10.2.2:8000/
```

## Fault 3: correct name syntax, wrong address information

Both requests keep the HTTP hostname the same. One supplies a bad address mapping:

```bash
sudo ip netns exec hdw-c curl --noproxy '*' --connect-timeout 2 --max-time 5 \
  --resolve story.test:8000:10.10.2.99 http://story.test:8000/
sudo ip netns exec hdw-c curl --noproxy '*' --connect-timeout 2 --max-time 5 \
  --resolve story.test:8000:10.10.2.2 http://story.test:8000/
```

**Explain before repairing:** this is an application-supplied mapping experiment,
not a DNS server deployment. It demonstrates how wrong address information can
break a request even when routing to the server's actual address works. In a
real resolver incident, compare the application's lookup path, DNS answers, and
a known-correct address while preserving the intended application hostname.

## Fault 4: transport succeeds, the application says no

```bash
sudo ip netns exec hdw-c curl --noproxy '*' -i --max-time 5 http://10.10.2.2:8000/missing
```

Expect HTTP 404. Plain curl normally exits successfully for an HTTP error
response because it completed the transfer. `curl --fail` changes that exit-code
policy. Inspecting only a shell exit code without knowing the tool's semantics
can misclassify the problem.

The repair here is to request an existing path or create the intended resource
in the server's scratch directory. Adding a route cannot turn a missing file
into an existing one.

## A troubleshooting ladder

Use the ladder to choose the next discriminating test, not as a demand to run
every command for every incident.

| Question | Evidence | What it does not establish |
|---|---|---|
| What name/address did this client use? | Resolver output, curl verbose output | Reachability |
| Which route would it choose? | `ip route get DESTINATION` | Successful packet delivery |
| Can it resolve its next hop? | `ip neigh`, ARP/ND capture | End-to-end transport |
| Do packets cross the router? | Captures on both interfaces | Application success |
| Does the return route exist? | Destination-side route lookup | Permission through filters |
| Is the expected socket listening? | `ss -lntp` in the correct namespace | Correct TLS or HTTP behavior |
| Is policy matching this traffic? | nftables rules and counters | Intent of an unseen upstream network |
| Does TLS authenticate the requested name? | Client handshake result | Honesty or correctness of the service |
| What does the application report? | HTTP status and server logs | Health of unrelated requests |

A packet seen at a capture point establishes presence there. Absence is weaker
evidence until you verify the interface, namespace, filter, and capture timing.
Preserve that distinction in your notebook.

## Tell the entire request story

Using your own diagram, explain a new HTTP/1.1-over-TLS connection to a remote
hostname. Include these events, and mark which can be skipped because of caching
or connection reuse:

1. The machine has addresses, resolver information, and usable routes, whether
   from configuration, DHCP, or an IPv6 configuration mechanism.
2. Name lookup returns candidate addresses; the client chooses an address and
   transport appropriate to the request.
3. Route selection picks an output and next hop; ARP or ND supplies local delivery
   information when needed.
4. TCP establishes endpoint state. Each routed hop uses a new local envelope,
   and the response must find a return path.
5. TLS authenticates the server according to the client's trust rules and
   establishes protected communication.
6. HTTP identifies the requested resource; the application returns a result.
7. Queues, losses, congestion control, filtering, and perhaps translation affect
   the traffic without being the application protocol itself.

Then explain what changes for HTTP/3: QUIC over UDP replaces this TCP transport
sequence and integrates TLS-based security into its handshake. The need for
addressing, routing, local delivery, and application meaning remains.

**Completion criterion:** you can diagnose all four faults, cite the observation
supporting each diagnosis, and connect each mechanism to the problem that motivated
it. This is the intuition the course is designed to build.

Stop the server, remove its scratch directory, then clean up:

```bash
sudo bash labs/network.sh down
sudo ip netns list
```

The `hdw-` lab namespaces should be gone. Existing unrelated namespaces, if any,
should remain.

## Where to go next

Pick an extension based on a question your experiments raised:

- Add a fourth namespace and a Linux bridge. Observe MAC learning with
  `bridge fdb show`, and compare one switched LAN with two routed subnets.
- Add a second router and make an asymmetric return path. Draw both directions
  before adding any routes.
- Implement request IDs and duplicate suppression in the UDP toy. Distinguish
  transport delivery from application execution.
- Compare IPv6 automatic configuration with our manual routes, keeping router
  advertisements and address allocation as distinct observations.
- Follow the repository's [SSH identity series](../ssh/README.md) to examine
  how another application protocol establishes who is on the other end.
