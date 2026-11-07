# AGENTS.md — Infinix X6855 / TWRP 16.0

## Device

Infinix NOTE 50 PRO 5G, codename `Infinix-X6855`, MediaTek MT6789
(Helio G100 Ultimate), Android 16 / kernel 6.12.38.

This tree uses the shared `device/transsion/mt6789-common` tree for boot
layout, recovery fstab, init, TEE and crypto configuration.

## Constraints

1. Android 16 firmware with a 6.12 kernel only. Android 15 and older are
   unsupported.
2. Keep TWRP/build-system changes as patches under `patches/`, applied by
   `vendorsetup.sh`. Do not leave unrecorded source edits as the
   implementation of a fix.
3. Do not claim hardware validation without an actual X6855 test. Build
   success alone is not hardware validation.
4. Preserve unrelated work. Do not reset or discard unrelated trees.

## Build

```bash
repo init --depth=1 -u https://github.com/TWRP-Test/platform_manifest_twrp_aosp.git -b twrp-16.0
repo sync
# device trees are local checkouts under device/infinix/
source build/envsetup.sh
lunch twrp_X6855
m vendorbootimage
```

Output: `out/target/product/Infinix-X6855/vendor_boot.img`.

Use `~/twrp-16.0/tmp/` for scratch files. Do not write build scratch to
`/tmp`.

## Porting architecture

- `prebuilt/dtb.img` is the stock X6855 vendor_boot DTB
  (`c6a71e8dd261193acdf8d13838a6e906640dbe2c93cfc953360fb1c2747b7b85`).
- `recovery/root/lib/modules/` is the stock X6855 platform-ramdisk module
  set, plus the touch modules from `odm_dlkm`:
  - `adaptive-ts.ko` — patched by `tools/patch_adaptive_ts_ko.py` so the
    driver probes the panel in recovery. The patched hash is
    `4896112fc234f000d426bb558b550216bf4b332ed305dd6378d369a60f6be719`.
    Do not replace it with the unpatched stock module.
  - `focaltech_ft3683g.ko` — FocalTech touch controller.
  - `modules.load.recovery` loads both after their dependencies.
- `recovery/root/vendor/firmware/` and `recovery/root/odm/firmware/` are
  copied from the X6855 dump, including FocalTech, Goodix, haptic, LED
  and wireless-charging firmware.
- The common tree builds an empty `emptyrecovery` RECOVERY fragment and
  keeps the TWRP payload in the platform ramdisk.
### Haptics / RichTap (AW8697)

The haptic amplifier is an AWINIC RichTap AW8697 on i2c (`haptic_hv@5A`,
`richtap_haptic_hv.ko`), not the MTK `regulator-vibrator` LED. The stock
X6855 DTBO contains `/fragment@18/__overlay__/haptic_hv@5A` with
`compatible = "awinic,haptic_hv"`; the boot DTB's `regulator-vibrator`
node only toggles a rail. The stock recovery module list does not load the
RichTap module; this tree adds it to `recovery/root/lib/modules/` and to
`modules.load.recovery`.

- The stock module builds a boot-mode skip mask with `mov w9, #0x304` and
  skips i2c driver registration for modes 2, 8 and 9. Recovery reports
  mode 2, so `vibrator_single` never appears. Patch every packaged copy
  with `tools/patch_haptic_ko.py` (mask `0x304` -> `0x300`):

  ```bash
  python3 tools/patch_haptic_ko.py \
    recovery/root/lib/modules/richtap_haptic_hv.ko
  ```

  The patched hash is
  `564dd496228464c6f3d4f68dfcff339fff223ea7d81b30af8710d44565d0083b`.
  `vendorsetup.sh` re-checks this automatically.
- `init.device.rc` writes `1` to
  `/sys/class/leds/vibrator_single/ram_update` when
  `sys.boot_completed=1`, loading `haptic_ram.bin` in ~200 ms instead of
  waiting for the driver's ~8 s deferred work.
- `haptic_ram.bin` and the `haptic_rtp*.bin` files are kept in both
  `vendor/firmware/` and `odm/firmware/`.
- The TWRP haptics patch probes `vibrator_single` duration/activate first,
  then the generic `vibrator` pair, `timed_output`, and a
  `vibrator/brightness` pulse.
- Do not `rmmod` the module after a failed registration; its cleanup path
  panics the kernel. Rebuild and flash instead.

## Kernel module updates

The current payload uses only two stock module sources:

1. `vendor_boot.img` platform ramdisk — `lib/modules/`:
   `modules.load.recovery`, `modules.load`, `modules.dep`,
   `modules.alias`, `modules.softdep`, and all 244 modules. It is
   self-contained: every stock `modules.load.recovery` entry and every
   `modules.dep` dependency exists in this directory.
2. `odm_dlkm` — `lib/modules/`:
   `adaptive-ts.ko`, `focaltech_ft3683g.ko`, `richtap_haptic_hv.ko`.
   These are normally loaded by `odm_dlkm/lib/modules/modules.load`, not
   by the stock recovery list.

`vendor_dlkm` and `system_dlkm` are not used directly. Only pull a module
from them if a future stock `modules.load.recovery` references a module
that is missing from the new platform ramdisk.

### New firmware update

1. Extract the new matching `vendor_boot.img` platform ramdisk and
   `odm_dlkm` from the firmware dump.
2. Replace `recovery/root/lib/modules` with the new platform ramdisk
   `lib/modules` (keep the metadata files).
3. Copy the new `odm_dlkm` touch/haptic modules into the same directory:
   `adaptive-ts.ko`, `focaltech_ft3683g.ko`, `richtap_haptic_hv.ko`.
4. Re-apply the binary patches:

   ```bash
   python3 tools/patch_adaptive_ts_ko.py \
     recovery/root/lib/modules/adaptive-ts.ko
   python3 tools/patch_haptic_ko.py \
     recovery/root/lib/modules/richtap_haptic_hv.ko
   ```

   `vendorsetup.sh` re-checks both automatically.
5. Re-append the three modules to `modules.load.recovery` and add the
   matching `modules.dep` / `modules.alias` entries. Do not rely on the
   stock recovery list including them.
6. Refresh touch/haptic firmware from the new `odm/firmware` and
   `vendor/firmware` if changed.
7. Verify:
   - every module in `modules.load.recovery` exists in the directory;
   - every dependency in `modules.dep` exists;
   - `modinfo -F vermagic` matches the stock kernel for all modules;
   - `prebuilt/dtb.img` still matches the new `vendor_boot` DTB; update it
     from the new image if the hash changed;
   - rebuild and inspect the ramdisk with `unpack_bootimg`.
8. Never mix modules from different firmware/kernel builds.

## Known validation gaps

The following still require X6855 hardware testing:

- Touch panel bring-up with the patched `adaptive-ts.ko`
- Haptics/vibration
- Charging and battery reporting
- FBE decryption
- USB OTG hotplug
- Fastbootd and slot switching
