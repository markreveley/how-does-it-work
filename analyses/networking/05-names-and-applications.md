# 5. From names to applications

[Previous: transport](04-transport.md) · [Course index](README.md) · [Next: growth](06-growth.md)

## The problem: a shared list stops scaling

Early Internet hosts used a centrally maintained host table. As hosts and
administrative groups multiplied, distributing updates and coordinating names
became a bottleneck. The DNS design published in 1983 replaced that model with
a hierarchical naming system and distributed responsibility. The 1987 DNS
documents refined the design. This was an administrative scaling decision as
well as a lookup algorithm. [Historical RFC 883](https://www.rfc-editor.org/rfc/rfc883.html)

DNS separates **authoritative servers**, which answer for zones they serve,
from **recursive resolvers**, which pursue answers on a client's behalf and
cache them. Delegation connects the hierarchy: root, top-level domain, and
further zones. Cached records have TTLs that bound ordinary reuse; changing an
authoritative answer does not instantly replace every cached copy.
[RFC 1034](https://www.rfc-editor.org/rfc/rfc1034.html)

```text
application → local resolver interface → recursive resolver
                                         ├─ root referral
                                         ├─ top-level-domain referral
                                         └─ authoritative answer
              ← answer, often from cache ←
```

The diagram describes a possible cache miss, not work repeated for every query.
An `A` record supplies an IPv4 address; `AAAA` supplies an IPv6 address. Other
types include aliases (`CNAME`), mail exchangers (`MX`), and name servers (`NS`).
DNS queries can use UDP or TCP; “DNS is always UDP” is an unsafe simplification.
The original DNS message and transport rules are specified in
[RFC 1035](https://www.rfc-editor.org/rfc/rfc1035.html).

A name is neither a route nor a promise that a service is alive. One name can
have several addresses; one address can host several named services. Applications
may resolve through files, caches, a local daemon, or other configured mechanisms.
`dig` and an application's normal resolver path therefore need not see identical
behavior.

## Exercise: compare name resolution with direct addressing

The following observations need Internet access and a working resolver:

```bash
python3 - <<'PY'
import socket
answers = socket.getaddrinfo("example.com", 443, type=socket.SOCK_STREAM)
for family, _, _, _, address in sorted(set(answers)):
    print(socket.AddressFamily(family).name, address)
PY
```

If `dig` is installed:

```bash
dig example.com A
dig example.com AAAA
dig example.com NS
```

Look at the status, answer type, TTL, and responding DNS server. Exact addresses
and TTLs vary; do not copy a particular public IP into later exercises. `NXDOMAIN`
means the queried name does not exist according to that response. `SERVFAIL`
means the resolver could not complete resolution; it is not the same assertion.
A timeout provides less information still.

Optional: `dig +trace example.com` follows delegations using direct queries. It
may fail where outbound DNS is restricted even if ordinary recursive resolution
works. Failure there does not prove the domain is broken. These are read-only
observations with no cleanup.

## Before DNS: how did the machine obtain configuration?

Manually assigning every new workstation an address and gateway creates another
coordination problem. DHCP leases IPv4 configuration to clients. A typical
initial exchange is Discover, Offer, Request, Acknowledge; it can supply an
address and options such as router and DNS server addresses. A lease belongs
to a configuration workflow, not a guarantee that the offered Internet service
will work. DHCP follows earlier bootstrap mechanisms and was standardized in
the 1990s. [RFC 2131](https://www.rfc-editor.org/rfc/rfc2131.html)

Our Linux labs assign addresses manually so you can see each required choice.
That does not imply real networks normally configure every endpoint by hand.

## Mini-project 2: host a named local website

Create a scratch directory, then run a server bound only to IPv4 loopback.
**Terminal A:**

```bash
site_dir=$(mktemp -d)
printf 'Hello from a local application.\n' > "$site_dir/index.html"
python3 -m http.server 8000 --bind 127.0.0.1 --directory "$site_dir"
```

**Terminal B:**

```bash
curl --noproxy '*' -v http://127.0.0.1:8000/
curl --noproxy '*' -v --resolve story.test:8000:127.0.0.1 http://story.test:8000/
```

Both should return your text. The second command supplies a per-command address
mapping; it does **not** create a DNS record or edit `/etc/hosts`. `.test` is
reserved for testing. Curl connects to loopback but sends `Host: story.test:8000`.
`--noproxy '*'` ensures a configured proxy does not reroute the exercise.
[curl manual](https://curl.se/docs/manpage.html),
[reserved test domains, RFC 2606](https://www.rfc-editor.org/rfc/rfc2606.html)

HTTP defines application messages, including request methods, target paths,
response status codes, headers, and body framing. HTTP/1.1 makes it possible to
see these in a text-oriented exchange; its Host field distinguishes names sharing
an address. Python's simple server does not implement separate websites per
Host value, so both requests serve the same file.
[HTTP/1.1, RFC 9112](https://www.rfc-editor.org/rfc/rfc9112.html)

Now speak HTTP without a dedicated HTTP client:

```bash
python3 - <<'PY'
import socket
with socket.create_connection(("127.0.0.1", 8000), timeout=3) as connection:
    connection.sendall(b"GET / HTTP/1.1\r\nHost: story.test:8000\r\nConnection: close\r\n\r\n")
    response = bytearray()
    while True:
        chunk = connection.recv(4096)
        if not chunk:
            break
        response.extend(chunk)
print(response.decode("utf-8", errors="replace"))
PY
```

The blank line terminates the request headers. `Connection: close` lets this
small demonstration read until EOF rather than implementing a full HTTP parser.
Do not infer that every HTTP response body normally ends by closing TCP.

**Your change:** request `/missing`. A 404 response proves that transport and
enough HTTP processing worked to return an application error. Stop the server
and repeat the original request: connection refusal occurs at a different stage.
Explain both observations in a short request timeline.

**Cleanup:** after Ctrl-C in Terminal A, run `rm -r -- "$site_dir"` there to
remove the scratch directory. The variable exists in Terminal A only.

## Why encryption arrived as another agreement

Getting bytes to an address does not establish who operates the peer or keep
intermediaries from reading them. TLS adds authenticated key establishment and
record protection. In typical HTTPS, the client checks a server certificate
against the requested name and its trust configuration. This establishes a
particular identity claim; it does not certify the site's honesty. TLS 1.3 was
specified in 2018. [RFC 8446](https://www.rfc-editor.org/rfc/rfc8446.html)

Optional public observation:

```bash
curl --noproxy '*' --http1.1 -v --connect-timeout 5 --max-time 15 https://example.com/ -o /dev/null
```

Find the phases: resolution, connection, TLS negotiation, and HTTP response.
Output details depend on curl's TLS library. Do not use `-k` to make a certificate
failure disappear; the identity check is part of what this experiment observes.
If direct egress is blocked on your network, record that limitation and keep the
local project as your reproducible result.

## Checkpoint

**Can DNS succeed while HTTPS fails?** Yes: the route, transport listener,
certificate check, or application can fail afterward.

**Does changing a hostname necessarily change the IP?** No. The local project
held the IP constant while changing the application-level Host value. For HTTPS,
the name also participates in TLS server selection and certificate verification.
