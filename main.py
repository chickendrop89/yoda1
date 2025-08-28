#!/usr/bin/env python3

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

import argparse
import asyncio
import logging
import bleak

from src.device import YodaDevice

def setup_logging() -> None:
    """Configure logging to be more readable."""

    logging.basicConfig(
        level=logging.INFO,
        format="[yoda-sniffer] %(message)s",
        handlers=[logging.StreamHandler()]
    )

async def scan(address: str, timeout: int) -> None:
    """Scans for Yoda1 scales and watches for data events."""

    device = None
    last_data = None
    logger = logging.getLogger(__name__)

    def print_devices(logger: logging.Logger, devices: list) -> None:

        logger.info("--- Found Devices ---")
        for d in devices:
            logger.info(d.mac_addr)
        logger.info("---------------------")

    def handle_data(scale_data):
        nonlocal last_data

        # Only log if the weight has changed
        if last_data is None or scale_data.weight != last_data.weight:
            logger.info("Weight: %.2f%s", scale_data.weight, scale_data.unit)
            last_data = scale_data

    if address:
        # Skip discovery and directly listen for events on the specified address
        device = YodaDevice(address, None, None)
    else:
        scan_message = "Searching for the Yoda1"
        if timeout:
            scan_message += f" for {timeout} seconds"
        logger.info("%s. Step or turn on your scale", scan_message)

        try:
            devices = await YodaDevice.discover(timeout or None)
        except bleak.exc.BleakError as error:
            return logger.error("An error occurred during discovery: %s", error)

        if not devices:
            return logger.critical("No Yoda1 scale found")

        if len(devices) > 1:
            logger.critical("Multiple scales found but no --address parameter specified")
            return print_devices(logger, devices)

        device = devices[0]
    try:
        await device.watch_events(handle_data)
    except asyncio.CancelledError:
        logger.info("Event watching canceled.")

async def main():
    """Parse command line arguments and start scanning."""

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='''yoda1-sniffer - a tool to grab weight data
        transmitted from a yoda1 bluetooth scale'''
    )
    parser.add_argument(
        "-a", "--address", 
        type=str,
        help="Bluetooth MAC address of the scale"
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        help="Discovery scan timeout in seconds"
    )
    args = parser.parse_args()

    await scan(args.address, args.timeout)

if __name__ == "__main__":
    setup_logging()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Exitting")
