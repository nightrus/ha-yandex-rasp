"""Config and options flow for Yandex Rasp."""

from __future__ import annotations

from collections.abc import Mapping
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
    TextSelector,
)

from .api import RaspAuthError, RaspClient, RaspError, RaspStationError, normalize_station
from .const import (
    CONF_STATION,
    CONF_UPDATE_INTERVAL,
    DEFAULT_STATION,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)


class RaspConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a station."""

    VERSION = 1

    async def _validate(self, api_key: str, station: str) -> tuple[dict, dict[str, str]]:
        client = RaspClient(async_get_clientsession(self.hass), api_key)
        try:
            return await client.station_info(station), {}
        except RaspAuthError:
            return {}, {"base": "invalid_auth"}
        except RaspStationError:
            return {}, {CONF_STATION: "invalid_station"}
        except RaspError:
            return {}, {"base": "cannot_connect"}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            station = normalize_station(user_input[CONF_STATION])
            await self.async_set_unique_id(station)
            self._abort_if_unique_id_configured()
            info, errors = await self._validate(user_input[CONF_API_KEY], station)
            if not errors:
                return self.async_create_entry(
                    title=info.get("title") or station,
                    data={CONF_API_KEY: user_input[CONF_API_KEY], CONF_STATION: station},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): TextSelector(),
                vol.Required(CONF_STATION, default=DEFAULT_STATION): TextSelector(),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, user_input),
            errors=errors,
        )

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
