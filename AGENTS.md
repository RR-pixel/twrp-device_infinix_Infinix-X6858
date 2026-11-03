# AGENTS.md — Infinix X6871 / TWRP 16.0

Durable guidance for the Infinix GT 20 Pro (`Infinix-X6871`, MT6895).
Read before working on this device or its common tree.

## Anchor policy

- This is an anchor, not a changelog or a session journal. Edit it only
  when architecture, workflow, or persistent constraints change.
- The build server is disposable. Do not assume `out/`, `tmp/`, logs,
  stock dumps, credentials, or a particular workspace path will survive.
- Keep durable decisions in version control, not only in chat or scratch
  files. Do not add build hashes, dates, download links, or test readings
  here.
- Keep this file in the X6871 repository only. Keep `README.md` short and
  user-facing; put build and implementation guidance here.

## Constraints

1. **Android 16 firmware with a 6.12 kernel only.** Android 15 and older
   firmware are unsupported. Preserve both normal Android boot and recovery
   boot.
2. **Keep TWRP/build-system source changes as patches** under the device
   repositories' `patches/`, applied by `vendorsetup.sh`. Do not leave
   unrecorded source edits as the implementation of a fix.
3. **On ServerHive, use workspace-local `tmp/`, never `/tmp`,** for scratch
   work; the host does not allow writes to `/tmp`.
4. **Commit subjects use a double scope:**
   `<project>: twrp-16.0: <description>`. Keep the description lowercase
   except for acronyms and proper nouns. Example:
   `X6871: twrp-16.0: document USB OTG hotplug discovery`. Commit or push
   only when authorized; documentation changes do not imply that permission.
5. **Do not commit or push functional fixes before device confirmation.**
   A successful build alone is not hardware validation.
6. **Prefer fewer patches and AIDL over HIDL.** Avoid cleanup patches that
   do not solve a functional problem; this is not a blanket HIDL ban.
7. Recovery may run in the permissive `recovery` domain. No SELinux policy
   work is required for this setup; do not add global `setenforce 0`.
8. Preserve unrelated work. Do not reset, discard, or include it in commits.
   Rewrite published history only when explicitly requested, using a lease.

## Repositories and ownership

Both repositories use `twrp-16.0-tos16`. Keep the `fox_12.1-tos15` branch
as a backup.
Paths below are relative to the Android source-tree root, which contains
multiple Git repositories rather than one workspace-wide repository.

| Tree | Local path | Repository |
|---|---|---|
| X6871 | `device/infinix/Infinix-X6871` | https://github.com/ramabondanp/twrp-device_infinix_Infinix-X6871 |
| Common | `device/transsion/mt6895-common` | https://github.com/ramabondanp/twrp-device_transsion_mt6895-common |

X6871 owns product configuration, `vendorsetup.sh`, the DTB in `prebuilt/`,
kernel modules in `recovery/root/lib/modules/`, and device init overrides.
Keep the DTB and modules compatible with the target stock firmware/kernel.

Common owns shared boot layout, brightness and crypto configuration
(`BoardConfigCommon.mk`), packages (`common.mk`), and recovery root files:

- `init.recovery.mt6895.rc` and `init.tee.rc`: boot HAL and TEE startup,
  plus the RichTap firmware preload.
- `first_stage_ramdisk/fstab.mt6895`: non-AVB first-stage fstab, including
  `tr_system`; distinct from `system/etc/recovery.fstab` used by TWRP.
- `system/etc/twrp.flags`: partition flags and removable-storage settings.
- `system/etc/init/` and VINTF manifests: recovery service declarations.
- Stock boot HAL and Trustonic binaries, libraries, and registry files.

## Build and patches

Run from the source-tree root:

```bash
source build/envsetup.sh
lunch twrp_X6871
m vendorbootimage
```

Output: `out/target/product/Infinix-X6871/vendor_boot.img`.
Use `m installclean` before rebuilding after replacing prebuilts, removing
packages, or switching HAL implementations to avoid stale packaged files.

