"""Yandex Rasp — suburban train departures for Home Assistant."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.typing import ConfigType

from .const import CARD_URL, CONF_STATION, DOMAIN, VERSION
from .coordinator import RaspConfigEntry, RaspCoordinator

PLATFORMS = [Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the bundled Lovelace card so no manual resource is needed."""
    card = Path(__file__).parent / "frontend" / "yandex-rasp-card.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(card), cache_headers=False)]
    )
    add_extra_js_url(hass, f"{CARD_URL}?v={VERSION}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: RaspConfigEntry) -> bool:
    _remove_stale_station(hass, entry)
    coordinator = RaspCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: RaspConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def _remove_stale_station(hass: HomeAssistant, entry: RaspConfigEntry) -> None:
    """After a station change (reconfigure) drop the old station's entities."""
    station = entry.data[CONF_STATION]
    ent_reg = er.async_get(hass)
    for ent in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if not ent.unique_id.startswith(f"{station}_"):
            ent_reg.async_remove(ent.entity_id)
    dev_reg = dr.async_get(hass)
    for dev in dr.async_entries_for_config_entry(dev_reg, entry.entry_id):
        if (DOMAIN, station) not in dev.identifiers:
            dev_reg.async_update_device(dev.id, remove_config_entry_id=entry.entry_id)


async def _async_options_updated(hass: HomeAssistant, entry: RaspConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
