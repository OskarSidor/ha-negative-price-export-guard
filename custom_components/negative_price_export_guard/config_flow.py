"""Config flow for Negative Price Export Guard."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import EntitySelector, EntitySelectorConfig

from .const import (
    CONF_BATTERY_CAPACITY_SENSOR,
    CONF_BATTERY_SOC_SENSOR,
    CONF_EXPORT_SURPLUS_POWER_NUMBER,
    CONF_EXPORT_SURPLUS_SWITCH,
    CONF_GRID_MAX_EXPORT_POWER_NUMBER,
    CONF_INVERTER_WORK_MODE_SELECT,
    CONF_LOAD_POWER_SENSOR,
    CONF_NIGHT_TARIFF_NUMBER,
    CONF_OKTE_PRICE_SENSOR,
    CONF_PV_POWER_SENSOR,
    CONF_SOLCAST_FORECAST_TODAY_SENSOR,
    CONF_SOLCAST_REMAINING_TODAY_SENSOR,
    CONF_TODAY_LOAD_CONSUMPTION_SENSOR,
    CONF_TODAY_PRODUCTION_SENSOR,
    CONF_TOTAL_ENERGY_EXPORT_SENSOR,
    DEFAULT_BATTERY_CAPACITY_SENSOR,
    DEFAULT_BATTERY_SOC_SENSOR,
    DEFAULT_EXPORT_SURPLUS_POWER_NUMBER,
    DEFAULT_EXPORT_SURPLUS_SWITCH,
    DEFAULT_GRID_MAX_EXPORT_POWER_NUMBER,
    DEFAULT_INVERTER_WORK_MODE_SELECT,
    DEFAULT_LOAD_POWER_SENSOR,
    DEFAULT_NIGHT_TARIFF_NUMBER,
    DEFAULT_OKTE_PRICE_SENSOR,
    DEFAULT_PV_POWER_SENSOR,
    DEFAULT_SOLCAST_FORECAST_TODAY_SENSOR,
    DEFAULT_SOLCAST_REMAINING_TODAY_SENSOR,
    DEFAULT_TODAY_LOAD_CONSUMPTION_SENSOR,
    DEFAULT_TODAY_PRODUCTION_SENSOR,
    DEFAULT_TOTAL_ENERGY_EXPORT_SENSOR,
    DOMAIN,
)


def _entity(domain: str, device_class: str | None = None) -> EntitySelector:
    config: dict[str, Any] = {"domain": domain}
    if device_class is not None:
        config["device_class"] = device_class
    return EntitySelector(EntitySelectorConfig(**config))


def _sensor(device_class: str | None = None) -> EntitySelector:
    return _entity("sensor", device_class)


STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default="Negative Price Export Guard"): str,
        vol.Required(
            CONF_OKTE_PRICE_SENSOR,
            default=DEFAULT_OKTE_PRICE_SENSOR,
        ): _sensor(),
        vol.Required(
            CONF_SOLCAST_FORECAST_TODAY_SENSOR,
            default=DEFAULT_SOLCAST_FORECAST_TODAY_SENSOR,
        ): _sensor("energy"),
        vol.Required(
            CONF_SOLCAST_REMAINING_TODAY_SENSOR,
            default=DEFAULT_SOLCAST_REMAINING_TODAY_SENSOR,
        ): _sensor("energy"),
        vol.Required(
            CONF_TODAY_LOAD_CONSUMPTION_SENSOR,
            default=DEFAULT_TODAY_LOAD_CONSUMPTION_SENSOR,
        ): _sensor("energy"),
        vol.Required(
            CONF_TOTAL_ENERGY_EXPORT_SENSOR,
            default=DEFAULT_TOTAL_ENERGY_EXPORT_SENSOR,
        ): _sensor("energy"),
        vol.Required(
            CONF_TODAY_PRODUCTION_SENSOR,
            default=DEFAULT_TODAY_PRODUCTION_SENSOR,
        ): _sensor("energy"),
        vol.Required(
            CONF_BATTERY_SOC_SENSOR,
            default=DEFAULT_BATTERY_SOC_SENSOR,
        ): _sensor("battery"),
        vol.Required(
            CONF_BATTERY_CAPACITY_SENSOR,
            default=DEFAULT_BATTERY_CAPACITY_SENSOR,
        ): _sensor("energy_storage"),
        vol.Required(
            CONF_PV_POWER_SENSOR,
            default=DEFAULT_PV_POWER_SENSOR,
        ): _sensor("power"),
        vol.Required(
            CONF_LOAD_POWER_SENSOR,
            default=DEFAULT_LOAD_POWER_SENSOR,
        ): _sensor("power"),
        vol.Required(
            CONF_INVERTER_WORK_MODE_SELECT,
            default=DEFAULT_INVERTER_WORK_MODE_SELECT,
        ): _entity("select"),
        vol.Required(
            CONF_EXPORT_SURPLUS_SWITCH,
            default=DEFAULT_EXPORT_SURPLUS_SWITCH,
        ): _entity("switch"),
        vol.Required(
            CONF_EXPORT_SURPLUS_POWER_NUMBER,
            default=DEFAULT_EXPORT_SURPLUS_POWER_NUMBER,
        ): _entity("number"),
        vol.Required(
            CONF_GRID_MAX_EXPORT_POWER_NUMBER,
            default=DEFAULT_GRID_MAX_EXPORT_POWER_NUMBER,
        ): _entity("number"),
        vol.Optional(
            CONF_NIGHT_TARIFF_NUMBER,
            default=DEFAULT_NIGHT_TARIFF_NUMBER,
        ): _entity("input_number"),
    }
)


def _state_attrs(hass: HomeAssistant, entity_id: str) -> dict[str, Any]:
    state = hass.states.get(entity_id)
    return dict(state.attributes) if state is not None else {}


def _unit(hass: HomeAssistant, entity_id: str) -> str | None:
    return _state_attrs(hass, entity_id).get("unit_of_measurement")


def _unit_is(hass: HomeAssistant, entity_id: str, expected_unit: str) -> bool:
    return _unit(hass, entity_id) == expected_unit


def _remove_missing_optional_entities(
    hass: HomeAssistant, user_input: dict[str, Any]
) -> None:
    """Drop optional entity defaults when the entity is not present."""
    night_tariff = user_input.get(CONF_NIGHT_TARIFF_NUMBER)
    if night_tariff and hass.states.get(night_tariff) is None:
        user_input.pop(CONF_NIGHT_TARIFF_NUMBER, None)


async def _validate_entities(
    hass: HomeAssistant, user_input: dict[str, Any]
) -> dict[str, str]:
    """Validate selected entities and return field errors."""
    errors: dict[str, str] = {}
    entity_keys = (
        CONF_OKTE_PRICE_SENSOR,
        CONF_SOLCAST_FORECAST_TODAY_SENSOR,
        CONF_SOLCAST_REMAINING_TODAY_SENSOR,
        CONF_TODAY_LOAD_CONSUMPTION_SENSOR,
        CONF_TOTAL_ENERGY_EXPORT_SENSOR,
        CONF_TODAY_PRODUCTION_SENSOR,
        CONF_BATTERY_SOC_SENSOR,
        CONF_BATTERY_CAPACITY_SENSOR,
        CONF_PV_POWER_SENSOR,
        CONF_LOAD_POWER_SENSOR,
        CONF_INVERTER_WORK_MODE_SELECT,
        CONF_EXPORT_SURPLUS_SWITCH,
        CONF_EXPORT_SURPLUS_POWER_NUMBER,
        CONF_GRID_MAX_EXPORT_POWER_NUMBER,
    )
    for key in entity_keys:
        if hass.states.get(user_input[key]) is None:
            errors[key] = "missing_entity"

    if errors:
        return errors

    okte_attrs = _state_attrs(hass, user_input[CONF_OKTE_PRICE_SENSOR])
    if not isinstance(okte_attrs.get("prices"), list):
        errors[CONF_OKTE_PRICE_SENSOR] = "missing_prices_attribute"

    solcast_attrs = _state_attrs(
        hass, user_input[CONF_SOLCAST_FORECAST_TODAY_SENSOR]
    )
    if not isinstance(solcast_attrs.get("detailedForecast"), list):
        errors[CONF_SOLCAST_FORECAST_TODAY_SENSOR] = (
            "missing_detailed_forecast_attribute"
        )

    energy_sensors = (
        CONF_SOLCAST_FORECAST_TODAY_SENSOR,
        CONF_SOLCAST_REMAINING_TODAY_SENSOR,
        CONF_TODAY_LOAD_CONSUMPTION_SENSOR,
        CONF_TOTAL_ENERGY_EXPORT_SENSOR,
        CONF_TODAY_PRODUCTION_SENSOR,
        CONF_BATTERY_CAPACITY_SENSOR,
    )
    for key in energy_sensors:
        entity_id = user_input[key]
        if not _unit_is(hass, entity_id, "kWh"):
            errors[key] = "invalid_energy_unit"

    power_sensors = (CONF_PV_POWER_SENSOR, CONF_LOAD_POWER_SENSOR)
    for key in power_sensors:
        entity_id = user_input[key]
        if not _unit_is(hass, entity_id, "W"):
            errors[key] = "invalid_power_unit"

    battery_soc_sensor = user_input[CONF_BATTERY_SOC_SENSOR]
    if not _unit_is(hass, battery_soc_sensor, "%"):
        errors[CONF_BATTERY_SOC_SENSOR] = "invalid_soc_unit"

    export_power_numbers = (
        CONF_EXPORT_SURPLUS_POWER_NUMBER,
        CONF_GRID_MAX_EXPORT_POWER_NUMBER,
    )
    for key in export_power_numbers:
        entity_id = user_input[key]
        if not _unit_is(hass, entity_id, "W"):
            errors[key] = "invalid_export_power_unit"

    return errors


class NegativePriceExportGuardConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}
        if user_input is not None:
            _remove_missing_optional_entities(self.hass, user_input)
            errors = await _validate_entities(self.hass, user_input)
            if not errors:
                title = user_input.pop(CONF_NAME, "Negative Price Export Guard")
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
