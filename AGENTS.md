# AGENTS.md — Infinix X6871 / TWRP 16.0

Durable guidance for the Infinix GT 20 Pro (`Infinix-X6871`, MT6895).
Read before working on this device or its common tree.

## Anchor policy

- This is an anchor, not a changelog or a session journal. Edit it only
  when architecture, workflow, or persistent constraints change.
- The build server is disposable. Do not assume `out/`, `tmp/`, logs,
  stock dumps, credentials, or a particular workspace path will survive.
- Keep durable decisions in version control, not only in chat or scratch
  files. Do not add build hashes, dates, download links, test readings,
  or host-specific instructions here.
- Keep this file in the X6871 repository only. `README.md` is for humans;
  tracked configuration and source files define exact implementation details.

## Constraints

1. **Android 16 firmware / kernel 6.12 only.** Android 15 and older firmware
   are unsupported. Preserve both normal Android boot and recovery boot.
2. **Keep TWRP/build-system source changes as patches** under the device
   repositories' `patches/`, applied by `vendorsetup.sh`. Do not leave
   unrecorded source edits as the implementation of a fix.
3. **Use workspace-local `tmp/`, never `/tmp`,** for scratch work.
4. **Every commit subject must contain `twrp-16.0`.** Commit or push only
   when authorized; documentation changes do not imply that permission.
5. **Do not commit or push functional fixes before device confirmation.**
   A successful build alone is not hardware validation.
6. **Prefer fewer patches and AIDL over HIDL.** Avoid cleanup patches that
   do not solve a functional problem; this is not a blanket HIDL ban.
7. Recovery may run in the permissive `recovery` domain. No SELinux policy
   work is required for this setup; do not add global `setenforce 0`.
8. Preserve unrelated work. Do not reset, discard, or include it in commits.
   Rewrite published history only when explicitly requested, using a lease.

## Repositories and ownership

Both repositories use `twrp-16.0-tos16`. Keep `fox_12.1-tos15` as a backup.
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

- `init.recovery.mt6895.rc` and `init.tee.rc`: boot HAL and TEE startup.
- `first_stage_ramdisk/fstab.mt6895`: non-AVB first-stage fstab, including
  `tr_system`; distinct from `system/etc/recovery.fstab` used by TWRP.
- `system/etc/twrp.flags`: partition flags and USB OTG device preference.
- `system/etc/init/` and VINTF manifests: recovery service declarations.
- Stock boot HAL and Trustonic binaries, libraries, and registry files.

## Build and patches

Run from the source-tree root:

```bash
source build/envsetup.sh
lunch twrp_X6871
m vendorbootimage -j"$(nproc)"
```

Output: `out/target/product/Infinix-X6871/vendor_boot.img`.
Use `m installclean` before rebuilding after replacing prebuilts, removing
packages, or switching HAL implementations to avoid stale packaged files.

X6871's `vendorsetup.sh` fetches the common repository when absent and
applies these patches. If common already exists, verify its branch;
the script does not switch or update an existing checkout.

| Patch (relative to its repository) | Owner | Target |
|---|---|---|
| `patches/0001-Add-zstd-ramdisk-compression.patch` | Common | `build/make` |
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
- Android and TWRP share this image. Retain the stock `boot.img` kernel;
  this tree builds `vendor_boot`, not a replacement kernel.
- Preserve configured bootconfig, cmdline, DTB, ramdisk table, partition
  size, and AVB metadata when changing or repacking the image. Read exact
  values from `BoardConfigCommon.mk`, not from old build artifacts.
- The device is virtual A/B with dynamic partitions. `boot`, `vendor_boot`,
  and `dtbo` are slotted; logical system partitions live in `super`.
- USB OTG must prefer `/dev/block/sdd1`, then `/dev/block/sdd` as fallback.

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

### Encryption

- Preserve the matching Trustonic stack: `mcDriverDaemon`/`mobicore`,
  TEE service, gatekeeper, keymint, supporting libraries, and mcRegistry.
- `init.tee.rc` starts mobicore early; the
  `ro.vendor.trustonic.ready=true` trigger in `init.recovery.mt6895.rc`
  starts TEE, gatekeeper, and keymint services.
- FBE also depends on keystore2, Keymaster 4.1, secureclock/sharedsecret,
  the Trustonic properties in `system.prop`, and matching fstab crypto
  settings. Preserve fscrypt policy v2 and metadata key-directory setup.
- Diagnose failures across the startup chain and matching firmware
  components; do not treat a filesystem flag alone as the whole fix.

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
battery reporting, USB OTG, fastbootd, AIDL boot-service registration,
actual A/B slot switching, and normal Android boot with the same image.
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
