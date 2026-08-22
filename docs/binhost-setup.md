# ◈ Consuming the AthanorOS binhost

## What you're pointing at

The binhost is configured via `/etc/portage/binrepos.conf/` — the current,
documented mechanism for remote binary package repositories (it replaces
the older `PORTAGE_BINHOST` make.conf variable).

`sync-uri` points at `https://choccynix.github.io` — a `<username>.github.io`
repo, which GitHub serves via Pages automatically from its root with no
settings toggle needed (unlike a regular repo's `gh-pages` branch, which
has to be manually enabled). That repo hosts an auto-updated mirror of the
`Packages` index, pushed there by this repo's own CI after every build.
The actual `.gpkg.tar` package blobs still live on **this** repo's GitHub
Releases — Portage fetches the index from the stable Pages URL and the
actual packages from wherever their individual entries point.

## Setup

1. Create `/etc/portage/binrepos.conf/` (it's a directory) and copy
   `templates/binrepos.conf.template` into it as e.g. `athanor.conf`.
   Note the `verify-signature = false` in that template — Portage
   ≥3.0.74 defaults this to `true` expecting its own gemato-based
   signature scheme, which isn't what this repo publishes (see step 4
   below for the actual signature check this repo uses instead).
2. Add to `/etc/portage/make.conf` — copy
   `templates/make.conf.binhost.template` in, or append if you already
   have entries there.
3. Copy `templates/package.use.template` to
   `/etc/portage/package.use/athanor-binpkgs`, matching flags against
   whatever's currently in upstream `packages*.list`.
4. If any packages track `~arch` (several in `packages.kde-qt.list` and
   everything in the `xlibre` overlay do), do the same with
   `templates/package.accept_keywords.template`.
5. Import this repo's own signing key if you want the `binpkg-signing`
   FEATURES check in make.conf to actually verify anything:

   ```
   curl -fsSL https://choccynix.github.io/athanor-binpkgs.pub.asc \
     -o /etc/portage/gpg/athanor-binpkgs.pub.asc
   ```

6. Sync and try installing something known to be in one of the
   `packages*.list` files:

   ```
   emerge --sync
   emerge --getbinpkg=y --usepkg=y gui-wm/sway
   ```

   Portage logs will say `[binary]` next to the package name if it pulled
   the prebuilt version instead of compiling.

## Also want the ebuild overlay?

`choccynix.github.io` is a valid Gentoo ebuild overlay too, separate from
the binhost concern above (empty for now, but structured correctly for
when it isn't). Copy that repo's own `templates/repos.conf.template` into
`/etc/portage/repos.conf/` if/when you want it.

## Xorg vs XLibre

These two are alternatives, not both-at-once — installing both on the same
system causes real file collisions (XLibre's own docs are explicit about
this). Pick one:

```
emerge --getbinpkg=y --usepkg=y x11-base/xorg-server
```

or

```
emerge --getbinpkg=y --usepkg=y x11-base/xlibre-server x11-base/xlibre-drivers
```

If you want source-fallback to also work for anything XLibre-related not
covered by the binary, you'll need the `X11Libre/ports-gentoo` overlay
added on your own machine too, same one the CI container uses.

## Why it might fall back to source anyway

- Your local USE flags don't match the build-time USE for that package —
  see `package.use.template`.
- Your `~arch` keyword acceptance doesn't match — see
  `package.accept_keywords.template`.
- The package simply isn't in any `packages*.list` yet — open a package
  request issue using the template in this repo.
- The rolling build is older than your currently-synced portage tree and
  Portage considers the binary stale — this resolves itself on the next
  scheduled build (Sundays, ahead of the ISO's own weekly build).
