# TWRP for Infinix GT 20 Pro (X6871)

Unofficial TWRP 16.0 recovery for the Infinix GT 20 Pro.

> [!WARNING]
> **Requires Android 16 firmware and a compatible 6.12 kernel.**
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

- Touchscreen and vibration
- Data decryption (FBE)
- Battery and charging status
- ADB
- USB OTG, including drives with multiple partitions
- Fastbootd and A/B slot switching
- Normal Android boot alongside TWRP

## Reporting issues

Please include your firmware and kernel versions, the recovery build you
used, and steps to reproduce the problem.

Use **Advanced → Export logs** to save recovery logs. Review them for
personal information before sharing.

## Development

Build instructions and development notes are in [AGENTS.md](AGENTS.md),
which is written primarily for AI coding agents.

Shared device support is maintained in the
[MT6895 common tree](https://github.com/ramabondanp/twrp-device_transsion_mt6895-common/tree/twrp-16.0-tos16).

## Credits

- [Team Win Recovery Project](https://twrp.me)
- [OrangeFox Recovery Project](https://orangefox.download)
- MediaTek and Transsion for stock firmware components
- Maintainer: [rama982 / ramabondanp](https://github.com/ramabondanp)
