# Raspberry Pi checklist: find the Pi 3, or buy a Pi 5 set

One page to tick off. Status: draft. No prices are listed and none are confirmed; check the seller's page on the day.
Items marked "(to verify)" come from general knowledge or a seller page that was not fully readable.

## Step 1: find the Pi 3 Model B

- [x] Found: a Raspberry Pi 3 in a black two-part case, base off, board visible through the cut-outs (`images/frugalai-rpi3_with_cover.jpg`). The SoC marking is consistent with a Pi 3 Model B.
- [ ] Free the board from the case shell. Work with the Pi unplugged and no card powered. Look for the small clips along the long sides and at the corners; release them one at a time with a fingernail or a plastic opening tool, pulling gently on the shell, never near the ports or ribbon sockets. If it will not release, stop: the Pi can stay in the shell for every use except reading the underside.
- [ ] Photograph the bare board top-down and from the underside (the microSD slot is underneath). Save the photos in `images/`.
- [ ] Read the text printed on the board and note the model and revision (Model B or B+).
- [ ] Check whether a microSD card is in the slot. If one is, do not boot from it until you know what it holds.

## Step 2: if the Pi 3 is found, what to add

Already in the kit: CanaKit 2.5 A power supply, micro-USB cable, HDMI cable, Ethernet cable, a USB webcam
(not yet tested on the Pi). See [hardware-kit.md](hardware-kit.md).

- [ ] microSD card reader for the laptop (probably owned; confirm)
- [x] Case that exposes the camera (CSI) port: the black case already shows the CSI and DSI sockets. Check that a ribbon cable fits through the gap with the case closed (to verify).
- [ ] Heatsinks: check first whether a small heatsink fits the chip window of the case (to verify)
- [ ] Optional: CSI Camera Module 3 (should fit the Pi 3 with its own 15-pin cable, to verify), only if the USB webcam is not enough
- [ ] Optional: USB power bank, 5 V and at least 2.5 A, for a demo away from a wall socket

## Step 3: a Pi 5 set (not needed now that the Pi 3 is found)

Kept for the later upgrade. The Pi 5 has different ports from the Pi 3, so the old cables do not all fit.

- [ ] Raspberry Pi 5 board (4 GB or 8 GB: decide before ordering)
- [ ] Official 27 W USB-C power supply (to verify the exact model on the seller page)
- [ ] Active Cooler (official)
- [ ] Case with camera access; confirm that the case and the Active Cooler fit together (to verify)
- [ ] microSD card, A2 rated, 32 to 64 GB, bought sealed from a brand store or an approved reseller
- [ ] Micro-HDMI to HDMI cable (the kit HDMI cable is full size, so it will not fit the Pi 5)
- [ ] Only for a CSI camera: a 22-pin to 15-pin camera cable, because the Pi 5 has the smaller camera socket
- [ ] Optional: Camera Module 3; the USB webcam also works without any cable

## Before you pay

- [ ] The seller is on the official reseller list: <https://www.raspberrypi.com/resellers/> (the list has no country labels; Robu and Robocraze are on it)
- [ ] The listing is in stock and shows the exact kit contents, with wattage of the power supply and size of the SD card
- [ ] The price includes GST, and you get a GST invoice
- [ ] Return or replacement terms are stated
- [ ] The board is sealed and original (not a lookalike board)

## Where to look

| Seller | Link | Notes |
|---|---|---|
| Official reseller list | <https://www.raspberrypi.com/resellers/> | Check every seller here first. |
| Robu | <https://robu.in/product-category/microcontroller-development-board/raspberry-pi-microcontroller-development-board/official-boards-and-accessories/> | On the official list. The page blocks automated reading, so open it in a browser. |
| Robocraze | <https://robocraze.com/collections/raspberry-pi> | On the official list. Pi 5 starter kits were sold out when read: [8 GB kit](https://robocraze.com/products/official-raspberry-pi-5-8gb-starter-kit), [4 GB kit](https://robocraze.com/products/official-raspberry-pi-5-4gb-starter-kit). The kit contents were not readable. |
| Thingbits | <https://www.thingbits.in/products/raspberry-pi-5-camera-cable-22-pin-to-15-pin> | Camera cable only. Not on the official list, to verify. |

ThinkRobotics and Zbotic were not found on the official list. That does not prove they are not genuine; ask for proof of
authorised supply before buying a board from them.
