# ◈ Consuming the AthanorOS binhost

## What you're pointing at

`PORTAGE_BINHOST` is set to GitHub's stable "latest release" URL —
`https://github.com/ORG/REPO/releases/latest/download` — which always
resolves to whatever the newest `binpkgs-rolling-YYYYMMDD` release is,
without you needing to track or update a dated tag yourself. That URL
serves the `Packages` file — Portage's binhost index format — as a
release asset. Each package entry in the index carries its own absolute
`URI` pointing at wherever its actual `.gpkg.tar` blob was uploaded (also
a Release asset, per group/day), so Portage fetches the index from one
stable place and the actual packages from wherever they individually live.

CORRECTED: this used to describe a gh-pages URL. That was never actually
served — GitHub Pages was never enabled for the repo — so if you set this
up before and it didn't work, that's why. Everything now goes entirely
through Releases.

## Setup

1. Copy `templates/make.conf.binhost.template` into `/etc/portage/make.conf`
   (or append its contents if you already have entries there), replacing
   ORG/REPO with the actual GitHub org/repo.
2. Copy `templates/package.use.template` to
   `/etc/portage/package.use/athanor-binpkgs`, matching flags against
   whatever's currently in upstream `packages*.list`.
3. If any packages track `~arch` (several in `packages.kde-qt.list` and
   everything in the `xlibre` overlay do), do the same with
   `templates/package.accept_keywords.template`.
4. Import the signing key if you want the `binpkg-signing` FEATURES check
   to actually verify anything — it's published as a release asset too:

   ```
   curl -fsSL https://github.com/ORG/REPO/releases/latest/download/athanor-binpkgs.pub.asc \
     -o /etc/portage/gpg/athanor-binpkgs.pub.asc
   ```

5. Sync and try installing something known to be in one of the
   `packages*.list` files:

   ```
   emerge --sync
   emerge --getbinpkg=y --usepkg=y gui-wm/sway
   ```

   Portage logs will say `[binary]` next to the package name if it pulled
   the prebuilt version instead of compiling.

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
