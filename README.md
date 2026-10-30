# AlphaWRT for the FiberHome SR1041Y

Port of [AlphaWRT](https://github.com/idiazraz/gn630v-alphawrt) (OpenWrt with
Quick Setup, ISP presets and Pi-hole) to the FiberHome SR1041Y, the GPON ONT +
Wi-Fi 6 router TM supplies with Unifi in Malaysia.

## Built on

This port stands on two projects, which are the main guides for it:

- **[AlphaWRT](https://github.com/idiazraz/gn630v-alphawrt)** by
  [idiazraz](https://github.com/idiazraz): the firmware itself, Quick Setup,
  ISP presets, Pi-hole, and the dual-bank GN630V port this one follows.
- **[Sirherobrine23's Airoha/EcoNet work](https://sirherobrine23.com.br/airoha)**
  ([tree](https://github.com/Sirherobrine23/openwrt),
  [openwrt/openwrt#20104](https://github.com/openwrt/openwrt/pull/20104)): the
  EN7523/EN7528 OpenWrt tree with the open xPON and OMCI stack that AlphaWRT
  builds on.

## Status

Early bring-up. AlphaWRT installs to flash bank B and boots from it, with the
stock firmware kept in bank A; upgrades go over LAN with `sysupgrade`. LAN,
Wi-Fi 6 (2.4 + 5 GHz), the web UI, Pi-hole and dnsproxy run on real hardware.
GPON (fibre) is not done yet. The first install needs the UART.

- [SR1041Y.md](SR1041Y.md): hardware, what works, changes to the tree, how to RAM-boot
- [BANK-FORMAT.md](BANK-FORMAT.md): stock flash banks and the free bootbase

| Path | |
|---|---|
| `en7528_fiberhome_sr1041y.dts` | device tree |
| `add_sr1041y.py` | adds the device to the `airoha/en7528` tree AlphaWRT builds on |
| `mk_uart_patch.sh` | generates the 8250 Airoha UART fix (kernel patch 888) |
| `sr1041y.config` | build config |
| `files/alphawrt-bootbank` | bank switching (installed into the image) |
| `tools/` | RAM boot over XMODEM, console, Wi-Fi test, bank-B install, flag records |
