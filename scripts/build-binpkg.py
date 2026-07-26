#!/usr/bin/env python3
"""
◈ build-binpkg.py

Reads packages.list, runs `emerge --buildpkg --usepkg=n` for each atom inside
the musl-llvm build container, and leaves finished .gpkg.tar (or legacy
.tbz2, depending on Portage's binpkg-format setting) files under PKGDIR
for a later step to collect and upload.

Stdlib only — no third-party deps, consistent with the rest of the toolchain.

Usage:
    python3 build-binpkg.py packages.list /var/cache/binpkgs

Exit codes:
    0  all atoms built successfully
    1  one or more atoms failed (failures are still logged/collected so CI
       can report per-package status rather than aborting the whole run)
"""
import subprocess
import sys
import re
import json
from pathlib import Path

ATOM_LINE = re.compile(r"^(?P<atom>\S+)(?:\s+use:(?P<use>\S+))?\s*$")


def parse_packages_list(path: Path):
    atoms = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        m = ATOM_LINE.match(line)
        if not m:
            print(f"[warn] could not parse line, skipping: {raw_line!r}", file=sys.stderr)
            continue
        atoms.append((m.group("atom"), m.group("use")))
    return atoms


def build_atom(atom: str, use_override: str | None, pkgdir: Path) -> tuple[bool, str]:
    env_use = ""
    if use_override:
        # translate "lua,-python" into a USE string: "lua -python"
        env_use = " ".join(flag.strip() for flag in use_override.split(","))

    cmd = ["emerge", "--buildpkg", "--usepkg=n", "--nodeps", "--quiet-build=y", atom]

    print(f"[build] {atom} (USE={env_use or 'default'})")
    import os
    env = os.environ.copy()
    env["PKGDIR"] = str(pkgdir)
    if env_use:
        env["USE"] = f"{env.get('USE', '')} {env_use}".strip()

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    ok = result.returncode == 0
    if not ok:
        print(f"[fail] {atom}\n{result.stderr[-4000:]}", file=sys.stderr)
    else:
        print(f"[ok]   {atom}")
    return ok, result.stderr


def main():
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} packages.list PKGDIR", file=sys.stderr)
        sys.exit(2)

    list_path = Path(sys.argv[1])
    pkgdir = Path(sys.argv[2])
    pkgdir.mkdir(parents=True, exist_ok=True)

    atoms = parse_packages_list(list_path)
    print(f"[info] {len(atoms)} atoms to build")

    results = {}
    any_failed = False
    for atom, use_override in atoms:
        ok, log = build_atom(atom, use_override, pkgdir)
        results[atom] = {"ok": ok, "log_tail": log[-2000:] if not ok else ""}
        any_failed = any_failed or not ok

    report_path = pkgdir / "build-report.json"
    report_path.write_text(json.dumps(results, indent=2))
    print(f"[info] report written to {report_path}")

    sys.exit(1 if any_failed else 0)


if __name__ == "__main__":
    main()
