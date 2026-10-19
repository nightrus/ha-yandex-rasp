"""Data update coordinator for Yandex Rasp."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import RaspAuthError, RaspClient, RaspError
from .const import (
    ATTR_WINDOW_HOURS,
    CONF_STATION,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    PRIORITY_DIRECTION,
)

_LOGGER = logging.getLogger(__name__)

type RaspConfigEntry = ConfigEntry[RaspCoordinator]


class RaspCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Keeps the departures of today (and tomorrow near midnight)."""

    config_entry: RaspConfigEntry

    def __init__(self, hass: HomeAssistant, entry: RaspConfigEntry) -> None:
        minutes = entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.data[CONF_STATION]}",
            update_interval=timedelta(minutes=minutes),
        )
        self.station: str = entry.data[CONF_STATION]
        self.client = RaspClient(async_get_clientsession(hass), entry.data[CONF_API_KEY])

    async def _async_update_data(self) -> dict[str, Any]:
        now = dt_util.now()
        days = [now.date()]
        # The window shown to the user may cross midnight.
        if (now + timedelta(hours=ATTR_WINDOW_HOURS)).date() != now.date():
            days.append(now.date() + timedelta(days=1))

        station: dict[str, Any] = {}
        directions: list[str] = []
        departures: list[dict[str, Any]] = []
        try:
            for day in days:
                raw = await self.client.day_schedule(self.station, day)
                station = station or raw["station"]
                for d in raw["directions"]:
                    if d.get("code") not in ("all", "arrival") and d["title"] not in directions:
                        directions.append(d["title"])
                departures.extend(
                    dep for item in raw["schedule"] if (dep := _departure(item))
                )
        except RaspAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except RaspError as err:
            raise UpdateFailed(str(err)) from err

        # Same train may come twice around midnight (both day queries).
        unique = {(d["uid"], d["departure"]): d for d in departures}
        departures = sorted(unique.values(), key=lambda d: d["departure"])
        for d in departures:
            if d["direction"] not in directions:
                directions.append(d["direction"])
        directions.sort(key=lambda t: PRIORITY_DIRECTION not in t.lower())

        return {
            "station": station,
            "directions": directions,
            "departures": departures,
            "updated": now.isoformat(),
        }

    def upcoming(self, hours: float = ATTR_WINDOW_HOURS) -> list[dict[str, Any]]:
        """Departures from now until now + hours."""
        if not self.data:
            return []
        now = dt_util.now()
        end = now + timedelta(hours=hours)
        return [d for d in self.data["departures"] if now <= d["_dt"] <= end]


def _departure(item: dict[str, Any]) -> dict[str, Any] | None:
    dep = item.get("departure")
    if not dep:
        return None
    when = datetime.fromisoformat(dep)
    thread = item.get("thread") or {}
    subtype = thread.get("transport_subtype") or {}
    return {
        "_dt": when,
        "departure": when.isoformat(),
        "number": thread.get("number"),
        "title": thread.get("short_title") or thread.get("title"),
        "direction": item.get("direction") or "",
        "express": bool(thread.get("express_type")),
        "subtype": subtype.get("title"),
        "color": subtype.get("color"),
        "stops": item.get("stops") or "",
        "platform": item.get("platform") or "",
        "uid": thread.get("uid"),
    }
