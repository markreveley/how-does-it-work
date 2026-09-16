# Lab files and verification

[Course index](../README.md)

| File | Purpose |
|---|---|
| [transport.py](transport.py) | Chapter 4's TCP framing and UDP missing-reply experiments; Python standard library only |
| [network.sh](network.sh) | Creates or removes chapter 8's three-namespace topology |
| [Dockerfile](Dockerfile) | Optional Debian environment for reproducing the offline labs |

The main learning path uses a Linux VM. Read the chapter explanations before
running the helpers; `network.sh up` intentionally leaves IPv4 forwarding off.
All course-relative commands run from `analyses/networking`, not this `labs`
subdirectory.

## Optional Docker environment

If you already use Docker, build the supplied environment from the tutorial
directory:

```bash
docker build -t hdw-network-tutorial:local -f labs/Dockerfile .
docker run --rm -it --name hdw-network-course --network none \
  --cap-add NET_ADMIN --cap-add SYS_ADMIN \
  --security-opt apparmor=unconfined \
  --security-opt systempaths=unconfined \
  hdw-network-tutorial:local
```

These additional permissions are needed to create named network namespaces,
virtual devices, and writable namespace sysctls inside Docker. This is a trusted
local lab environment with administrative capabilities, not a sandbox for
untrusted code. It exposes no ports, mounts no host directories, and has no
external network after startup. Docker security policy may disallow these
options; the Linux VM remains the main course environment.

The shell starts in `/course` as root. The course's `sudo` commands still work.
For Terminal B or C, open another host terminal and run:

```bash
docker exec -it hdw-network-course bash
```

The public DNS/HTTPS exercises cannot run in this offline container. Do those
from your ordinary terminal. Stop lab processes, run
`bash labs/network.sh down`, and exit the initial container shell when finished.
Docker then removes the container. The reusable image remains; remove it with
`docker image rm hdw-network-tutorial:local` if you no longer want it.

## Verification record

The offline exercises were exercised on September 15, 2026 using Debian 12
userspace on a Linux `6.10.14-linuxkit` kernel, Python 3.11.2, iproute2 6.1.0,
and nftables 1.0.6. This was a Docker-hosted Linux test, not a separate Ubuntu VM
test. A temporary integration harness checked the following observable outcomes:

| Experiment | Verified outcome |
|---|---|
| Queue simulation and prefix arithmetic | The printed values match the chapter predictions |
| TCP toy | Two newline-framed replies despite three-byte maximum reads; half-close completes |
| UDP toy | Requests 3 and 6 time out when every third request is discarded |
| Local HTTP | Per-command name mapping and raw socket request return the local file |
| Forwarding | Local gateway works before forwarding; cross-subnet ping works after enabling it |
| Captures | ARP resolves the next hop; the IP destination persists and TTL decrements across the router |
| Return route | Removing it breaks the exchange; restoring it repairs the exchange |
| Delay/rate/loss | Added RTT, constrained throughput, and retransmissions become observable |
| MTU | Small probes work; oversized DF probe fails; fitting probe works |
| Firewall | ICMP passes while TCP is rejected; dropping produces a timeout; removing rules restores HTTP |
| NAT | SNAT permits replies without the server's default route and changes the logged source address |
| IPv6 | Addresses complete DAD, ND is captured, and routed ping/HTTP work without NAT |
| Capstone | Wrong listener, wrong gateway, wrong mapping, and HTTP 404 are distinguishable |
| Lifecycle | Existing namespace names are protected; cleanup stops leftover lab processes and preserves unrelated namespaces |

The enclosing namespace's interfaces, routes, forwarding setting, and nftables
rules matched their pre-lab state afterward. ShellCheck passed for `network.sh`;
the Markdown's Bash blocks passed syntax checks, embedded Python compiled, and
local document links resolved.

Timing results are illustrative rather than benchmark targets. One test run's
five-second transfers measured about 9.1 Mbit/s without deliberate loss and
3.5 Mbit/s with 1% configured loss; another run produced different numbers.
Use the chapter's longer interactive runs and record your own observations.
Public DNS answers and HTTPS behavior depend on your resolver and network and
were not part of this offline verification.
