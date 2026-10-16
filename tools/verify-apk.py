#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify that a downloaded MicroG-RE APK is the genuine official release file.

Why: Android phone-manager / antivirus apps (Realme, OPPO, OnePlus, vivo, ...
all powered by the Avast engine) flag microG with a heuristic detection
("Evo-gen", "AdCheat", "risky app"). That is a known false positive -- but it
also means you must make sure the file you downloaded is really the official
one and not a repackaged copy from a random APK website.

This script computes the SHA-256 of an APK and compares it with the official
digests published by GitHub for the releases of MorpheApp/MicroG-RE.

Usage:
    python3 tools/verify-apk.py microg-7.2.1-icon-arm64-v8a.apk
    python3 tools/verify-apk.py *.apk --fetch        # refresh digests from GitHub
    python3 tools/verify-apk.py my.apk --offline     # only use built-in digests
    python3 tools/verify-apk.py my.apk --list        # show known official digests

Exit code: 0 = matches an official release, 1 = no match / error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import zipfile

UPSTREAM = "MorpheApp/MicroG-RE"

# Official SHA-256 digests published by GitHub for MorpheApp/MicroG-RE release
# assets (repos/.../releases -> assets[].digest). Refresh with --fetch.
OFFICIAL: dict[str, dict[str, tuple[int, str]]] = {
    "7.2.2-dev.2": {
        "microg-7.2.2-dev.2.apk": (112362171, "9fd553479b311f37039556e1abb671580651ce6ded0cb28ce5faa424e9495ac3"),
        "microg-7.2.2-dev.2-noicon.apk": (112362171, "9ab67089cfcb7088cc6e78df3dcfbc38b6e286c2a8e84f3ed63b03b16124463f"),
        "microg-7.2.2-dev.2-icon-arm64-v8a.apk": (44928071, "9b4128e4e05ab2b51906a79158803bf7fe446b42edce53f7e13c87069e5edfb3"),
        "microg-7.2.2-dev.2-noicon-arm64-v8a.apk": (44928071, "0be6abf9aea3a66983f6710d1687caa110dfd77523b9841892549e156de40dc0"),
        "microg-7.2.2-dev.2-icon-armeabi-v7a.apk": (42720341, "3c944d926e8548623ffb991915afc27b372a21462c245280872e01c8217d9dc2"),
        "microg-7.2.2-dev.2-noicon-armeabi-v7a.apk": (42720341, "6a64b9700ae38e4ad2124c27080f0c76238318a9e57980a9f97438565530aaad"),
    },
    "7.2.1": {
        "microg-7.2.1.apk": (112362171, "8c0ae9abfc698e9f4ccc8cbc306b19481ff0066634e7c5baeea2ede3579cdd91"),
        "microg-7.2.1-noicon.apk": (112362171, "1fd47f3908fcb11a4c694272432699141c6d7690dc446cebbab1ade136c63476"),
        "microg-7.2.1-icon-arm64-v8a.apk": (44928071, "3425e46e95cd45012892cfaa23061b70db0a25affffcfcb84e3df4511d63eb82"),
        "microg-7.2.1-noicon-arm64-v8a.apk": (44928071, "a4af6e46d10eefedc14e9642b6fbe1acd1dafa7356f7252dd039159e78eefbb6"),
        "microg-7.2.1-icon-armeabi-v7a.apk": (42720341, "a96fcb82f3547e0864b17e97894c8cecb1d9ca11e4f1d4c0996bf8bebafcaf91"),
        "microg-7.2.1-noicon-armeabi-v7a.apk": (42720341, "f0ccb8c2d2e5c002142e7949876a02aa2c538a18974bced9df9f50496c48d353"),
    },
}


def sha256_of(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def fetch_official(tags: list[str] | None = None) -> dict[str, dict[str, tuple[int, str]]]:
    """Refresh official digests from the GitHub API (no auth needed)."""
    import urllib.error
    import urllib.request

    out: dict[str, dict[str, tuple[int, str]]] = {}
    url = "https://api.github.com/repos/%s/releases?per_page=100" % UPSTREAM
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "verify-apk.py",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        releases = json.load(resp)
    for rel in releases:
        tag = rel.get("tag_name", "")
        if tags and tag not in tags:
            continue
        assets: dict[str, tuple[int, str]] = {}
        for asset in rel.get("assets", []):
            digest = asset.get("digest") or ""
            if digest.startswith("sha256:") and asset["name"].endswith(".apk"):
                assets[asset["name"]] = (asset["size"], digest[len("sha256:"):])
        if assets:
            out[tag] = assets
    return out


def abis_of(path: str) -> list[str]:
    try:
        with zipfile.ZipFile(path) as zf:
            return sorted({n.split("/")[1] for n in zf.namelist()
                           if n.startswith("lib/") and len(n.split("/")) > 2})
    except zipfile.BadZipFile:
        return []


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("apks", nargs="*", help="downloaded .apk file(s)")
    parser.add_argument("--fetch", action="store_true",
                        help="refresh the official digest list from the GitHub API")
    parser.add_argument("--list", action="store_true",
                        help="only print the known official digests")
    parser.add_argument("--offline", action="store_true",
                        help="never touch the network (skip --fetch failures silently)")
    args = parser.parse_args(argv)

    table = OFFICIAL
    if args.fetch and not args.offline:
        try:
            fresh = fetch_official()
            if fresh:
                table = {**OFFICIAL, **fresh}
                print("Fetched %d release(s) worth of official digests from GitHub.\n"
                      % len(fresh))
        except Exception as exc:  # noqa: BLE001 - report and fall back
            print("warning: could not fetch digests from GitHub (%s); using built-in list\n"
                  % exc, file=sys.stderr)

    if args.list:
        for tag in sorted(table, reverse=True):
            print(tag)
            for name, (size, digest) in sorted(table[tag].items()):
                print("  %-42s %12d  %s" % (name, size, digest))
        return 0

    if not args.apks:
        parser.error("give at least one .apk file (or use --list)")

    by_digest = {(digest, size): name
                 for tag in table for name, (size, digest) in table[tag].items()}

    ok = True
    for path in args.apks:
        if not os.path.isfile(path):
            print("ERROR  %s: file not found" % path)
            ok = False
            continue

        digest = sha256_of(path)
        size = os.path.getsize(path)
        known = by_digest.get((digest, size))

        print("=" * 78)
        print(path)
        print("  size      : %d bytes (%.2f MB)" % (size, size / 1048576.0))
        print("  sha256    : %s" % digest)
        print("  native ABI: %s" % (", ".join(abis_of(path)) or "(none)"))
        if known:
            print("  VERDICT   : MATCH -> this is the genuine official %s asset" % known)
            print("              (%s). A phone-manager 'risky app' / Avast 'Evo-gen'"
                  % UPSTREAM)
            print("              warning on this file is a known FALSE POSITIVE.")
        else:
            print("  VERDICT   : NO MATCH with any known official release asset.")
            print("              Do NOT install it until you downloaded it again from")
            print("              https://github.com/%s/releases  (or morphe.software)."
                  % UPSTREAM)
            print("              Run with --fetch to include newer releases.")
            ok = False
        print()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
