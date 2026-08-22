# ◈ Contributing a package

## Adding to the curated set

1. Add a line to the relevant `packages*.list` (seven groups exist:
   `packages.list` core, `packages.graphics.list`, `packages.desktop.list`,
   `packages.browser.list`, `packages.kde-qt.list`, `packages.xorg.list`,
   `packages.xlibre.list`):

   ```
   category/package[-version]  [use:flag1,-flag2]
   ```

2. Open a PR. `build-packages.yml` triggers on any PR touching a
   `packages*.list` and attempts the build inside the real musl+llvm
   container for that group.
3. On a PR, packages are uploaded to a throwaway release tagged
   `binpkgs-artifacts-pr-<number>` rather than the rolling release, and the
   published `Packages` index (both the Release copy and the
   choccynix.github.io mirror) is left untouched — merging to `main` is
   what actually publishes.
4. Check `build-report-<group>.json` (uploaded to the release for that
   run, even on failure) if a build fails.

## Things that commonly break under musl+llvm

- `dev-qt/qtcore`/`qtgui`/`qtwidgets`/`qtnetwork`/`qtdbus` don't exist as
  standalone Qt6 packages — Qt6 consolidates them into `dev-qt/qtbase` via
  USE flags. Only relevant if adding new Qt-dependent packages.
- Packages needing X11 pull in `mesa` with a different USE combination
  than the Wayland stack (`packages.graphics.list` builds mesa with `-X`)
  — this is fine as long as they're in different matrix groups (separate
  containers), but would conflict within the same list.
- `--nodeps`-style single-atom builds break interdependent sets (shared
  deps like `boost` need consistent USE flags across everything that
  needs them) — `build-binpkg.py` builds each group's whole list in one
  combined `emerge` call specifically to avoid this.
- glibc-only build systems are the most common source of genuine musl
  build failures — if in doubt, open the PR anyway and let CI tell you.

## Requesting without building it yourself

Use the "◈ Package request" issue template instead of a PR if you don't
want to write the `packages*.list` line yourself.
