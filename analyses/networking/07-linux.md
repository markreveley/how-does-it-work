# 7. Meet the Linux network stack

[Previous: growth](06-growth.md) · [Course index](README.md) · [Next: build a router](08-router-lab.md)

## The transition: a protocol is not a command

IP and TCP define communication behavior. Linux implements that behavior in a
kernel, exposing sockets to applications and configuration interfaces to tools.
Running `ip route` queries or changes kernel routing state; it does not invent
a Linux-specific version of IP.

The socket API grew out of Unix networking and lets an application request
services without assembling every packet itself. Linux separates that application
interface from network administration. Tools such as `ip`, `ss`, and `tc` expose
different views and controls rather than one universal “network settings” object.
[Linux socket API](https://man7.org/linux/man-pages/man7/socket.7.html),
[iproute2's ip manual](https://man7.org/linux/man-pages/man8/ip.8.html)

```text
application process
    │ socket calls: connect, send, receive
Linux kernel: sockets → TCP/UDP → IP routing → neighbor lookup → device
    │
physical NIC, loopback, or virtual link

administration tools → kernel configuration/state
```

A network namespace supplies another set of interfaces, routes, sockets, and
network-related state inside the same kernel. A process uses the network stack
of its namespace. This makes a laptop capable of hosting our three-node lab
without three virtual machines. A network namespace alone does not isolate the
filesystem, process IDs, or all other machine resources.
[network_namespaces manual](https://man7.org/linux/man-pages/man7/network_namespaces.7.html)

## Prepare the VM

Use a disposable Ubuntu/Debian Linux VM with administrative access. Package
installation needs network access; the routed labs afterward work offline.

```bash
sudo apt-get update
sudo apt-get install -y python3 curl iproute2 iputils-ping iputils-tracepath \
  tcpdump dnsutils nftables conntrack iperf3 traceroute ethtool
```

If installation asks whether iperf3 should run as a daemon, choose **No**. We
start it explicitly only when needed. Run these checks inside Linux:

```bash
uname -r
ip -Version
python3 --version
nft --version
```

The lab uses longstanding Linux interfaces, but minimal kernels or restricted
containers may omit network namespaces, `netem`, or nftables support. Diagnose
an unsupported operation as an environment limitation rather than trying to
reconfigure a production host to fit the lesson.

## Exercise: inventory the real machine, read-only

```bash
ip -br link
ip -br address
ip -4 route show
ip -4 rule show
ip -4 neigh show
ss -lnt
cat /etc/resolv.conf
```

Read the output in this order:

1. **Links:** which devices exist and are administratively up?
2. **Addresses:** which addresses and prefixes belong to each interface?
3. **Routes:** where would a matching destination go?
4. **Rules:** which routing tables are consulted?
5. **Neighbors:** which local IP-to-link-address mappings are cached?
6. **Sockets:** which TCP listeners exist in this namespace?
7. **Resolver configuration:** where might name queries be sent?

`ss -lnt` means listening, numeric addresses, TCP. Add `-p` (and often `sudo`) to
identify processes. A listener on `127.0.0.1` accepts loopback traffic; a listener
on `0.0.0.0` requests all local IPv4 addresses in its namespace. Neither binding
bypasses a firewall. [ss manual](https://man7.org/linux/man-pages/man8/ss.8.html)

An IPv6 wildcard listener does not uniformly imply the same IPv4 behavior across
all systems and settings. Inspect the actual listener and test the desired family.

Record one interface, its prefix, a route, and a listener if present. An empty
socket or neighbor listing is fine. Never substitute a real interface name into
later lab mutation commands; those commands already name the isolated devices.

## Running state versus persistent configuration

An `ip address add` changes the running kernel state. A network manager may later
replace it, and it generally will not survive reboot on its own. Depending on
the distribution, NetworkManager, systemd-networkd, Netplan, or another system
may own persistent configuration. Read what is installed before assuming one
file is authoritative.

Likewise, `/etc/resolv.conf` can point to a local resolver stub. Where available,
`resolvectl status` shows systemd-resolved's upstream and per-link configuration;
`getent ahosts example.com` exercises the system's configured name lookup path.
`dig` directly tests DNS and bypasses some of that application lookup machinery.
[systemd-resolved manual](https://manpages.debian.org/trixie/systemd-resolved/systemd-resolved.service.8.en.html),
[getent manual](https://man7.org/linux/man-pages/man1/getent.1.html)

The isolated lab uses temporary kernel settings deliberately. Its reset operation
removes the namespaces and their state, making experimentation repeatable.

## A few devices that are software

| Device | Role |
|---|---|
| `lo` | Loopback inside this namespace |
| `veth` pair | Two linked virtual Ethernet interfaces; transmit on one, receive on the other |
| Bridge | A software Ethernet switch joining ports |
| TUN/TAP | Userspace packet interfaces: IP packets for TUN, Ethernet frames for TAP |

These are mechanisms used in larger systems such as container networking and
VPNs. Our lab uses two veth pairs; it needs no container orchestrator and no
bridge because the router joins two separate links directly.
[veth manual](https://man7.org/linux/man-pages/man4/veth.4.html),
[kernel TUN/TAP documentation](https://docs.kernel.org/networking/tuntap.html)

## Checkpoint

**Why can two namespaces both listen on port 8000?** Their socket and addressing
contexts are separate.

**If `ip route get` shows a route, has a packet reached the server?** No. It
shows the kernel's chosen route for that lookup, not successful neighbor
resolution, forwarding, replies, or application service.

Keep those distinctions in your notebook. We will intentionally create a case
where addresses and routes look sensible, but forwarding is disabled.
