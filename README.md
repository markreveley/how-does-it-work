# How Does It Work?

Implementation-first notes on technologies worth understanding.

Implementation analyses are pinned to a source revision; protocol explainers
identify their standards and implementation references. Each separates claims
from the mechanisms that support them. The goal is not to reproduce product
documentation, but to explain the mechanism, identify the important design
choices, and make the risks and adoption tradeoffs legible.

## Analyses

| Technology | Category | Analysis |
|---|---|---|
| Prime Agent | Long-running coding-agent harness | [Analysis index](analyses/prime-agent/README.md) |
| SSH | Host identity, digital signatures, and fingerprints | [Explanation series](analyses/ssh/README.md) |
| Networking | History, protocols, and hands-on Linux networking | [Tutorial course](analyses/networking/README.md) |

## Method

Analyses generally cover:

- the shortest accurate mental model;
- architecture and control flow;
- persistence and trust boundaries;
- what is genuinely novel versus product framing;
- implementation quality and operational risks; and
- when the technology is, and is not, a good fit.
