# 1. From circuits to packets

[Course index](README.md) · [Next: one link](02-links.md)

## The problem: computers speak in bursts

Imagine two universities sharing an expensive long-distance connection. One
computer sends a command, waits while the other computes, then receives a large
answer. Reserving the connection throughout the silence wastes capacity. Reserving
too little makes the answer slow.

Traditional circuit switching allocates a communication path and capacity for
the duration of a call. A circuit need not be a separate physical wire; it can be
a reserved slice of a shared facility. That predictability suits a continuous
conversation. Interactive computer traffic presents a different workload.

During the 1960s, researchers including Paul Baran at RAND and Donald Davies at
NPL explored packet switching. ARPANET connected its first four hosts in 1969.
This history involved resource sharing, communication research, and several
independent lines of work; reducing it to one invention for surviving nuclear
war loses the important distinctions. The participant-written
[Internet history](https://www.internetsociety.org/internet/history-internet/brief-history-internet/)
describes these parallel developments.

The useful intuition is economic: **share capacity when there is work to do**.
Cut a long message into bounded pieces, attach delivery information, and let
pieces from different conversations take turns on a link.

```text
Messages:      AAAAAAAAAAAA     BBBB     CC
Shared link:   AAAA BBBB AAAA CC AAAA
               time moves →
```

The diagram is an invented scheduling example, not a claim that routers always
use that order. A **protocol** is a set of rules peers agree to: how to encode a
piece, identify its recipient, and react when something goes wrong. A **packet**
is a bounded unit sent according to such rules. Later we distinguish Ethernet
frames, IP packets, TCP segments, and application messages.

## The cost: queues and uncertain delivery

If two packets arrive for an output that can transmit only one, the other waits
in a queue. If arrivals keep exceeding departures, the queue fills. A real device
has finite memory and eventually discards something.

That gives us four different quantities:

| Quantity | Question it answers |
|---|---|
| Link capacity, bits/second | How quickly can bits be serialized onto this link? |
| Throughput, bits/second | How much data actually arrives per unit of time? |
| Latency, seconds | How long does one operation or trip take? |
| Loss | Which transmitted units fail to arrive? |

**Goodput** counts useful application data, excluding headers and retransmitted
data. A speed test, file transfer, and packet capture may report different rates
because they count different things.

For one link, separate serialization time from propagation time. Putting 1,500
bytes on a 10 Mbit/s link takes `1500 × 8 / 10,000,000 = 0.0012` seconds, or
1.2 ms. The first bit still has to travel through the medium. A faster interface
reduces serialization time; it does not abolish distance, queuing, or computation.

Packets also introduce overhead. Sending very small pieces improves opportunities
to interleave work, but spends a larger fraction of the link on headers. Very
large pieces hold an output busy longer. There is no universally ideal size.

## Exercise: a queue you can calculate

Predict when a short interactive message finishes if it arrives behind a large
transfer. Then run this deterministic simulation; it sends no network traffic.

```bash
python3 - <<'PY'
rate = 1_000_000  # bits per second
for label, jobs in [
    ("one large unit", [("bulk", 100_000), ("interactive", 100)]),
    ("interleaved pieces", [("bulk", 1000), ("interactive", 100)]
     + [("bulk", 1000)] * 99),
]:
    elapsed = 0.0
    for name, size in jobs:
        elapsed += size * 8 / rate
        if name == "interactive":
            print(f"{label}: interactive completes at {elapsed * 1000:.1f} ms")
    print(f"  all work completes at {elapsed * 1000:.1f} ms")
PY
```

Expected: interactive completion changes from **800.8 ms** to **8.8 ms**; total
completion remains **800.8 ms** in both cases. We deliberately ignored headers,
propagation, and losses. Packetization makes interleaving possible; a scheduler
still has to choose it. Putting all 100 bulk pieces ahead of the interactive
piece would reproduce the long wait.

Change the rate to 10 Mbit/s. Then add 40 bytes of overhead per unit. Explain why
the second schedule can improve responsiveness while using more total capacity.
This exercise creates no files or servers, so no cleanup is needed.

## Checkpoint

**Would infinitely large buffers fix congestion?** They could postpone drops,
but sustained excess arrivals would produce an ever-growing wait. Delivery after
an unusably long delay is not a satisfactory interactive service.

**Does packet switching require every packet to take a different route?** No.
Many packets in a conversation follow the same route. The important distinction
is that the network need not reserve a dedicated end-to-end circuit for them.

We now have pieces to send. We still need to decide who may transmit on a shared
medium and how a receiver knows which pieces belong to it.