### ServerHive

Build on the ServerHive host (`ssh waffle`) in a login shell inside a
persistent tmux or byobu session. The login shell provides the RBE
environment. Do not override `CUSTOM_NINJA_BIN`, `USE_RBE`, or `NINJA_ARGS`,
and do not pass `-j`; RBE controls parallelism.

```bash
ssh waffle
tmux new-session -s twrp-build
bash -l
cd ~/twrp-16.0
source build/envsetup.sh
lunch twrp_X6871
m vendorbootimage
```

Use `~/twrp-16.0/tmp/` for scratch files. Do not write to `/tmp`.

X6871's `vendorsetup.sh` fetches the common repository when absent and
applies these patches. If common already exists, verify its branch;
the script does not switch or update an existing checkout.

| Patch (relative to its repository) | Owner | Target |
|---|---|---|
| `patches/0001-Add-zstd-ramdisk-compression.patch` | Common | `build/make` |
| `patches/0002-Respect-disabled-repacking.patch` | Common | `bootable/recovery` |
| `patches/0003-Refresh-removable-partitions-after-uevent.patch` | Common | `bootable/recovery` |
| `patches/0001-Change-haptics-activation-file-path.patch` | X6871 | `bootable/recovery` |

A patch error is not automatically harmless. Check forward application
with `git apply --check` and reverse application with
`git apply --reverse --check`, from the target repository with the correct
patch path. Distinguish an already-applied patch from a real conflict.

Applied patches intentionally make `build/make` and `bootable/recovery`
dirty. Check their diffs before changing anything; do not commit the
applied copies upstream or discard unrelated edits.

## Architecture decisions

### Boot image and partitions

- Use header-v4 `vendor_boot` with a zstd PLATFORM ramdisk (`0x1`)
  containing all recovery files, plus an empty RECOVERY fragment (`0x2`)
  named `emptyrecovery` from common's `prebuilt/empty_recovery.cpio.zst`.
- The empty fragment is required for the bootloader to enter recovery.
  Preserve it; do not move the recovery payload into that fragment.
- Android and TWRP share this image. Retain the existing compatible
  `boot.img` kernel; this tree builds `vendor_boot`, not a replacement kernel.
- Bundled repacking is disabled: its recovery-fragment assumptions and
  compression support do not match this layout. Build and flash complete
  images instead; do not re-enable repacking without layout-aware support.
- Preserve configured bootconfig, cmdline, DTB, ramdisk table, partition
  size, and AVB metadata when changing or repacking the image. Read exact
  values from `BoardConfigCommon.mk`, not from old build artifacts.
- The device is virtual A/B with dynamic partitions. `boot`, `vendor_boot`,
  and `dtbo` are slotted; logical system partitions live in `super`.
- USB OTG is discovered through the v2 xHCI sysfs entry in common's
  `recovery.fstab`; do not pin it to a static `/dev/block/sddN`. The
  `/usbotg` parent is a placeholder; real partitions are `/usbotg-N`.

### Boot and health HALs

- Use the **stock MTK AIDL boot HAL prebuilt**:
  `system/bin/hw/android.hardware.boot-service.mtk_recovery`, with
  `system/lib64/libmtk_bsg.so`, its init rc, and its VINTF declaration.
- `init.recovery.mt6895.rc` starts `vendor.boot-default`, registering
  `android.hardware.boot.IBootControl/default`. It runs as root in the
  `recovery` domain. Actual A/B slot switching is verified working.
- Use `android.hardware.health-service.example_recovery` from `common.mk`.
  Its device-tree rc overlay runs as root/group root in the `recovery`
  domain so it can report real battery information.

### USB OTG hotplug

The xHCI host typically exposes a plugged drive as `sdd`. Common's
`recovery.fstab` carries a v2 sysfs entry for it:

```
/devices/platform/soc/11201000.usb0/11200000.xhci*  /usbotg  auto  ...
```

