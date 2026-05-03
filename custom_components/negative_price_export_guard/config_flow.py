"""Config flow for Negative Price Export Guard."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_ALLOW_BATTERY_EARLY_EXPORT,
    CONF_BATTERY_CAPACITY_SENSOR,
    CONF_BATTERY_SOC_SENSOR,
    CONF_CONSUMPTION_MARGIN_KWH,
    CONF_EXPORT_SURPLUS_POWER_NUMBER,
    CONF_EXPORT_SURPLUS_SWITCH,
    CONF_EXPORT_SURPLUS_THRESHOLD_KWH,
    CONF_GRID_MAX_EXPORT_POWER_NUMBER,
    CONF_GUARD_ENABLED,
    CONF_INVERTER_WORK_MODE_SELECT,
    CONF_LOAD_POWER_SENSOR,
    CONF_MAX_EXPORT_POWER_W,
    CONF_MIN_EXPORT_POWER_W,
    CONF_MIN_RESERVE_SOC,
    CONF_NIGHT_TARIFF_NUMBER,
    CONF_OKTE_PRICE_SENSOR,
    CONF_PRICE_FLOOR,
    CONF_PV_POWER_SENSOR,
    CONF_SOLAR_WINDOW_END,
    CONF_SOLAR_WINDOW_START,
    CONF_SOLCAST_FORECAST_TODAY_SENSOR,
    CONF_SOLCAST_REMAINING_TODAY_SENSOR,
    CONF_TODAY_LOAD_CONSUMPTION_SENSOR,
    CONF_TODAY_PRODUCTION_SENSOR,
    CONF_TOTAL_ENERGY_EXPORT_SENSOR,
    CONF_TYPICAL_IDLE_POWER_W,
    DEFAULT_ALLOW_BATTERY_EARLY_EXPORT,
    DEFAULT_CONSUMPTION_MARGIN_KWH,
    DEFAULT_EXPORT_SURPLUS_THRESHOLD_KWH,
    DEFAULT_GUARD_ENABLED,
    DEFAULT_MAX_EXPORT_POWER_W,
    DEFAULT_MIN_EXPORT_POWER_W,
    DEFAULT_MIN_RESERVE_SOC,
    DEFAULT_PRICE_FLOOR,
    DEFAULT_SOLAR_WINDOW_END,
    DEFAULT_SOLAR_WINDOW_START,
    DEFAULT_TYPICAL_IDLE_POWER_W,
    DOMAIN,
)


def _entity(domain: str, device_class: str | None = None) -> EntitySelector:
    config: dict[str, Any] = {"domain": domain}
    if device_class is not None:
        config["device_class"] = device_class
    return EntitySelector(EntitySelectorConfig(**config))


def _sensor(device_class: str | None = None) -> EntitySelector:
    return _entity("sensor", device_class)


def _number(
    minimum: float,
    maximum: float,
    step: float,
    unit: str | None = None,
) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step=step,
            unit_of_measurement=unit,
            mode=NumberSelectorMode.BOX,
        )
    )


STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_NAME, default="Negative Price Export Guard"): str,
        vol.Required(CONF_OKTE_PRICE_SENSOR): _sensor(),
        vol.Required(CONF_SOLCAST_FORECAST_TODAY_SENSOR): _sensor("energy"),
        vol.Required(CONF_SOLCAST_REMAINING_TODAY_SENSOR): _sensor("energy"),
        vol.Required(CONF_TODAY_LOAD_CONSUMPTION_SENSOR): _sensor("energy"),
        vol.Required(CONF_TOTAL_ENERGY_EXPORT_SENSOR): _sensor("energy"),
        vol.Required(CONF_TODAY_PRODUCTION_SENSOR): _sensor("energy"),
        vol.Required(CONF_BATTERY_SOC_SENSOR): _sensor("battery"),
        vol.Required(CONF_BATTERY_CAPACITY_SENSOR): _sensor("energy_storage"),
        vol.Required(CONF_PV_POWER_SENSOR): _sensor("power"),
        vol.Required(CONF_LOAD_POWER_SENSOR): _sensor("power"),
        vol.Required(CONF_INVERTER_WORK_MODE_SELECT): _entity("select"),
        vol.Required(CONF_EXPORT_SURPLUS_SWITCH): _entity("switch"),
        vol.Required(CONF_EXPORT_SURPLUS_POWER_NUMBER): _entity("number"),
        vol.Required(CONF_GRID_MAX_EXPORT_POWER_NUMBER): _entity("number"),
        vol.Optional(CONF_NIGHT_TARIFF_NUMBER): _entity("input_number"),
        vol.Optional(CONF_SOLAR_WINDOW_START, default=DEFAULT_SOLAR_WINDOW_START): str,
        vol.Optional(CONF_SOLAR_WINDOW_END, default=DEFAULT_SOLAR_WINDOW_END): str,
        vol.Optional(CONF_MIN_RESERVE_SOC, default=DEFAULT_MIN_RESERVE_SOC): _number(
            10, 90, 1, "%"
        ),
        vol.Optional(
            CONF_CONSUMPTION_MARGIN_KWH, default=DEFAULT_CONSUMPTION_MARGIN_KWH
        ): _number(0, 10, 0.5, "kWh"),
        vol.Optional(
            CONF_EXPORT_SURPLUS_THRESHOLD_KWH,
            default=DEFAULT_EXPORT_SURPLUS_THRESHOLD_KWH,
        ): _number(0, 10, 0.25, "kWh"),
        vol.Optional(CONF_PRICE_FLOOR, default=DEFAULT_PRICE_FLOOR): _number(
            -50, 50, 0.1, "EUR/MWh"
        ),
        vol.Optional(CONF_MIN_EXPORT_POWER_W, default=DEFAULT_MIN_EXPORT_POWER_W): _number(
            0, 5000, 100, "W"
        ),
        vol.Optional(CONF_MAX_EXPORT_POWER_W, default=DEFAULT_MAX_EXPORT_POWER_W): _number(
            500, 20000, 100, "W"
        ),
        vol.Optional(
            CONF_TYPICAL_IDLE_POWER_W, default=DEFAULT_TYPICAL_IDLE_POWER_W
        ): _number(0, 2000, 10, "W"),
        vol.Optional(CONF_GUARD_ENABLED, default=DEFAULT_GUARD_ENABLED): BooleanSelector(),
        vol.Optional(
            CONF_ALLOW_BATTERY_EARLY_EXPORT,
            default=DEFAULT_ALLOW_BATTERY_EARLY_EXPORT,
        ): BooleanSelector(),
    }
)


def _state_attrs(hass: HomeAssistant, entity_id: str) -> dict[str, Any]:
    state = hass.states.get(entity_id)
    return dict(state.attributes) if state is not None else {}


def _unit(hass: HomeAssistant, entity_id: str) -> str | None:
    return _state_attrs(hass, entity_id).get("unit_of_measurement")


def _unit_is(hass: HomeAssistant, entity_id: str, expected_unit: str) -> bool:
    return _unit(hass, entity_id) == expected_unit


def _validate_time(value: str) -> bool:
    parts = value.split(":")
    if len(parts) not in (2, 3):
        return False
    try:
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) == 3 else 0
    except ValueError:
        return False
    return 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59


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
        CONF_NIGHT_TARIFF_NUMBER,
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

    if not _validate_time(user_input[CONF_SOLAR_WINDOW_START]):
        errors[CONF_SOLAR_WINDOW_START] = "invalid_time"
    if not _validate_time(user_input[CONF_SOLAR_WINDOW_END]):
        errors[CONF_SOLAR_WINDOW_END] = "invalid_time"

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
            errors = await _validate_entities(self.hass, user_input)
            if not errors:
                title = user_input.pop(CONF_NAME, "Negative Price Export Guard")
                return self.async_create_entry(title=title, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
