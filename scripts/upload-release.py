#!/usr/bin/env python3
"""
◈ upload-release.py

stdlib-only GitHub Releases uploader for binary packages — same approach as
the ISO release script (urllib + the REST API, no `gh` CLI, no third-party
deps, since the musl-llvm container can't run Node-based tooling anyway).

Creates (or reuses) a release tagged e.g. `binpkgs-rolling-YYYYMMDD`, uploads
every package file found under PKGDIR, and writes upload-map.json mapping
each package's relative path to its final browser_download_url, for
generate-packages-index.py to consume.

Requires GITHUB_TOKEN and GITHUB_REPOSITORY (both set automatically inside
GitHub Actions) in the environment.

CORRECTED from an earlier revision: deletes any existing asset with the
same name before uploading. Without this, re-running the workflow on the
same UTC day (same rolling tag) crashed with a 422 "already_exists" the
moment it hit a filename already uploaded by an earlier attempt that day.

Usage:
    python3 upload-release.py PKGDIR binpkgs-rolling-20260726 upload-map.json
"""
import json
import mimetypes
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

API = "https://api.github.com"


def api_request(method: str, url: str, token: str, data: bytes | None = None, content_type: str = "application/json"):
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data is not None:
        req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"[error] {method} {url} -> {e.code}\n{body}", file=sys.stderr)
        raise


def get_or_create_release(repo: str, tag: str, token: str) -> dict:
    try:
        return api_request("GET", f"{API}/repos/{repo}/releases/tags/{tag}", token)
    except urllib.error.HTTPError:
        pass  # doesn't exist yet, fall through to create

    payload = json.dumps({
        "tag_name": tag,
        "name": tag,
        "body": f"Automated binary package build: {tag}",
        "prerelease": "rolling" not in tag,
    }).encode()
    return api_request("POST", f"{API}/repos/{repo}/releases", token, data=payload)


def delete_existing_asset(release: dict, name: str, repo: str, token: str) -> None:
    for asset in release.get("assets", []):
        if asset["name"] == name:
            req = urllib.request.Request(f"{API}/repos/{repo}/releases/assets/{asset['id']}", method="DELETE")
            req.add_header("Authorization", f"Bearer {token}")
            urllib.request.urlopen(req)
            return


def upload_asset(release: dict, file_path: Path, token: str) -> dict:
    upload_url = release["upload_url"].split("{", 1)[0]
    mime, _ = mimetypes.guess_type(str(file_path))
    mime = mime or "application/octet-stream"
    data = file_path.read_bytes()
    url = f"{upload_url}?name={file_path.name}"
    return api_request("POST", url, token, data=data, content_type=mime)


def main():
    if len(sys.argv) != 4:
        print(f"usage: {sys.argv[0]} PKGDIR TAG OUTPUT_MAP_JSON", file=sys.stderr)
        sys.exit(2)

    pkgdir = Path(sys.argv[1])
    tag = sys.argv[2]
    out_map_path = Path(sys.argv[3])

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("[error] GITHUB_TOKEN and GITHUB_REPOSITORY must be set", file=sys.stderr)
        sys.exit(1)

    release = get_or_create_release(repo, tag, token)
    print(f"[info] using release {tag} (id={release['id']})")

    upload_map = {}
    files = sorted(p for p in pkgdir.rglob("*") if p.is_file() and p.name not in {"Packages", "build-report.json"})
    print(f"[info] uploading {len(files)} package files")

    for f in files:
        rel = str(f.relative_to(pkgdir))
        print(f"[upload] {rel}")
        delete_existing_asset(release, f.name, repo, token)
        asset = upload_asset(release, f, token)
        upload_map[rel] = asset["browser_download_url"]

    out_map_path.write_text(json.dumps(upload_map, indent=2))
    print(f"[info] wrote {len(upload_map)} entries to {out_map_path}")


if __name__ == "__main__":
    main()
