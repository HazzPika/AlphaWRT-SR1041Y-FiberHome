# AlphaWRT for the FiberHome SR1041Y

Port of [AlphaWRT](https://github.com/idiazraz/gn630v-alphawrt) (OpenWrt with
Quick Setup, ISP presets and Pi-hole) to the FiberHome SR1041Y, the GPON ONT +
Wi-Fi 6 router TM supplies with Unifi in Malaysia.

**Status:** early bring-up, RAM boot only. LAN, Wi-Fi 6 (2.4 + 5 GHz), the
web UI, Pi-hole and dnsproxy run on real hardware. GPON and installing to
flash are not done yet.

- [SR1041Y.md](SR1041Y.md): hardware, what works, changes to the tree, how to RAM-boot
- [BANK-FORMAT.md](BANK-FORMAT.md): stock flash banks and the free bootbase

| Path | |
|---|---|
| `en7528_fiberhome_sr1041y.dts` | device tree |
| `add_sr1041y.py` | adds the device to the `airoha/en7528` tree AlphaWRT builds on |
| `mk_uart_patch.sh` | generates the 8250 Airoha UART fix (kernel patch 888) |
| `sr1041y.config` | build config |
| `tools/` | UART tools: RAM boot over XMODEM, console, Wi-Fi test |
