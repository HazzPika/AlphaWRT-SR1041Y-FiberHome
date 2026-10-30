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
  DEVICE_PACKAGES := kmod-usb3 kmod-mt7915e kmod-mt7915-firmware
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

patch("en7528/base-files/etc/board.d/02_network", "\tjiofiber,jcow407|\\",
      "\tfiberhome,sr1041y|\\\n", "\tfiberhome,sr1041y|\\")

patch("en7528/base-files/etc/board.d/02_network",
      "\thuawei,hg2821t-u)\n\t\tlocal conffile",
"""\tfiberhome,sr1041y)
		lan_mac=$(get_mac_sr1041y brmac)
		[ -n "$lan_mac" ] && label_mac="$(macaddr_add $lan_mac -1)"
		;;
""", "lan_mac=$(get_mac_sr1041y brmac)")

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
	mkdir -p /tmp/factory
	mount -t ubifs -o ro ubi:factory /tmp/factory
}

""", "preinit_mount_factory_ubifs()")

patch("base-files/lib/preinit/09_mount_factory_data",
      "\thuawei,hg2821t-u)\n\t\tpreinit_mount_factory_data configuration_a",
"""\tfiberhome,sr1041y)
		preinit_mount_factory_ubifs
		;;
""", "\tfiberhome,sr1041y)\n\t\tpreinit_mount_factory_ubifs")

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
