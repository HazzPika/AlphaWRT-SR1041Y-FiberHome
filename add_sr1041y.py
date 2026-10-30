#!/usr/bin/env python3
"""Add FiberHome SR1041Y to the airoha/en7528 tree AlphaWRT builds on.

Idempotent. Usage: python3 add_sr1041y.py <tree>
"""
import pathlib, shutil, sys

here = pathlib.Path(__file__).resolve().parent
tree = pathlib.Path(sys.argv[1])
air = tree / "target/linux/airoha"


def patch(rel, anchor, insert, marker):
    p = air / rel
    s = p.read_text()
    if marker in s:
        print(f"skip  {rel}")
        return
    if anchor not in s:
        sys.exit(f"anchor not found in {rel}: {anchor!r}")
    p.write_text(s.replace(anchor, insert + anchor, 1))
    print(f"patch {rel}")


def write(rel, text):
    p = air / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists() and p.read_text() == text:
        print(f"skip  {rel}")
        return
    p.write_text(text)
    print(f"write {rel}")


shutil.copy(here / "en7528_fiberhome_sr1041y.dts", air / "dts")
print("copy  dts/en7528_fiberhome_sr1041y.dts")

patch("image/en7528.mk", "define Device/jiofiber_en7528",
"""define Device/fiberhome_sr1041y
  $(call Device/tclinux-ubi)
  DEVICE_VENDOR := FiberHome
  DEVICE_MODEL := SR1041Y
  DEVICE_DTS := en7528_fiberhome_sr1041y
  FACTORY_SIZE := 40m
  TRX_LOADADDR := 0x80002000
  KERNEL := kernel-bin | append-dtb | tclinux-free-bootbase-jump | lzma | \\
    kernel-trx
  DEVICE_PACKAGES := kmod-usb3 kmod-mt7915e kmod-mt7915-firmware \\
	wpad-mbedtls iw -wpad-basic-mbedtls kmod-usb-ledtrig-usbport
endef
TARGET_DEVICES += fiberhome_sr1041y

""", "define Device/fiberhome_sr1041y")

patch("base-files/lib/functions/econet.sh", "get_mac_gs3101() {",
"""# FiberHome SR1041Y keeps its MACs in factory_conf on the UBIFS "factory"
# volume (mounted by 79_sr1041y_factory), as uci-like
# "config key '<name>'" / "option value '<mac>'" pairs.
get_mac_sr1041y() {
	local conffile="/tmp/factory/factory_conf"

	[ -f "$conffile" ] || return
	awk -v k="$1" '
		$1 == "config" && $2 == "key" { cur = $3; gsub("\\047", "", cur); next }
		cur == k && $1 == "option" && $2 == "value" {
			v = $3; gsub("\\047", "", v); print tolower(v); exit
		}' "$conffile"
}

""", "get_mac_sr1041y()")

# A router, not an ONT: port 1 is the WAN port
patch("en7528/base-files/etc/board.d/02_network", "\ttplink,xc220-g3v)\n",
"""\tfiberhome,sr1041y)
		# a router, not an ONT: port 1 is the WAN port
		ucidef_set_interfaces_lan_wan "lan2 lan3 lan4" "lan1"
		;;
""", "\tfiberhome,sr1041y)\n\t\t# a router")

patch("en7528/base-files/etc/board.d/02_network",
      "\thuawei,hg2821t-u)\n\t\tlocal conffile",
"""\tfiberhome,sr1041y)
		lan_mac=$(get_mac_sr1041y brmac)
		wan_mac=$(get_mac_sr1041y internetmac)
		[ -n "$lan_mac" ] && label_mac="$(macaddr_add $lan_mac -1)"
		;;
""", "lan_mac=$(get_mac_sr1041y brmac)")

# USB LED: on while something is plugged into the USB port (the iPhone
# showed up on usb1-port2; usb2-port1 is the SuperSpeed side)
patch("en7528/base-files/etc/board.d/01_leds", "  tplink,xc220-g3v)\n",
"""  fiberhome,sr1041y)
    ucidef_set_led_usbport "usb" "USB" "green:usb" usb1-port1 usb1-port2 usb2-port1
    ;;
""", "  fiberhome,sr1041y)")

