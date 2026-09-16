# Networking: the problems that shaped the protocols

Networking becomes easier to understand when each mechanism answers a problem:
Why divide data into packets? Why have both IP and MAC addresses? Why does TCP
need acknowledgments if Ethernet already checks for errors? Why does a working
ping tell us so little about a broken website?

This course follows the decisions behind those mechanisms, then recreates them
on Linux. The history provides context, not a claim that every design was
inevitable. Different networks made different choices, and several developments
overlapped. We follow dependencies rather than a strict year-by-year chronology.

## Audience and route

Assumed background: you can open a terminal, change directories, and run a
command. No networking knowledge is required. Short Python programs are provided;
you do not need to write Python to begin. Budget roughly 12–18 hours including
experiments, spread across several sessions. The chapters are ordinary Markdown;
diagrams remain readable without a special renderer.

| Part | Chapter | What you should be able to explain afterward |
|---|---|---|
| Universal | [1. From circuits to packets](01-packets.md) | Why sharing creates both efficiency and queues |
| Universal | [2. Delivering on one link](02-links.md) | What a frame, MAC address, switch, and ARP actually do |
| Universal | [3. Joining unlike networks](03-internetworking.md) | Prefixes, routes, next hops, ICMP, and the purpose of IP |
| Universal | [4. Conversations over unreliable delivery](04-transport.md) | Ports, UDP, TCP, framing, flow control, and congestion |
| Universal | [5. From names to applications](05-names-and-applications.md) | DNS, DHCP, HTTP, TLS, and where each can fail |
| Universal | [6. Growing beyond the original assumptions](06-growth.md) | CIDR, routing policy, NAT, IPv6, and QUIC |
| Linux | [7. Meet the Linux network stack](07-linux.md) | How interfaces, routes, sockets, and configuration fit together |
| Linux | [8. Build a small routed network](08-router-lab.md) | Trace one packet across two links and diagnose a missing route |
| Linux | [9. Make the network misbehave](09-loss-and-mtu.md) | Measure latency, loss, throughput, and MTU failures |
| Linux | [10. Policy, translation, and IPv6](10-policy-and-ipv6.md) | Separate routing, filtering, and NAT; repeat the route in IPv6 |
| Practice | [11. A debugging capstone](11-capstone.md) | Diagnose failures from evidence and explain the whole request |

The course includes four mini-projects: a tiny application protocol, a local
named website, a software router, and a network incident notebook. There are
smaller command-line exercises in every chapter. Use this rhythm:

1. Predict what will happen before running the command.
2. Observe the actual result, including errors.
3. Explain which mechanism produced it.
4. Change one condition and try again.

Checkpoints include answers after the questions. Attempt your own explanation
first. Copying a working command is a starting point; predicting a broken one
is a stronger test of understanding.

## Exercise environments

Chapters 1–6 explain protocols independently of operating systems. Their core
exercises use Python 3 and `curl` on macOS or Linux. Optional DNS exercises use
`dig`. On Windows, use a Linux shell such as WSL for the command examples; the
concepts do not depend on it. Network access is needed only for explicitly marked
public DNS/HTTPS observations and installing packages.

Chapters 7–11 target a disposable Ubuntu/Debian Linux VM with `sudo`, Bash,
network namespaces, and the packages listed in chapter 7. A normal unprivileged
container does not provide the permissions needed for those chapters. Run the
commands inside the VM, not the macOS terminal hosting it.

The Linux lab builds three isolated network namespaces named `hdw-c`, `hdw-r`,
and `hdw-s`. They share the VM's kernel and filesystem but have separate network
stacks. Their links have no connection to the VM's external network. All route,
firewall, and impairment changes in the exercises target these namespaces.
The lab requires root because it creates interfaces and changes network state.
An optional Docker setup and the tested environment are documented in
[lab files and verification](labs/README.md).

From the repository root, enter the tutorial directory:

```bash
cd analyses/networking
python3 --version
curl --version
```

Run all relative paths below from this directory, in every terminal. A code block
headed **Terminal A** stays running while you use **Terminal B**. Stop foreground
servers and captures with **Ctrl-C**. `127.0.0.1` means this machine's IPv4
loopback interface; `::1` is its IPv6 counterpart. Ports 8000 and 9000 are local
exercise choices, not required protocol ports.

If a command says `Address already in use`, stop the server from the preceding
exercise. If `sudo` is unavailable or `ip netns add` returns `Operation not
permitted`, use a VM with administrative access before continuing the Linux labs.

## Historical and technical grounding

Written September 15, 2026. Historical RFCs are identified as such; their dates
are evidence of publication, not always the date an idea was invented or widely
deployed. Each chapter links primary standards, project manuals, or research by
the people involved. The Internet Society's participant-written
[history of the Internet](https://www.internetsociety.org/internet/history-internet/brief-history-internet/)
provides background for the early chronology.

This is a course in mechanisms, not an exhaustive networking certification guide.
Radio engineering, full BGP configuration, cryptographic mathematics, and
production network administration deserve their own courses. You will still
learn where those subjects connect to the packet's journey.

Start with [the cost of reserving a wire](01-packets.md).
