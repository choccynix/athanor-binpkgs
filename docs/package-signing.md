# ◈ Package index signing

The `Packages` index is published to both this repo's GitHub Releases and
mirrored to choccynix.github.io, rather than relying on Gentoo's own
signed mirror infrastructure — a detached GPG signature is how consumers
verify it wasn't tampered with in transit.

## One-time maintainer setup

1. Generate (or reuse) a dedicated signing key — don't reuse a personal
   key that has other trust attached to it:

   ```
   gpg --batch --gen-key <<'EOF'
   %no-protection
   Key-Type: eddsa
   Key-Curve: ed25519
   Name-Real: AthanorOS binpkgs
   Name-Email: ci@athanoros.invalid
   Expire-Date: 2y
   EOF
   ```

2. Export the public key and commit it into this repo's root as
   `athanor-binpkgs.pub.asc` — the `merge-and-publish` job copies it into
   the choccynix.github.io mirror automatically if present:

   ```
   gpg --armor --export ci@athanoros.invalid > athanor-binpkgs.pub.asc
   ```

3. Export the private key material and store it as repo secrets
   (`GPG_SIGNING_KEY_ID` for the key ID, plus whatever the workflow needs
   to import the secret key itself at runtime — don't commit private key
   material to the repo, even a private one).

## What actually gets signed

Just the `Packages` index file itself — every entry's checksum lives
inside the index, so a valid signature on the index transitively
guarantees the integrity of every package it references, as long as
Portage is configured to check those checksums (default behavior).

## Rotating the key

Run the `Re-publish Packages index` workflow manually after updating the
`GPG_SIGNING_KEY_ID`/`GPG_PASSPHRASE` secrets — it re-signs the currently
published index without needing a full package rebuild.