# No fibre: AlphaWRT's pages offer router mode only (alphawrt.board.fibre)
write("en7528/base-files/etc/uci-defaults/05_alphawrt_board", """#!/bin/sh
# Boards with no fibre: AlphaWRT's pages offer router mode only, with the
# Internet on the board's WAN port

. /lib/functions.sh

case "$(board_name)" in
fiberhome,sr1041y)
	uci -q batch <<EOF
set alphawrt.board=board
set alphawrt.board.fibre=0
set alphawrt.board.wan_port=lan1
set alphawrt.setup.mode=router
set alphawrt.setup.port=lan1
commit alphawrt
EOF
	;;
esac

exit 0
""")
(air / "en7528/base-files/etc/uci-defaults/05_alphawrt_board").chmod(0o755)

patch("base-files/etc/hotplug.d/ieee80211/10_fix_wifi_mac", "huawei,hg2821t-u)",
"""fiberhome,sr1041y)
	mac=$(get_mac_sr1041y brmac)
	[ -n "$mac" ] && echo "$(macaddr_add $mac $((PHYNBR + 2)))" > /sys${DEVPATH}/macaddress
	;;
""", "fiberhome,sr1041y)\n\tmac=$(get_mac_sr1041y brmac)")

# Must run before 70_initramfs_test, which ends preinit_main on RAM boots.
patch("base-files/lib/preinit/09_mount_factory_data", "preinit_mount_factory_partitions() {",
"""# FiberHome SR1041Y: the MACs and the Wi-Fi calibration are files in the UBIFS
# volume "factory" on the stock "config" UBI. The kernel attaches "config"
# itself (linux,ubi in DTS), read-only because the partition is read-only, so
# nothing here can write to flash.
preinit_mount_factory_ubifs() {
	local idx=$(find_mtd_index config) d

	# "ubi:NAME" only looks at ubi0, which is the system's own UBI once
	# AlphaWRT boots from flash: mount through the device "config" sits on
	for d in /sys/class/ubi/ubi[0-9]*; do
		[ "$(cat "$d/mtd_num" 2>/dev/null)" = "$idx" ] || continue
		mkdir -p /tmp/factory
		mount -t ubifs -o ro "${d##*/}:factory" /tmp/factory
		return
	done
}

""", "preinit_mount_factory_ubifs()")

patch("base-files/lib/preinit/09_mount_factory_data",
      "\thuawei,hg2821t-u)\n\t\tpreinit_mount_factory_data configuration_a",
"""\tfiberhome,sr1041y)
		preinit_mount_factory_ubifs
		;;
""", "\tfiberhome,sr1041y)\n\t\tpreinit_mount_factory_ubifs")

patch("en7528/base-files/lib/upgrade/platform.sh", "  tplink,xc220-g3v)",
"""  fiberhome,sr1041y)
    # AlphaWRT lives in bank B. The free bootbase loads the kernel trx from
    # UBI volume ID 0 of the bank; create it static with that ID, as stock
    # does, rather than letting nand.sh make a dynamic one.
    CI_UBIPART="KernelB"
    CI_KERNPART="ubi_kernel"
    ubimkvol() {
      case " $* " in
      *" -N ubi_kernel "*) command ubimkvol "$@" -n 0 -t static ;;
      *) command ubimkvol "$@" ;;
      esac
    }
    nand_do_upgrade "$1"
    ;;
""", "  fiberhome,sr1041y)")

bb = air / "en7528/base-files/usr/sbin/alphawrt-bootbank"
write("en7528/base-files/usr/sbin/alphawrt-bootbank", (here / "files/alphawrt-bootbank").read_text())
bb.chmod(0o755)

write("en7528/base-files/lib/preinit/79_sr1041y_factory", r'''# FiberHome SR1041Y: copy the Wi-Fi calibration out of the "factory" volume,
# which 09_mount_factory_data mounts read-only at /tmp/factory.

# Named to match the Wi-Fi node's "mediatek,eeprom-name", so mt76 loads it as
# its OF EEPROM. Needs a writable /lib/firmware: after mount_root for
# squashfs + overlay, or on the initramfs root.
sr1041y_place_wifi_eeprom() {
	local src=/tmp/factory/wlan/RT30xxEEPROM_5.bin
	local dst=/lib/firmware/mediatek/mt7915_eeprom_sr1041y.bin

	[ "$(board_name)" = "fiberhome,sr1041y" ] || return
	[ -f "$src" ] || return
	[ -f "$dst" ] && return
	mkdir -p "${dst%/*}"
	cp "$src" "$dst"
}

boot_hook_add preinit_mount_root sr1041y_place_wifi_eeprom
boot_hook_add initramfs sr1041y_place_wifi_eeprom
''')
