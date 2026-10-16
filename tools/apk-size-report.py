#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Break down where the megabytes of one or more built APKs come from.

Usage:
    python3 tools/apk-size-report.py app.apk [another.apk ...] [--top N] [--json]

It prints, per APK, the packed (compressed) size of each group:
    lib/<abi>/   native libraries, grouped per CPU architecture
    dex          classes*.dex    (Java/Kotlin code)
    res/         compiled resources
    assets/      raw assets
    resources.arsc, META-INF/, other

Native libraries are normally *compressed* inside these APKs
(`jniLibs { useLegacyPackaging true }`), so every extra ABI adds a whole
extra compressed copy of every .so -> that is why a 4-ABI "universal" APK is
roughly 2.5x the size of a single-ABI one.

No third-party dependency: plain stdlib zipfile.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
from collections import defaultdict

GROUPS = (
    ("dex", "Java/Kotlin dex"),
    ("res/", "resources"),
    ("assets/", "assets"),
    ("resources.arsc", "resource table"),
    ("META-INF/", "signatures"),
    ("kotlin/", "kotlin metadata"),
    ("other", "other"),
)


def group_of(name: str) -> str:
    if name.startswith("lib/"):
        parts = name.split("/")
        if len(parts) >= 3:
            return "lib/%s/" % parts[1]
        return "lib/"
    if name == "resources.arsc":
        return "resources.arsc"
    if name == "classes.dex" or (name.startswith("classes") and name.endswith(".dex")):
        return "dex"
    for prefix in ("res/", "assets/", "META-INF/", "kotlin/"):
        if name.startswith(prefix):
            return prefix
    if name.endswith(".kotlin_module"):
        return "kotlin/"
    return "other"


def scan(path: str) -> dict:
    groups_packed: dict[str, int] = defaultdict(int)
    groups_raw: dict[str, int] = defaultdict(int)
    groups_count: dict[str, int] = defaultdict(int)
    libs: dict[str, int] = defaultdict(int)  # "lib/<abi>/<name>" -> packed

    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            g = group_of(info.filename)
            groups_packed[g] += info.compress_size
            groups_raw[g] += info.file_size
            groups_count[g] += 1
            if info.filename.startswith("lib/"):
                libs[info.filename] = info.compress_size

    return {
        "path": path,
        "file_size": os.path.getsize(path),
        "groups": {
            g: {
                "packed": groups_packed.get(g, 0),
                "raw": groups_raw.get(g, 0),
                "entries": groups_count.get(g, 0),
            }
            for g in set(list(groups_packed) + [k for k, _ in GROUPS])
        },
        "libs": dict(libs),
    }


def mb(value: int) -> str:
    return "%.2f" % (value / 1048576.0)


def abi_of(group: str) -> str:
    return group[len("lib/"):-1] if group.startswith("lib/") and group.endswith("/") else ""


def print_report(rep: dict, top: int) -> None:
    total = rep["file_size"]
    packed_total = sum(g["packed"] for g in rep["groups"].values())
    print("=" * 74)
    print("%s" % rep["path"])
    print("  file size (on disk) : %s MB (%d bytes)" % (mb(total), total))
    print("  packed entries      : %s MB   (zip payload / central directory adds the rest)"
          % mb(packed_total))
    print("-" * 74)
    print("  %-27s %10s %10s %7s %8s" % ("group", "packed MB", "raw MB", "share", "entries"))

    rows = sorted(rep["groups"].items(), key=lambda kv: -kv[1]["packed"])

    def label(g: str) -> str:
        abi = abi_of(g)
        if abi:
            return "lib/%s (native)" % abi
        for key, human in GROUPS:
            if g == key:
                return "%s (%s)" % (key, human)
        return g

    for g, data in rows:
        if data["packed"] == 0 and g != "other":
            continue
        share = (data["packed"] / total * 100.0) if total else 0.0
        print("  %-27s %10s %10s %6.1f%% %8d"
              % (label(g), mb(data["packed"]), mb(data["raw"]), share, data["entries"]))

    abis = sorted(abi_of(g) for g in rep["groups"] if abi_of(g))
    if abis:
        print("-" * 74)
        print("  ABIs in this APK: %s" % ", ".join(abis))
        print("  biggest native libraries (packed):")
        for name, size in sorted(rep["libs"].items(), key=lambda kv: -kv[1])[: max(top, 1)]:
            print("    %-52s %8s MB" % (name, mb(size)))
    print()


def packed_of(rep: dict, group: str) -> int:
    entry = rep["groups"].get(group)
    return entry["packed"] if entry else 0


def print_comparison(reps: list[dict]) -> None:
    groups = sorted({g for rep in reps for g in rep["groups"]},
                    key=lambda g: -max(packed_of(rep, g) for rep in reps))
    name_width = max(24, max(len(g) for g in groups))
    headers = [os.path.basename(rep["path"])[:26] for rep in reps]

    print("=" * 74)
    print("COMPARISON (packed MB per group)")
    print("  %-*s %s" % (name_width, "group", "  ".join("%26s" % h for h in headers)))
    print("  %-*s %s" % (name_width, "file size",
                         "  ".join("%26s" % mb(rep["file_size"]) for rep in reps)))
    for g in groups:
        if all(packed_of(rep, g) == 0 for rep in reps):
            continue
        print("  %-*s %s" % (name_width, g,
                             "  ".join("%26s" % mb(packed_of(rep, g)) for rep in reps)))
    print()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("apks", nargs="+", help="built .apk file(s)")
    parser.add_argument("--top", type=int, default=10,
                        help="how many native libraries to list per APK (default 10)")
    parser.add_argument("--json", action="store_true", help="dump raw numbers as JSON")
    args = parser.parse_args(argv)

    reps = []
    for path in args.apks:
        if not os.path.isfile(path):
            print("not a file: %s" % path, file=sys.stderr)
            return 1
        try:
            reps.append(scan(path))
        except zipfile.BadZipFile:
            print("not a valid APK/zip: %s" % path, file=sys.stderr)
            return 1

    if args.json:
        print(json.dumps(reps, indent=2))
        return 0

    for rep in reps:
        print_report(rep, args.top)
    if len(reps) > 1:
        print_comparison(reps)

    if len(reps) > 1:
        print("Tip: universal vs single-ABI -- the difference is the extra lib/<abi>/ groups.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
