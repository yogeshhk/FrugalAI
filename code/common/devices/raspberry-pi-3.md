# Raspberry Pi 3 Model B (the kit's edge device)

Status: found, not yet booted or benchmarked. No number below is measured; every spec is from general knowledge and
tagged "(to verify)" until a script or the board's own printout confirms it.

## Hardware to record before benchmarking
Photo: `docs/images/frugalai-rpi3_with_cover.jpg` (black case, base off). Fill in from the bare board and from
`cat /proc/cpuinfo`, `cat /proc/device-tree/model`, `free -h` and `vcgencmd get_throttled` once it runs.

| Item | Value |
|------|-------|
| Model and revision | Pi 3 Model B from the SoC marking (BCM2837); confirm the revision text on the board |
| CPU | quad-core 64-bit ARM Cortex-A53, 1.2 GHz (kit sheet; to verify) |
| RAM | 1 GB (to verify) |
| Network | WiFi 802.11n, Bluetooth 4.1, 100 Mbit Ethernet (kit sheet; to verify) |
| Ports | 40-pin GPIO, 4 USB, full-size HDMI, 3.5 mm A/V, CSI camera, DSI display, microSD (seen in the photo) |
| Case | black two-part case, CSI and DSI sockets exposed (official style, to verify) |
| Storage | microSD; the CanaKit box note says a 32 GB card came with it; not yet checked in the slot |
| Power | CanaKit 2.5 A supply, micro-USB |
| OS and version | to fill in |

## Limits that shape every recipe
- 1 GB RAM: the Dhir 2B GGUF (about 1.3 GB at 4-bit) does not fit; expect models well under 1 GB, low image
  resolution and few frames per second. Frame rate stays "pending" until measured.
- Heat: the Pi 3 can throttle under sustained load (to verify). Log `vcgencmd get_throttled` and temperature in every run.
- Power: an under-rated supply or cable also throttles. Use the 2.5 A supply.
- Conda is not practical on a Pi 3 (to verify); each recipe documents its own environment.

## Setup checklist
1. Photograph the bare board and read its revision (see `docs/pi-checklist.md`). Check the microSD slot first.
2. Flash a 64-bit Raspberry Pi OS Lite with the official imager on a fresh card, enable SSH, set WiFi, change the default password.
3. Boot headless over Ethernet, update packages, record OS and kernel versions in the table above.
4. Plug in the USB webcam (kit webcam is untested; a second webcam worked on the laptop at low resolution) or a CSI camera.
5. Run the laptop-proven recipe, then log the first benchmark row with `--device raspberry-pi-3`.

Recipes: `code/gesture-switch/` first. Follow [benchmarks/METHODOLOGY.md](../benchmarks/METHODOLOGY.md).
