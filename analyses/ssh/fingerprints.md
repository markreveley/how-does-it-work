# What a fingerprint preserves and loses

[Previous: signatures](signatures.md) · [Series index](README.md)

A public key is used to verify signatures. A fingerprint is an identifier used
to compare public keys. You cannot substitute the fingerprint for the public key
in signature verification.

## Bytes can be printed without hashing them

Keys are represented as bytes. A public-key file can render those bytes as text,
for example in this schematic form:

```text
ssh-ed25519 BASE64_ENCODED_PUBLIC_KEY_BLOB optional-comment
```

Base64 is a reversible encoding: it represents binary data using printable
characters. It does not encrypt or discard the encoded bytes, and generally
makes them longer. “Readable” here means printable and copyable, not meaningful
English. [Base64 specification](https://www.rfc-editor.org/rfc/rfc4648.html#section-4)

## How OpenSSH makes the fingerprint

For an ordinary Ed25519 key displayed with a SHA-256 fingerprint:

```text
SSH public-key blob
    → SHA-256
32-byte digest
    → Base64 without trailing padding
43 printable characters
    → prepend algorithm label
SHA256:...
```

OpenSSH hashes the serialized public-key blob, not the literal text line or its
comment. Its `sshkey_fingerprint_raw` function serializes the public key and
computes the digest; `fingerprint_b64` encodes that digest and removes trailing
`=` padding. [OpenSSH Portable V_10_0_P1, sshkey.c](https://github.com/openssh/openssh-portable/blob/V_10_0_P1/sshkey.c)

The SSH blob includes the algorithm name and length-prefixed public-key bytes.
The raw Ed25519 public key itself is already 32 bytes—the same length as a
SHA-256 digest. Thus “fingerprints just shorten keys” is incomplete: the
fingerprint provides a consistent comparison format across key types and sizes,
and hashes the SSH representation. [SSH Ed25519 public-key format](https://www.rfc-editor.org/rfc/rfc8709.html#section-4)

## Hashing is not lossless compression

SHA-256 maps variable-length inputs to a fixed 256-bit result. There are only
`2^256` possible results, but more possible input byte strings. Different inputs
must therefore sometimes map to the same result: a **collision**.

Hashing is not a reversible representation of its input. The full input
participating in the calculation does not mean the output preserves all its
information. [NIST definition of a hash function](https://csrc.nist.gov/glossary/term/hash_function)

| Operation | Can you recover the original input? | Purpose here |
|---|---|---|
| Encode a public-key blob in Base64 | Yes, by decoding | Store or copy the public key as text |
| Hash that blob with SHA-256 | No general inverse | Produce a fixed-size comparison identifier |
| Encode the digest in Base64 | Yes, recover the digest only | Display the fingerprint |

Decoding the fingerprint gets you the digest, not the public key. The reversible
display step cannot undo the earlier hashing step.

## How can comparison work if collisions exist?

Collision resistance means finding different inputs with the same digest is
computationally infeasible. It does not mean collisions are mathematically
impossible. Fingerprint comparison relies on that practical difficulty, not on a
claim that every possible key has a globally unique digest.
[NIST definition of collision resistance](https://csrc.nist.gov/glossary/term/collision_resistance)

A fingerprint obtained from an impostor can faithfully identify the impostor's
key. Hashing adds no evidence about ownership. The value of comparing it depends
on having a trusted expected fingerprint, as described in
[the host-identity article](host-identity.md).

## Inspect an existing public key

If you already have a public-key file, OpenSSH can display its fingerprint:

```bash
ssh-keygen -lf /path/to/public-key.pub -E sha256
```

Replace the path with an actual public-key file. Here `-l` requests a fingerprint,
`-f` selects the file, and `-E sha256` selects the hash. This reads the file; it
does not create a key or contact a server. [ssh-keygen manual](https://man.openbsd.org/ssh-keygen)

Prediction: changing only the optional comment leaves the fingerprint unchanged.
Replacing the public key changes the fingerprint, apart from an infeasible
collision. Neither observation tells you who owns the key.
