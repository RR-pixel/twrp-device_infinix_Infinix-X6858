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
import re
import sys
from pathlib import Path

# mtk_get_boot_mode: mov w8,#1 ; mov w9,#0x52 ; lsl ; tst ; b.eq
#                    mov w0,#2 ; b ; mov w9,#0x304 ; tst ; b.eq
#                    printk message ; bl ; mov w0,#1 ; b
#
# The printk call passes __LINE__ as `mov w2,#imm16`. That immediate changes
# between module builds (0x11f in 16.3, 0x112 in 16.2) without any change in
# logic, so it is matched as a wildcard instead of a fixed value. Everything
# else in the block must still match exactly.
_PRE = bytes.fromhex(
    "28008052490a80520821c31a1f01096a6000005440008052eaffff17"
    "896080521f01096ac0fcff5400000090000000910100009021000091"
)
_POST = bytes.fromhex("0000009420008052dfffff17")
_POST_NEW = bytes.fromhex("0000009400008052dfffff17")
# mov w2,#imm16 : b0 low 5 bits = 2, b1 any, b2 in 0x80..0x9f, b3 = 0x52
_MOV_W2 = rb"[\x02\x22\x42\x62\x82\xa2\xc2\xe2][\x00-\xff][\x80-\x9f]\x52"
_PRE_NEW = _PRE[:20] + bytes.fromhex("00008052") + _PRE[24:]

ORIG_RE = re.compile(re.escape(_PRE) + _MOV_W2 + re.escape(_POST), re.DOTALL)
NEW_RE = re.compile(re.escape(_PRE_NEW) + _MOV_W2 + re.escape(_POST_NEW), re.DOTALL)

# Offsets inside the matched block of the two `mov w0,#N` returns to zero out.
_RET_OFFSETS = (20, len(_PRE) + 4 + 4)
_ZERO_RET = bytes.fromhex("00008052")


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

    orig_matches = list(ORIG_RE.finditer(data))
    new_matches = list(NEW_RE.finditer(data))
    n_orig = len(orig_matches)
    n_new = len(new_matches)
    if n_new == 1 and n_orig == 0:
        print(f"{path}: already patched")
        return 0
    if n_orig == 1 and n_new == 0:
        if check:
            print(f"{path}: needs patch (boot-mode returns 2 and 1)")
            return 2
        start = orig_matches[0].start()
        buf = bytearray(data)
        for off in _RET_OFFSETS:
            buf[start + off:start + off + 4] = _ZERO_RET
        patched = bytes(buf)
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
  
