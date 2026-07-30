# athanor-binpkgs

◈ Prebuilt binary packages for **AthanorOS** — a musl+llvm+openrc Gentoo derivative.

This repo is the *retort* — it holds no binaries itself. It holds the scripts,
templates, and CI wiring that build packages inside the same
`gentoo/stage3:musl-llvm` container used for the ISO, then publish them as
GitHub Release assets. A `Packages` index (Portage's binhost metadata format)
is regenerated on every publish and served via GitHub Pages, so end users
point `PORTAGE_BINHOST` at one stable URL while the actual `.gpkg.tar` blobs
live wherever Releases puts them.

## Why not just commit binaries to git?

Git repos degrade badly once binary blobs accumulate — every clone re-downloads
the full history, and there's no garbage collection for old package versions.
GitHub Releases already solves this for the AthanorOS ISOs; this repo reuses
that exact mechanism instead of reinventing it.

## Layout

```
athanor-binpkgs/
├── packages.list               core set: small, fast-building tools
├── packages.graphics.list      Wayland-minimal graphics stack (mesa, wlroots, seatd)
├── packages.desktop.list       usable live desktop (sway, foot)
├── packages.firefox.list       firefox, isolated in its own group (long compile)
├── packages.calamares.list     installer stack (Qt5, KF5, KPMcore, Calamares)
├── .github/workflows/
│   ├── build-packages.yml      matrix build across all five lists, then merges
│   │                           + signs + publishes one combined Packages index
│   └── publish-index.yml       manual re-sign/re-publish without a full rebuild
├── scripts/
│   ├── build-binpkg.py         one combined `emerge --buildpkg` per list (CI + local use)
│   ├── generate-packages-index.py  builds the Portage-compatible Packages file
│   ├── merge-packages-index.py     combines each group's fragment into one index
│   ├── sync-ccache.py          persists a per-group ccache between CI runs
│   ├── sign-packages.py        GPG-signs the index
│   ├── upload-release.py       stdlib-only GitHub Releases uploader (package blobs)
│   └── upload-single-asset.py  uploads/replaces one named asset (fragments, ccache)
├── templates/                  copy-paste configs for end users and contributors
└── docs/                       setup guide, contributing guide, signing notes
```

## Why five lists instead of one

GitHub-hosted runners hard-cap every job at 6 hours, no matter the plan. A
serial build of Mesa + Sway + Firefox + Qt5 + KDE Frameworks + KPMcore +
Calamares could easily exceed that (Firefox alone has hit the ceiling on
its own). `build-packages.yml` builds `core`, `graphics`, `desktop`,
`firefox`, and `calamares` as five parallel matrix jobs, each with its own
ccache (persisted as a release asset on a fixed `build-cache` tag), so the
first run is slow but every rebuild after that only recompiles what
changed — and a slow group like `firefox` can't hold up or get cancelled
alongside fast ones like `desktop`. A final job merges all five groups'
index fragments into one combined `Packages` file before publishing.

Each group's `emerge` invocation covers its *entire* list in one call
rather than one atom at a time — that's what lets Portage's solver pick
mutually consistent USE flags for shared dependencies (e.g. `boost` needing
`python` for `calamares` but not for anything else in `core`) instead of
locking in a USE combination too early and hitting a conflict later in the
same run.

## Quick start (consuming packages)

See `docs/binhost-setup.md`. Short version: copy
`templates/make.conf.binhost.template` into `/etc/portage/make.conf`.

## Quick start (contributing a package)

See `docs/contributing-packages.md`. Short version: add a line to
`packages.list`, open a PR — CI builds it and reports back on the PR whether
it compiled cleanly under musl+llvm.

## Pillars

Same three as AthanorOS proper: **Divergence, Minimalism, Transmutation.**
This repo exists so `Transmutation` — turning source into something usable —
doesn't have to happen on every single machine, every single time.
