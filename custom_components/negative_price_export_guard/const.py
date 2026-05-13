"""Constants for Negative Price Export Guard."""

from __future__ import annotations

from datetime import time

from homeassistant.const import Platform

DOMAIN = "negative_price_export_guard"

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.TIME,
]

CONF_OKTE_PRICE_SENSOR = "okte_price_sensor"
CONF_SOLCAST_FORECAST_TODAY_SENSOR = "solcast_forecast_today_sensor"
CONF_SOLCAST_REMAINING_TODAY_SENSOR = "solcast_remaining_today_sensor"
CONF_TODAY_LOAD_CONSUMPTION_SENSOR = "today_load_consumption_sensor"
CONF_TOTAL_ENERGY_EXPORT_SENSOR = "total_energy_export_sensor"
CONF_TODAY_PRODUCTION_SENSOR = "today_production_sensor"
CONF_BATTERY_SOC_SENSOR = "battery_soc_sensor"
CONF_BATTERY_CAPACITY_SENSOR = "battery_capacity_sensor"
CONF_PV_POWER_SENSOR = "pv_power_sensor"
CONF_LOAD_POWER_SENSOR = "load_power_sensor"
CONF_INVERTER_WORK_MODE_SELECT = "inverter_work_mode_select"
CONF_EXPORT_SURPLUS_SWITCH = "export_surplus_switch"
CONF_EXPORT_SURPLUS_POWER_NUMBER = "export_surplus_power_number"
CONF_GRID_MAX_EXPORT_POWER_NUMBER = "grid_max_export_power_number"
CONF_NIGHT_TARIFF_NUMBER = "night_tariff_number"

CONF_SOLAR_WINDOW_START = "solar_window_start"
CONF_SOLAR_WINDOW_END = "solar_window_end"
CONF_MIN_RESERVE_SOC = "min_reserve_soc"
CONF_CONSUMPTION_MARGIN_KWH = "consumption_margin_kwh"
CONF_EXPORT_SURPLUS_THRESHOLD_KWH = "export_surplus_threshold_kwh"
CONF_PRICE_FLOOR = "price_floor"
CONF_MIN_EXPORT_POWER_W = "min_export_power_w"
CONF_MAX_EXPORT_POWER_W = "max_export_power_w"
CONF_TYPICAL_IDLE_POWER_W = "typical_idle_power_w"
CONF_GUARD_ENABLED = "guard_enabled"
CONF_ALLOW_BATTERY_EARLY_EXPORT = "allow_battery_early_export"

DEFAULT_OKTE_PRICE_SENSOR = "sensor.okte_ceny_elektriny_prices"
DEFAULT_SOLCAST_FORECAST_TODAY_SENSOR = "sensor.solcast_pv_forecast_predpoved_dnes"
DEFAULT_SOLCAST_REMAINING_TODAY_SENSOR = (
    "sensor.solcast_pv_forecast_predpoved_zostavajuca_dnes"
)
DEFAULT_TODAY_LOAD_CONSUMPTION_SENSOR = "sensor.inverter_today_load_consumption"
DEFAULT_TOTAL_ENERGY_EXPORT_SENSOR = "sensor.inverter_total_energy_export"
DEFAULT_TODAY_PRODUCTION_SENSOR = "sensor.inverter_today_production"
DEFAULT_BATTERY_SOC_SENSOR = "sensor.inverter_battery"
DEFAULT_BATTERY_CAPACITY_SENSOR = "sensor.inverter_battery_capacity"
DEFAULT_PV_POWER_SENSOR = "sensor.inverter_pv_power"
DEFAULT_LOAD_POWER_SENSOR = "sensor.inverter_load_power"
DEFAULT_INVERTER_WORK_MODE_SELECT = "select.inverter_work_mode"
DEFAULT_EXPORT_SURPLUS_SWITCH = "switch.inverter_export_surplus"
DEFAULT_EXPORT_SURPLUS_POWER_NUMBER = "number.inverter_export_surplus_power"
DEFAULT_GRID_MAX_EXPORT_POWER_NUMBER = "number.solarny_menic_grid_max_export_power"
DEFAULT_NIGHT_TARIFF_NUMBER = "input_number.cena_elektriny_nocny_tarif"

DEFAULT_SOLAR_WINDOW_START = "07:00:00"
DEFAULT_SOLAR_WINDOW_END = "18:00:00"
DEFAULT_MIN_RESERVE_SOC = 30
DEFAULT_CONSUMPTION_MARGIN_KWH = 1
DEFAULT_EXPORT_SURPLUS_THRESHOLD_KWH = 1
DEFAULT_PRICE_FLOOR = 0
DEFAULT_MIN_EXPORT_POWER_W = 500
DEFAULT_MAX_EXPORT_POWER_W = 3000
DEFAULT_TYPICAL_IDLE_POWER_W = 0
DEFAULT_GUARD_ENABLED = True
DEFAULT_ALLOW_BATTERY_EARLY_EXPORT = True
DEFAULT_BATTERY_CAPACITY_KWH = 20
DEFAULT_NIGHT_TARIFF_EUR_KWH = 0.054

SOLAR_WINDOW_START = time(7, 0)
SOLAR_WINDOW_END = time(18, 0)
INTERVAL_MINUTES = 15
INTERVALS_PER_SOLAR_WINDOW = 44
MIN_COMPLETE_LOAD_CURVE_INTERVALS = 40

ATTR_LOAD_CURVE = "load_curve"
ATTR_PAST_CONSUMPTION = "past_consumption"
ATTR_TODAY_LOAD_CURVE = "today_load_curve"
ATTR_PAST_LOAD_CURVES = "past_load_curves"
ATTR_CURRENT_INTERVAL_INDEX = "current_interval_index"
ATTR_LAST_INTERVAL_TOTAL_KWH = "last_interval_total_kwh"

MODE_EXPORT_FIRST = "Export First"
MODE_ZERO_EXPORT_TO_CT = "Zero Export To CT"

REFRESH_LISTENER_OPTION_KEYS: tuple[str, ...] = (
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