Keep the sysfs path. A static `/dev/block/sddN` entry is evaluated only when
the fstab is parsed and is not refreshed when the drive is plugged in later.

TWRP can receive the disk-add event before the partition nodes exist, and a
partition event that arrives first has no block device to resolve. Keep
common's `patches/0003-Refresh-removable-partitions-after-uevent.patch`
applied by `vendorsetup.sh`; it reconciles removable sysfs parents after each
uevent burst and creates or removes the child partitions.

The entire burst can also finish before `ueventd` creates `/dev/block` nodes.
Keep the bounded delayed retries on the background storage worker: after
block add/change or socket-loss events, it retries discovery on the existing
snapshot ticks and publishes the reconciled lists. A single immediate scan
can miss the node and wait for an unrelated battery event. Do not replace
the retries with GUI-thread sleeps or continuous idle sysfs polling.

Measure hotplug latency without `strace`/`ptrace` attached; tracing can alter
event timing and mask the device-node race.

The `/usbotg` entry is a placeholder parent, not a mountable filesystem. Real
partitions appear as `/usbotg-1`, `/usbotg-2`, ... and are labeled `OTG 1`,
`OTG 2`, ...; numbering follows discovery order, so do not assume `sdd1`
is `OTG 1`.

### Encryption

- Preserve the matching Trustonic stack: `mcDriverDaemon`/`mobicore`,
  TEE service, gatekeeper, keymint, supporting libraries, and mcRegistry.
- `init.tee.rc` starts mobicore only after `twrp.storage.ready=1`.
  `init.recovery.mt6895.rc` requires both storage readiness and
  `ro.vendor.trustonic.ready=true` before starting TEE, gatekeeper, and
  keymint. Keep these services disabled for class-based startup: early
  startup can attach them to temporary `/vendor` mounts, causing unmount
  cleanup to kill them and leave keystore2 with a dead KeyMint connection.
- FBE also depends on keystore2, Keymaster 4.1, secureclock/sharedsecret,
  the Trustonic properties in `system.prop`, and matching fstab crypto
  settings. Preserve fscrypt policy v2 and metadata key-directory setup.
- Diagnose failures across the startup chain and matching firmware
  components; do not treat a filesystem flag alone as the whole fix.

### Haptics / RichTap vibrator

The haptic amplifier is an AWINIC RichTap part on i2c (`haptic_hv@5A`,
`tran_richtap_haptic_hv.ko`), not the MTK `regulator-vibrator` LED. The
`vibrator` LED only toggles a rail and produces no feedback on this board.

Stock module behavior: `init_module` builds a boot-mode skip mask with
`mov w9, #0x304` and does not call `i2c_add_driver` for modes 2, 8 and 9.
Recovery reports mode 2, so the module loads but never binds; `haptic_hv@5A`
has no driver and `/sys/class/leds/vibrator_single` never appears. TWRP then
falls through its other haptics candidates and stays silent.

Every packaged copy of the module must be patched before installation:

```bash
python3 tools/patch_haptic_ko.py \
  recovery/root/lib/modules/tran_richtap_haptic_hv.ko
```

The script rewrites the mask immediate to `0x300`, requires a unique
instruction signature, and is idempotent (`--check` reports state without
writing). Re-run it **whenever the module is replaced from a new stock dump**:
the prebuilt is a binary blob, and a plain copy silently reintroduces the
bug. If the signature is not found, disassemble `init_module` with
`llvm-objdump` and re-derive the mask rather than patching a raw offset.

Successful registration in recovery shows:

- `dmesg`: `aw_i2c_probe: probe completed successfully!`
- `/sys/class/leds/vibrator_single/` exposing `duration` and `activate`
- haptic feedback on button, keyboard and action input

Do **not** `rmmod` this module on a running device: its cleanup path panics
the kernel when the driver was never registered. Rebuild and flash the image.

The TWRP side is `patches/0001-Change-haptics-activation-file-path.patch`
(target `bootable/recovery`). It probes `vibrator_single` duration/activate,
then the generic `vibrator` LED pair, then `timed_output`, then a
`vibrator/brightness` pulse, then evdev force feedback.

