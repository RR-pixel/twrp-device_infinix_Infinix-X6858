#!/usr/bin/env python3
"""Patch adaptive-ts.ko so the Transsion touch panel probes in recovery.

mtk_get_boot_mode() maps the MTK boot mode to a driver state. It returns 2
for modes 1/4/6 and 1 for modes 2/8/9; recovery reports mode 2, so the
driver takes its recovery path and never probes the panel. TWRP then has a
working display but no touch.

Changing both early returns to 0 makes the driver take the normal-boot
path. The two instructions live in one contiguous block, matched as a unit
so a changed build fails instead of patching the wrong return.

Usage:
  python3 tools/patch_adaptive_ts_ko.py [--check] <path-to-adaptive-ts.ko>

--check does not write: exit 0 = already patched, 2 = needs patch, 1 = error.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

# mtk_get_boot_mode: mov w8,#1 ; mov w9,#0x52 ; lsl ; tst ; b.eq
#                    mov w0,#2 ; b ; mov w9,#0x304 ; tst ; b.eq
#                    printk message ; bl ; mov w0,#1 ; b
ORIG = bytes.fromhex(
    "28008052490a80520821c31a1f01096a6000005440008052eaffff17"
    "896080521f01096ac0fcff5400000090000000910100009021000091"
    "e22380520000009420008052dfffff17"
)
NEW = bytes.fromhex(
    "28008052490a80520821c31a1f01096a6000005400008052eaffff17"
    "896080521f01096ac0fcff5400000090000000910100009021000091"
    "e22380520000009400008052dfffff17"
)


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
            print(f"{path}: needs patch (boot-mode returns 2 and 1)")
            return 2
        patched = data.replace(ORIG, NEW, 1)
        path.write_bytes(patched)
        print(f"patched {path}")
        print(f"  sha256 {sha256(data)} -> {sha256(patched)}")
        return 0

    print(f"error: instruction signature not unique in {path} "
          f"(orig={n_orig}, patched={n_new})")
    print("The module build changed. Disassemble mtk_get_boot_mode with")
    print("llvm-objdump and re-derive the boot-mode returns; do not patch a")
    print("raw offset.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
