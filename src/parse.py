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

import struct

from dataclasses import dataclass

@dataclass
class ScaleData:
    """Data class for scale measurements."""

    weight: float
    unit: str = 'kg' # No way to detect current unit set on the weight

    def __repr__(self):
        return f"ScaleData(weight={self.weight:.2f}{self.unit})"

def parse_scale_data(data: bytes) -> ScaleData:
    """Parses the manufacturer advertisement data from the scale."""

    if len(data) < 2:
        return None

    # The most reliable data seems to be the first two bytes for weight.
    # The more complex parsing for impedance/stabilization is not working reliably.
    weight = struct.unpack('>H', data[0:2])[0] / 100.0
    return ScaleData(weight=weight)
