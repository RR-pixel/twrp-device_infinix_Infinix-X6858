# TWRP for Infinix HOT 60 Pro+ (X6886)

Unofficial TWRP 16.0 recovery for the Infinix HOT 60 Pro+.

> [!WARNING]
> **Requires Android 16 firmware and a compatible 6.12 kernel.**
> Android 15 and older firmware are not supported.

## Device information

| Item | Details |
|---|---|
| Device | Infinix HOT 60 Pro+ |
| Codename | `Infinix-X6886` |
| SoC | MediaTek Helio G200 (MT6789) |
| Display | AMOLED, 1080x2400, 480 dpi |
| Partition layout | Virtual A/B with dynamic partitions |
| Recovery image | `vendor_boot.img` |
| Development branch | `twrp-16.0-tos16` |

## Working features

- Recovery boot
- Touchscreen
- Vibration
- USB OTG, including multi-partition drives and hotplug
- FBE decryption, including PIN/password-protected data
- Battery and charging status
- ADB and ADB sideload
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

Shared device support is maintained in the MT6789 common tree
(`device/transsion/mt6789-common`, branch `twrp-16.0-tos16`).

## Credits

- [Team Win Recovery Project](https://twrp.me)
- [OrangeFox Recovery Project](https://orangefox.download)
- MediaTek and Transsion for stock firmware components
- Maintainer: [rama982 / ramabondanp](https://github.com/ramabondanp)
