# TWRP for Infinix GT 20 Pro (X6871)

Unofficial TWRP 16.0 device tree for the Infinix GT 20 Pro.

> [!WARNING]
> **Android 16 firmware with kernel 6.12 only.**
> Android 15 and older firmware are not supported.

## Device information

| Item | Details |
|---|---|
| Device | Infinix GT 20 Pro |
| Codename | `Infinix-X6871` |
| SoC | MediaTek Dimensity 8200 Ultimate (MT6895) |
| Partition layout | Virtual A/B with dynamic partitions |
| Recovery image | `vendor_boot.img` |
| Development branch | `twrp-16.0-tos16` |

## Working features

- Touchscreen
- FBE decryption through Trustonic TEE
- Battery and charging information
- ADB
- USB OTG
- A/B slot switching using the stock MTK AIDL boot HAL
- Normal Android boot alongside TWRP

## Building

Start with a configured TWRP 16.0 source tree on Linux.

Clone this repository from the source-tree root:

```bash
git clone --branch twrp-16.0-tos16 \
  https://github.com/ramabondanp/twrp-device_infinix_Infinix-X6871.git \
  device/infinix/Infinix-X6871
```

The device setup script fetches the
[MT6895 common tree](https://github.com/ramabondanp/twrp-device_transsion_mt6895-common/tree/twrp-16.0-tos16)
if missing and applies the required zstd, haptics, and repacking-safety patches.

Build the recovery image:

```bash
source build/envsetup.sh
lunch twrp_X6871
m vendorbootimage -j"$(nproc)"
```

Output:

```text
out/target/product/Infinix-X6871/vendor_boot.img
```

When replacing prebuilt binaries or removing packages, run
`m installclean` before rebuilding to avoid stale ramdisk files.

## Technical notes

- TWRP lives in the `vendor_boot` PLATFORM ramdisk, allowing Android and
  recovery to coexist while retaining the stock boot kernel.
- An empty RECOVERY fragment is intentional and required for the
  bootloader to enter recovery mode.
- In-recovery ramdisk repacking is disabled because it does not support
  this layout.
- The device uses virtual A/B updates and dynamic partitions.
- Slot switching uses the stock MTK AIDL boot HAL and is verified working.
- Battery reporting uses an AIDL health HAL.
- FBE decryption uses the Trustonic TEE stack.
- Recovery services run in the permissive SELinux `recovery` domain.

## Reporting issues

Please include:

- Your complete Android 16 firmware version
- The recovery build used
- Steps to reproduce the problem
- What you expected and what happened
- Recovery logs, where available

If ADB is available in recovery, capture logcat:

```bash
adb logcat -b all -d > recovery-log.txt
```

Also attach TWRP's recovery log using **Advanced → Copy Log**, if
accessible.

Review logs for personal information before sharing them.

## Credits and links

- [Team Win Recovery Project](https://twrp.me)
- [OrangeFox Recovery Project](https://orangefox.download)
- MediaTek and Transsion for stock firmware components
- Maintainer: [rama982 / ramabondanp](https://github.com/ramabondanp)

Repositories:

- [X6871 device tree](https://github.com/ramabondanp/twrp-device_infinix_Infinix-X6871)
- [MT6895 common tree](https://github.com/ramabondanp/twrp-device_transsion_mt6895-common)

## Disclaimer

This is an unofficial project. Using custom recovery carries a risk of
data loss or an unbootable device. Back up important data and proceed at
your own risk.
