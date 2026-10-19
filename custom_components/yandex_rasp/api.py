"""Minimal client for the Yandex Rasp schedule API (v3.0)."""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

import aiohttp

from .const import API_PAGE_LIMIT, API_URL


class RaspError(Exception):
    """Generic API error."""


class RaspAuthError(RaspError):
    """Invalid or blocked API key."""


class RaspStationError(RaspError):
    """Unknown station code."""


def normalize_station(code: str) -> str:
    """Accept '9601805' as well as 's9601805'."""
    code = code.strip().lower()
    return code if code.startswith("s") else f"s{code}"


class RaspClient:
    """Fetches the suburban departure board of one station."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        self._session = session
        self._api_key = api_key

    async def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        query = {
            "apikey": self._api_key,
            "format": "json",
            "lang": "ru_RU",
            "transport_types": "suburban",
            **params,
        }
        try:
            async with asyncio.timeout(20):
                resp = await self._session.get(API_URL, params=query)
                data = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise RaspError(f"Request failed: {err}") from err

        if resp.status == 200:
            return data
        text = _error_text(data)
        if resp.status in (401, 403) or "ключ" in text.lower():
            raise RaspAuthError(text)
        if resp.status == 404:
            raise RaspStationError(text)
        raise RaspError(f"HTTP {resp.status}: {text}")

    async def station_info(self, station: str) -> dict[str, Any]:
        """Return the station object (used to validate config)."""
        data = await self._get({"station": station, "limit": 1})
        return data.get("station") or {}

    async def day_schedule(self, station: str, day: date) -> dict[str, Any]:
        """Return station info, directions and all departures of a day."""
        offset = 0
        schedule: list[dict[str, Any]] = []
        while True:
            data = await self._get(
                {
                    "station": station,
                    "date": day.isoformat(),
                    "limit": API_PAGE_LIMIT,
                    "offset": offset,
                }
            )
            schedule.extend(data.get("schedule") or [])
            total = (data.get("pagination") or {}).get("total", 0)
            offset += API_PAGE_LIMIT
            if offset >= total:
                break
        return {
            "station": data.get("station") or {},
            "directions": data.get("directions") or [],
            "schedule": schedule,
        }


def _error_text(data: Any) -> str:
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict):
            return str(err.get("text") or err)
    return str(data)[:200]