The driver also defers its `haptic_ram.bin` load: `ram_work_init()` queues
the work for 2000 jiffies (8 s at HZ=250) after probe. TWRP is interactive
before then, and `activate_store` rejects early writes with
`ram init failed, not allow to play!`. Common's `init.recovery.mt6895.rc`
writes `1` to `/sys/class/leds/vibrator_single/ram_update` when
`sys.boot_completed` is set, loading the firmware in about 200 ms. Keep
that trigger: without it, the first several seconds of touches are silent.

### Touchscreen / adaptive-ts

`adaptive-ts.ko` is the Transsion touch panel driver. Its
`mtk_get_boot_mode()` returns 2 for boot modes 1/4/6 and 1 for modes
2/8/9; recovery reports mode 2, so the driver takes its recovery path and
never probes the panel. TWRP then boots with a working display but no
touch. Both returns are `mov w0` immediates in one contiguous block.

Every packaged copy of the module must be patched to return 0 on both
paths:

```bash
python3 tools/patch_adaptive_ts_ko.py \
  recovery/root/lib/modules/adaptive-ts.ko
```

The script matches the whole return block, requires a unique signature,
and is idempotent (`--check` reports state without writing). Re-run it
**whenever the module is replaced from a new stock dump**: the prebuilt is
a binary blob, and a plain copy silently reintroduces the bug. If the
signature is not found, disassemble `mtk_get_boot_mode` with
`llvm-objdump` and re-derive the returns rather than patching a raw
offset.

## Rejected approaches

- **Single-slot fallback:** virtual A/B does not mean a single boot slot.
  Reporting one slot or hardcoding `_a` hides real A/B state and breaks
  switching. Do not infer the running slot from priority alone.
- **Previous source boot HAL:** its AIDL wrapper aborted at
  `CHECK(impl_.Init())` with a backend requiring `ro.boot.slot_suffix`,
  leaving TWRP at the splash. It was removed in favor of the working stock
  prebuilt. This is not a known limitation of the stock HAL.
- **Assumed replacement logic:** do not prescribe a BCB fallback or treat
  preliminary disassembly as a complete specification. A future source
  HAL needs evidence for current/active slot semantics, MTK boot-region
  handling, and snapshot state, followed by hardware validation.
- **HIDL-removal cleanup patch:** deliberately dropped. The HIDL boot
  service binaries can remain packaged with `disabled` rc files. Do not
  explicitly start them; use the stock AIDL boot service instead.

## Verified baseline and validation

Established capabilities: recovery boot, touch, FBE decryption, real
battery reporting, USB OTG hotplug, fastbootd, AIDL boot-service
registration, actual A/B slot switching, RichTap haptics with the patched
module, and normal Android boot with the same image.
This is a baseline, not proof that a new build preserves those features.

Before calling a functional change ready:

1. Build successfully and inspect the packaged ramdisk, not only the source
   tree. Check required HAL binaries, dependencies, rc files, and manifests.
2. Verify the two-entry ramdisk layout and AVB using the tree's boot-image
   tools. For the built image:

   ```bash
   out/host/linux-x86/bin/avbtool verify_image \
     --image out/target/product/Infinix-X6871/vendor_boot.img
   ```

3. Obtain hardware confirmation for affected features. Boot-affecting
   changes must test both recovery and normal Android boot; HAL/crypto
   changes must also retest the relevant slot, battery, or decryption path.
4. Coordinate slot-switch and flashing tests with the user; do not change
   a connected device's boot state without authorization.
5. Investigate crashes or startup failures with recovery logs and logcat.
   `permissive=1` AVCs are not enforced denials, but do not dismiss actual
   service failures just because SELinux is permissive.

Missing stock dumps or outputs must be obtained again from matching
firmware or rebuilt. Do not make a reproducible fix depend on files that
only exist on the disposable server.
