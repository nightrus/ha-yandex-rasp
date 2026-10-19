"""Next-departure sensor; the upcoming list lives in its attributes."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RaspConfigEntry, RaspCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: RaspConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([NextTrainSensor(entry.runtime_data)])


class NextTrainSensor(CoordinatorEntity[RaspCoordinator], SensorEntity):
    """State: time of the next departure from the station."""

    _attr_has_entity_name = True
    _attr_translation_key = "next_train"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:train"
    # The departure list changes every minute; keep it out of the recorder.
    _unrecorded_attributes = frozenset({"departures", "directions", "updated"})

    def __init__(self, coordinator: RaspCoordinator) -> None:
        super().__init__(coordinator)
        station = coordinator.station
        title = (coordinator.data or {}).get("station", {}).get("title") or station
        self._attr_unique_id = f"{station}_next_train"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, station)},
            name=f"Электрички: {title}",
            manufacturer="Яндекс.Расписания",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=f"https://rasp.yandex.ru/station/{station[1:]}/suburban",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Recompute from cached data each minute, without API calls.
        self.async_on_remove(
            async_track_time_change(self.hass, self._minute_tick, second=0)
        )

    @callback
    def _minute_tick(self, _now: datetime) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> datetime | None:
        upcoming = self.coordinator.upcoming()
        return upcoming[0]["_dt"] if upcoming else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "station": data.get("station", {}).get("title"),
            "station_code": self.coordinator.station,
            "directions": data.get("directions", []),
            "departures": [
                {k: v for k, v in d.items() if not k.startswith("_")}
                for d in self.coordinator.upcoming()
            ],
            "updated": data.get("updated"),
        }
