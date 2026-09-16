# 4. Conversations over unreliable delivery

[Previous: IP](03-internetworking.md) · [Course index](README.md) · [Next: names and applications](05-names-and-applications.md)

## The problem: a packet reaches a machine, but which program?

A machine can browse the web while receiving mail and serving a database.
Transport protocols add **ports**, numbers that help the operating system deliver
incoming data to the right socket. A socket is an application-facing communication
endpoint, not a physical connector. An ordinary TCP connection is distinguished
by its source and destination IP addresses and ports; the transport protocol is
also part of a flow's identity. TCP port 9000 and UDP port 9000 are separate spaces.

The split between IP delivery and transport behavior let applications make
different choices. UDP's short 1980 specification provides datagrams and ports
without promising delivery, order, or duplicate suppression. A receiver gets a
message boundary, but the application must handle missing messages itself.
[RFC 768](https://www.rfc-editor.org/rfc/rfc768.html)

TCP's 1981 specification instead described a reliable, ordered byte stream.
Sequence numbers identify byte positions; acknowledgments report progress;
retransmission repairs suspected loss; and duplicates can be recognized. A
connection establishes shared transport state at the endpoints. The familiar
SYN, SYN-ACK, ACK exchange synchronizes that state and sequence spaces; it does
not reserve a circuit through the intervening routers.
[Historical RFC 793](https://www.rfc-editor.org/rfc/rfc793.html)

The current consolidated base TCP specification is RFC 9293. TCP provides a
stream **or reports failure**; it cannot guarantee success across an indefinite
outage. A successful write commonly means the local stack accepted bytes, not
that the peer application processed them. Even an acknowledgment from the peer's
TCP stack is not a database commit receipt. TCP does not provide encryption or
preserve the boundaries of application writes.
[RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html)

```text
application writes:     [one\n][two\n]
possible application reads: [on][e\nt][wo\n]
logical records:        [one] [two]  ← reconstructed using the newline rule
```

This diagram concerns application reads, not a prediction of packet boundaries.
The operating system can split or combine delivery to match buffering and timing.
An application protocol needs its own **framing** rule: fixed sizes, a length
prefix, delimiters, or another unambiguous grammar.

## Mini-project 1: invent a tiny application protocol

Our protocol has one rule: send a newline-terminated ASCII record and receive
the uppercase record plus a newline. The supplied
[transport program](labs/transport.py) uses Python's standard socket API. Read
`tcp_server` and find `bind`, `listen`, `accept`, `recv`, and `sendall`. Those are
library calls; TCP itself is implemented by the operating system here.
[Python socket reference](https://docs.python.org/3/library/socket.html)

**Terminal A:**

```bash
python3 labs/transport.py tcp-server
```

**Terminal B:**

```bash
python3 labs/transport.py tcp-client
```

Expect replies `b'ONE\n'` and `b'TWO\n'`. The server deliberately requests at most
three bytes per `recv`, so its printed chunks cannot align with the two four-byte
records. Exact chunk divisions can vary. It accumulates bytes until a newline
appears, then interprets a complete record. This forces a framing issue to become
visible; it does not pretend that tiny reads are an efficient production design.

The client calls `shutdown(SHUT_WR)` after sending. This closes its sending
direction while it continues receiving replies. Reading until end-of-stream and
closing immediately after writing are different actions.

**Your change:** replace `b"one\ntwo\n"` in a copy of the client with
`b"one\ntwo"`. Predict the result. The server can reply to the complete `one`
record, but the final `two` is incomplete at EOF. Record an explicit rule for
that situation before changing the implementation. Restore the original example
when finished, and stop the server with Ctrl-C.

**Success criterion:** explain why “one send equals one receive” is not a valid
protocol, and show both complete and incomplete records in your observations.

## Exercise: make a missing reply visible

**Terminal A:**

```bash
python3 labs/transport.py udp-server --drop-every 3
```

**Terminal B:**

```bash
python3 labs/transport.py udp-client --count 6
```

From a freshly started server, expect echoes for 1, 2, 4, and 5, and timeouts for
3 and 6. Here the **application deliberately discards requests**; we are modeling
a missing reply, not measuring real network loss. Chapter 9 introduces loss in
the Linux network path. Stop the UDP server afterward with Ctrl-C.

A timeout is uncertainty: the request may have been lost, the reply may have
been lost, or the peer may be slow. Adding retries to a “charge my account”
request requires an application request ID and duplicate-handling policy. A
transport repair mechanism alone does not define business-level exactly-once
execution. For this echo toy, print the sequence IDs rather than blindly assuming
that the next reply belongs to the latest request if you extend it to delayed
or reordered traffic.

UDP is useful when the application wants message semantics or implements its
own recovery strategy. It is not intrinsically “the fast protocol.” The workload,
implementation, and congestion behavior matter.

## Two different reasons to slow down

**Flow control** protects a receiver. If an application stops reading, the
receiver advertises less available buffer space. **Congestion control** protects
the network path. A fast sender and fast receiver can still overload a slow
router output between them.

In 1986, congestion collapse made this distinction painfully practical: sending
and retransmitting more could produce less useful delivery. Van Jacobson's 1988
paper describes algorithms responding to that problem. Reliability without a
stable sending policy was insufficient.
[Congestion Avoidance and Control](https://ee.lbl.gov/www/papers/congavoid.pdf)

Classic TCP congestion control uses a congestion window, grows it as delivery
succeeds, and responds to congestion signals. “Slow start” grows quickly from a
small initial amount of outstanding data; the name does not mean constant slow
transmission. Actual TCP algorithms vary, so treat this as a family of feedback
strategies rather than one permanent formula.
[RFC 5681](https://www.rfc-editor.org/rfc/rfc5681.html)

## Checkpoint

**Why isn't Ethernet error detection enough?** The path can contain many links,
queues, and failures outside the first link. Local correctness does not establish
end-to-end delivery, and end-to-end delivery does not establish application success.

**What does a port identify?** A transport endpoint within an addressing context,
not a universally fixed program. Port 443 commonly serves HTTPS, but any chosen
number still requires a listening service and an agreed application protocol.

We can now talk to a process. The next problems are discovering its address and
agreeing what the exchanged bytes mean.
