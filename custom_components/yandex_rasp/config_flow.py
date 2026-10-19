"""Config and options flow for Yandex Rasp."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_API_KEY
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .api import RaspAuthError, RaspClient, RaspError, RaspStationError, normalize_station
from .const import (
    CONF_STATION,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)
from .stations import MAX_RESULTS, Station, async_get_station, async_search

CONF_QUERY = "query"
_CODE_RE = re.compile(r"^s?\d+$", re.IGNORECASE)


class RaspConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a station: API key and name search, then pick from the matches."""

    VERSION = 1

    def __init__(self) -> None:
        self._api_key: str | None = None
        self._matches: list[Station] = []

    async def _validate(self, api_key: str, station: str) -> tuple[dict, dict[str, str]]:
        client = RaspClient(async_get_clientsession(self.hass), api_key)
        try:
            return await client.station_info(station), {}
        except RaspAuthError:
            return {}, {"base": "invalid_auth"}
        except RaspStationError:
            return {}, {"base": "invalid_station"}
        except RaspError:
            return {}, {"base": "cannot_connect"}

    async def _search(self, query: str) -> dict[str, str]:
        """Fill self._matches; a raw code ('9601805') is accepted as is."""
        query = query.strip()
        if _CODE_RE.match(query):
            code = normalize_station(query)
            known = await async_get_station(self.hass, code)
            self._matches = [known or Station(code, code, "", "", "")]
            return {}
        if len(query) < 2:
            return {CONF_QUERY: "query_too_short"}
        self._matches = await async_search(self.hass, query)
        return {} if self._matches else {CONF_QUERY: "not_found"}

    def _station_schema(self) -> vol.Schema:
        options = [SelectOptionDict(value=s.code, label=s.label) for s in self._matches]
        return vol.Schema(
            {
                vol.Required(CONF_STATION, default=options[0]["value"]): SelectSelector(
                    SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST)
                    if len(options) <= 8
                    else SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
                )
            }
        )

    def _picked(self, code: str) -> Station:
        return next(s for s in self._matches if s.code == code)

    def _placeholders(self) -> dict[str, str]:
        more = f" (показаны первые {MAX_RESULTS})" if len(self._matches) >= MAX_RESULTS else ""
        return {"count": f"{len(self._matches)}{more}"}

    # --- new entry -------------------------------------------------------

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await self._search(user_input[CONF_QUERY])
            if not errors:
                self._api_key = user_input[CONF_API_KEY]
                return await self.async_step_station()

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): TextSelector(),
                vol.Required(CONF_QUERY): TextSelector(),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )

    async def async_step_station(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            station = self._picked(user_input[CONF_STATION])
            await self.async_set_unique_id(station.code, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            info, errors = await self._validate(self._api_key, station.code)
            if not errors:
                return self.async_create_entry(
                    title=info.get("title") or station.title,
                    data={CONF_API_KEY: self._api_key, CONF_STATION: station.code},
                )
        return self.async_show_form(
            step_id="station",
            data_schema=self._station_schema(),
            description_placeholders=self._placeholders(),
            errors=errors,
        )

    # --- change station of an existing entry -----------------------------

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            errors = await self._search(user_input[CONF_QUERY])
            if not errors:
                return await self.async_step_reconfigure_station()
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({vol.Required(CONF_QUERY): TextSelector()}),
            description_placeholders={"title": self._get_reconfigure_entry().title},
            errors=errors,
        )

    async def async_step_reconfigure_station(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()
        if user_input is not None:
            station = self._picked(user_input[CONF_STATION])
            await self.async_set_unique_id(station.code, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            info, errors = await self._validate(entry.data[CONF_API_KEY], station.code)
            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    unique_id=station.code,
                    title=info.get("title") or station.title,
                    data_updates={CONF_STATION: station.code},
                )
        return self.async_show_form(
            step_id="reconfigure_station",
            data_schema=self._station_schema(),
            description_placeholders=self._placeholders(),
            errors=errors,
        )

    # --- new API key -----------------------------------------------------

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            _, errors = await self._validate(
                user_input[CONF_API_KEY], entry.data[CONF_STATION]
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_API_KEY: user_input[CONF_API_KEY]}
                )
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): TextSelector()}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> RaspOptionsFlow:
        return RaspOptionsFlow()


class RaspOptionsFlow(OptionsFlow):
    """Update interval."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            user_input[CONF_UPDATE_INTERVAL] = int(user_input[CONF_UPDATE_INTERVAL])
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(
            CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_UPDATE_INTERVAL, default=current): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_UPDATE_INTERVAL,
                            max=MAX_UPDATE_INTERVAL,
                            step=1,
                            unit_of_measurement="мин",
                            mode=NumberSelectorMode.BOX,
                        )
                    )
                }
            ),
        )
