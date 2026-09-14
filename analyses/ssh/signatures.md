# What signing and verification actually do

[Previous: host identity](host-identity.md) · [Series index](README.md) · [Next: fingerprints](fingerprints.md)

Signing calculates a piece of data that someone with the public key can check,
while creating valid signatures requires the private key. These are separate
algorithms with different inputs:

```text
sign(private_key, message_bytes) → signature_bytes
verify(public_key, message_bytes, signature_bytes) → valid or invalid
```

For SSH host authentication, the message being signed is the exchange hash.
The client verifies against the hash it calculated for this exchange, not an
arbitrary message selected by the server.
[SSH transport specification, section 8](https://www.rfc-editor.org/rfc/rfc4253.html#section-8)

## A signature is separate from the message

The signature is not the message encrypted with the private key. Ed25519 is a
signature algorithm, not an encryption algorithm. It produces a 64-byte signature
checked using a 32-byte public key; SSH wraps these in its protocol encoding.
[Ed25519 in SSH, sections 3–6](https://www.rfc-editor.org/rfc/rfc8709.html#section-3)

Anyone with the message, signature, and public key can perform verification.
There is no verifier password or private key required for this check.

For example, suppose a signature verifies for the exact bytes of:

```text
Create one disposable VM.
```

Changing the message to `Create ten disposable VMs.` makes that signature fail
verification against the same public key. A signature for this sentence also
says nothing about whether anyone actually created a VM. The statement's content
and the evidence that a key signed it are different things.

## The mathematics behind the check

Here is the core relationship in Ed25519, simplified for explanation. Let `B`
be a fixed elliptic-curve point, `a` a secret number derived from the private key,
and `A = aB` the public point. Multiplication here is repeated curve-point
addition, not ordinary multiplication of two numbers.

For message `M`, the signer derives a secret per-message value `r`, computes
`R = rB`, hashes encoded `R`, `A`, and `M` to obtain `k`, then calculates:

```text
S = r + k·a   (modulo the subgroup order)
signature = encoded (R, S)
```

The verifier recomputes `k` and checks a curve equation of the form:

```text
SB = R + kA
```

It works because `(r + k·a)B = rB + k(aB)`. The public point lets the verifier
check this relation without learning `a`. Recovering `a` from `A` is assumed
computationally infeasible. The challenge `k` also depends on `R` and the message,
preventing freely choosing the equation's parts independently.

Actual Ed25519 includes SHA-512 hashing, deterministic derivation of `r`, encoding
and range checks, and precise cofactor rules. This sketch is not an
implementation recipe. [Ed25519 specification, sections 5.1.5–5.1.7](https://www.rfc-editor.org/rfc/rfc8032.html#section-5.1.5)

## What a valid signature proves

The direct observation is narrow: these message bytes and this signature satisfy
the verification algorithm under this public key. The security inference is that
someone with access to the private key produced it, assuming forgery is
infeasible and the implementation is sound.

| Question | Does a valid signature answer it? |
|---|---|
| Does this signature verify for these bytes under this key? | Yes |
| Does that establish the key owner's name or organization? | No; that association needs separate evidence |
| Is the signed statement true? | No |
| Is the statement recent? | Only if the signed protocol data establishes freshness |
| Did the signer authorize every possible use of the signature? | No; the protocol must define what the signed data means |

A static signed document can be copied and verified years later. SSH gets
freshness from the connection-specific exchange inputs, not from a magical
timestamp property of signatures.

The earlier phrase “the server holds the private key” is convenient shorthand.
More precisely, the exchange demonstrates access to signing with that key. A
server might ask a hardware security device to sign without holding extractable
private-key bytes in its own memory.
