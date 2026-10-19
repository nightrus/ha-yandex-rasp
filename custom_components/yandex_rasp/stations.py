"""Bundled railway station directory (see tools/build_stations.py)."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import NamedTuple

from homeassistant.core import HomeAssistant

from .const import DOMAIN

_FILE = Path(__file__).parent / "stations.json.gz"
_DATA_KEY = f"{DOMAIN}_stations"
_HOME_REGION = "Москва и Московская область"
MAX_RESULTS = 50


class Station(NamedTuple):
    code: str
    title: str
    direction: str
    settlement: str
    region: str

    @property
    def label(self) -> str:
        parts = [self.title]
        if self.direction:
            parts.append(f"{self.direction} напр.")
        if self.settlement and self.settlement != self.title:
            parts.append(self.settlement)
        if self.region != _HOME_REGION:
            parts.append(self.region)
        return " · ".join(parts)


def _norm(text: str) -> str:
    return text.lower().replace("ё", "е").strip()


def _load() -> list[Station]:
    return [Station(*row) for row in json.loads(gzip.decompress(_FILE.read_bytes()))]


async def async_get_stations(hass: HomeAssistant) -> list[Station]:
    if _DATA_KEY not in hass.data:
        hass.data[_DATA_KEY] = await hass.async_add_executor_job(_load)
    return hass.data[_DATA_KEY]


async def async_search(hass: HomeAssistant, query: str) -> list[Station]:
    """Stations whose name contains query; prefix matches and Moscow first."""
    q = _norm(query)
    if not q:
        return []
    found = []
    for st in await async_get_stations(hass):
        name = _norm(st.title)
        pos = name.find(q)
        if pos < 0:
            continue
        rank = (0 if name == q else 1 if pos == 0 else 2, st.region != _HOME_REGION)
        found.append((rank, st))
    found.sort(key=lambda x: (x[0], x[1].title, x[1].direction))
    return [st for _, st in found[:MAX_RESULTS]]


async def async_get_station(hass: HomeAssistant, code: str) -> Station | None:
    return next((s for s in await async_get_stations(hass) if s.code == code), None)
