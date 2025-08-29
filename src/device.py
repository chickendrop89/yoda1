# A tool to grab weight data transmitted from a yoda1 bluetooth scale
# Copyright (C) 2025 chickendrop89
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import asyncio
import logging
import struct

from bleak import BleakScanner, BLEDevice
from bleak.backends.scanner import AdvertisementData
from src.parse import parse_scale_data, ScaleData

logger = logging.getLogger(__name__)

# Bluetooth MAC address prefix for CHIPSEA TECHNOLOGIES (Yoda1 MCU)
YODA_MAC_PREFIX = "50:FB:19"

def _parse_device_data(advertisement_data: AdvertisementData) -> ScaleData:
    """Helper to parse raw advertisement data into scale data."""

    try:
        # Get manufacturer-specific data
        mf_data = advertisement_data.manufacturer_data
        if not mf_data:
            return None

        # Extract the bytes from the first entry
        variant = next(iter(mf_data.values()), None)
        if not variant:
            return None

        return parse_scale_data(variant)
    except struct.error as e:
        logger.error("Error parsing advertisement data: %s", e)
        return None


class YodaDevice:
    """A class to interact with a Yoda1 MCU"""

    def __init__(self, mac_addr: str, data: ScaleData, device: BLEDevice):
        self.mac_addr = mac_addr.upper()
        self.data = data
        self.dev = device

    async def listen_for_events(self, callback) -> None:
        """Continuously scans for advertisement data from specific device."""

        logger.info("Listening for events from %s", self.mac_addr)

        def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData) -> None:
            if device.address.upper() == self.mac_addr:
                logger.debug("Received advertisement from %s", device.address)

                scale_data = _parse_device_data(advertisement_data)
                if scale_data:
                    callback(scale_data)

        async with BleakScanner(detection_callback) as _scanner:
            # Scan forever and keep the script running
            while True:
                await asyncio.sleep(1.0)

    @classmethod
    async def discover(cls, timeout: int) -> list["YodaDevice"]:
        """Scans for the scale for a given amount of time."""

        yoda_devices = {}
        device_found = asyncio.Event()

        def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData) -> None:
            if device.address.upper().startswith(YODA_MAC_PREFIX):
                if device.address not in yoda_devices:
                    logger.info("Found a Yoda1 scale: %s", device.address)

                    scale_data = _parse_device_data(advertisement_data)
                    yoda_devices[device.address] = cls(device.address, scale_data, device)

                    if not timeout:
                        device_found.set()

        async with BleakScanner(detection_callback) as scanner:
            try:
                if timeout:
                    await asyncio.sleep(timeout)
                else:
                    # Scan until the first device is found
                    await device_found.wait()
            finally:
                await scanner.stop()

        logger.info("Scan complete. Found %s devices.", len(yoda_devices))
        return list(yoda_devices.values())
