#!/usr/bin/env python3
"""Patch richtap_haptic_hv.ko so the RichTap driver binds in recovery.

The prebuilt module builds a boot-mode skip mask with `mov w9, #0x304` and
skips i2c driver registration when the boot mode is 2, 8 or 9. Recovery
reports mode 2, so the module loads without binding haptic_hv@5A and
/sys/class/leds/vibrator_single never appears.

Changing the immediate to 0x300 removes mode 2 from the skip mask.

Usage:
  python3 tools/patch_haptic_ko.py [--check] <path-to-richtap_haptic_hv.ko>

--check does not write: exit 0 = already patched, 2 = needs patch, 1 = error.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

# init_module: cmp w0,#0x9 ; str w0,[x8] ; b.hi ; mov w8,#1 ; mov w9,#0x304 ; lsl
ORIG = bytes.fromhex("1f240071000100b90801005428008052896080520821c01a")
NEW = bytes.fromhex("1f240071000100b90801005428008052096080520821c01a")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(argv: list[str]) -> int:
    paths = [a for a in argv[1:] if not a.startswith("-")]
    check = "--check" in argv
    if len(paths) != 1:
        print(__doc__.strip())
        return 1

    path = Path(paths[0])
    try:
        data = path.read_bytes()
    except OSError as exc:
        print(f"error: {exc}")
        return 1

    n_orig = data.count(ORIG)
    n_new = data.count(NEW)
    if n_new == 1 and n_orig == 0:
        print(f"{path}: already patched")
        return 0
    if n_orig == 1 and n_new == 0:
        if check:
            print(f"{path}: needs patch (boot-mode mask 0x304)")
            return 2
        patched = data.replace(ORIG, NEW, 1)
        path.write_bytes(patched)
        print(f"patched {path}")
        print(f"  sha256 {sha256(data)} -> {sha256(patched)}")
        return 0

    print(f"error: instruction signature not unique in {path} "
          f"(orig={n_orig}, patched={n_new})")
    print("The module build changed. Disassemble init_module with llvm-objdump")
    print("and re-derive the boot-mode mask; do not patch a raw offset.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
