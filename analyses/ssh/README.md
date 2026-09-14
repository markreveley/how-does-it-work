# SSH: keys, signatures, and trust

Why does a first SSH connection ask whether you trust a key? What does signing
prove, and how can a public key check a signature without letting everyone forge
one? Is a fingerprint a compressed public key?

This series follows those questions from the terminal prompt into the mechanism.
It assumes no cryptography background.

1. [How SSH establishes the server's identity](host-identity.md): the first
   connection, proof of key possession, and the separate decision to trust a key.
2. [What signing and verification actually do](signatures.md): the inputs,
   mathematical check, and limits of what a valid signature establishes.
3. [What a fingerprint preserves and loses](fingerprints.md): public-key bytes,
   SHA-256, Base64, and why hashing is not lossless compression.

Written September 13, 2026. Scope: ordinary SSH connections using an Ed25519
host key and OpenSSH's SHA-256 fingerprint display. Protocol references are
RFCs 4253, 8032, and 8709. Fingerprint implementation references are pinned to
OpenSSH Portable release tag `V_10_0_P1`; this is a reading baseline, not a claim
about the installed client or server version. Each article links its sources.

Examples use a documentation-only IP address. No live server, account, password,
or private key is needed to read the series. This is an explanation of the
connection mechanism, not a completed server deployment or security audit.
