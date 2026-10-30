#!/bin/bash
# Generate 888-serial-8250-airoha-program-XYD-after-the-divisor.patch for the
# airoha tree from its already-patched kernel source. Usage: sh mk_uart_patch.sh <tree>
set -eu
TREE=$1
S=$(ls -d "$TREE"/build_dir/target-mipsel_24kc_musl/linux-airoha_en7528/linux-*/ | head -1)
S=${S%/}
W=$(mktemp -d)
mkdir -p "$W/a/drivers/tty/serial/8250" "$W/b/drivers/tty/serial/8250"
cp "$S/drivers/tty/serial/8250/8250_port.c" "$W/a/drivers/tty/serial/8250/"

python3 - "$W" <<'EOF'
import sys
w = sys.argv[1]
s = open(w + "/a/drivers/tty/serial/8250/8250_port.c").read()
old = """#ifdef CONFIG_SERIAL_8250_AIROHA
	/* Airoha SoCs have custom registers for baud rate settings */
	if (port->type == PORT_AIROHA)
		en7523_set_uart_baud_rate(port, baud);
#endif

"""
assert s.count(old) == 1, "airoha hunk not found exactly once"
s = s.replace(old, "", 1)
anchor = "\t\tserial8250_set_divisor(port, baud, quot, frac);\n"
assert s.count(anchor) == 1, "set_divisor anchor not found exactly once"
s = s.replace(anchor, anchor + """#ifdef CONFIG_SERIAL_8250_AIROHA
		/* Airoha SoCs have custom registers for baud rate settings */
		if (port->type == PORT_AIROHA)
			en7523_set_uart_baud_rate(port, baud);
#endif
""", 1)
open(w + "/b/drivers/tty/serial/8250/8250_port.c", "w").write(s)
EOF

P="$TREE/target/linux/airoha/patches-6.18/888-serial-8250-airoha-program-XYD-after-the-divisor.patch"
{
	cat <<'HDR'
Subject: [PATCH] serial: 8250: airoha: program XYD after the divisor

en7523_set_uart_baud_rate() forces BRD to 1 and programs the XYD and
XINCLKDR registers. Calling it before serial8250_set_divisor() lets the
generic divisor overwrite BRD, so any uartclk other than 16 * baud gives a
wrong rate: on the FiberHome SR1041Y (free bootbase, 7.3728 MHz uartclk)
the console turned to NULs at handover. Call it after the divisor, inside
the port lock, as mainline Linux and OpenWrt's econet target do.

HDR
	cd "$W" && diff -u a/drivers/tty/serial/8250/8250_port.c b/drivers/tty/serial/8250/8250_port.c || true
} > "$P"
rm -rf "$W"
echo "wrote $P ($(grep -c '^[-+][^-+]' "$P") changed lines)"
