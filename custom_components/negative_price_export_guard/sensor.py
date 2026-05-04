"""Sensor platform for Negative Price Export Guard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CURRENT_INTERVAL_INDEX,
    ATTR_LAST_INTERVAL_TOTAL_KWH,
    ATTR_LOAD_CURVE,
    ATTR_PAST_CONSUMPTION,
    ATTR_PAST_LOAD_CURVES,
    ATTR_TODAY_LOAD_CURVE,
    DOMAIN,
)
from .coordinator import NegativePriceExportGuardCoordinator


@dataclass(frozen=True, kw_only=True)
class ExportGuardSensorEntityDescription(SensorEntityDescription):
    """Describe an export guard sensor."""

    value_key: str
    extra_attribute_keys: tuple[str, ...] = ()


SENSORS: tuple[ExportGuardSensorEntityDescription, ...] = (
    ExportGuardSensorEntityDescription(
        key="okte_spot_price",
        translation_key="okte_spot_price",
        value_key="okte_spot_price",
        native_unit_of_measurement="EUR/MWh",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ExportGuardSensorEntityDescription(
        key="negative_price_minutes_until_window_end",
        translation_key="negative_price_minutes_until_window_end",
        value_key="negative_price_minutes_until_window_end",
        native_unit_of_measurement="min",
    ),
    ExportGuardSensorEntityDescription(
        key="solar_window_load_7d_average",
        translation_key="solar_window_load_7d_average",
        value_key="solar_window_load_7d_average",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
        extra_attribute_keys=(
            ATTR_PAST_CONSUMPTION,
            ATTR_TODAY_LOAD_CURVE,
            ATTR_PAST_LOAD_CURVES,
            ATTR_LOAD_CURVE,
            ATTR_LAST_INTERVAL_TOTAL_KWH,
            ATTR_CURRENT_INTERVAL_INDEX,
        ),
    ),
    ExportGuardSensorEntityDescription(
        key="solar_window_load_today",
        translation_key="solar_window_load_today",
        value_key="solar_window_load_today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ExportGuardSensorEntityDescription(
        key="remaining_solar_window_load_estimate",
        translation_key="remaining_solar_window_load_estimate",
        value_key="remaining_solar_window_load_estimate",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ExportGuardSensorEntityDescription(
        key="expected_load_power",
        translation_key="expected_load_power",
        value_key="expected_load_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ExportGuardSensorEntityDescription(
        key="battery_target_soc",
        translation_key="battery_target_soc",
        value_key="battery_target_soc",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ExportGuardSensorEntityDescription(
        key="expected_surplus_today",
        translation_key="expected_surplus_today",
        value_key="expected_surplus_today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ExportGuardSensorEntityDescription(
        key="recommended_export_power",
        translation_key="recommended_export_power",
        value_key="recommended_export_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ExportGuardSensorEntityDescription(
        key="sell_price",
        translation_key="sell_price",
        value_key="sell_price",
        native_unit_of_measurement="EUR/kWh",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ExportGuardSensorEntityDescription(
        key="exported_energy_during_negative_spot_price",
        translation_key="exported_energy_during_negative_spot_price",
        value_key="exported_energy_during_negative_spot_price",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ExportGuardSensorEntityDescription(
        key="exported_energy_by_automation",
        translation_key="exported_energy_by_automation",
        value_key="exported_energy_by_automation",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    ExportGuardSensorEntityDescription(
        key="automation_export_savings",
        translation_key="automation_export_savings",
        value_key="automation_export_savings",
        native_unit_of_measurement="EUR",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
    ),
    ExportGuardSensorEntityDescription(
        key="negative_price_wasted_potential",
        translation_key="negative_price_wasted_potential",
        value_key="negative_price_wasted_potential",
        native_unit_of_measurement="EUR",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors."""
    coordinator: NegativePriceExportGuardCoordinator = entry.runtime_data
    async_add_entities(
        ExportGuardSensor(coordinator, entry, description) for description in SENSORS
    )


class ExportGuardSensor(
    CoordinatorEntity[NegativePriceExportGuardCoordinator], SensorEntity
):
    """A calculated export guard sensor."""

    entity_description: ExportGuardSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NegativePriceExportGuardCoordinator,
        entry: ConfigEntry,
        description: ExportGuardSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_suggested_object_id = f"export_optimizer_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
        }

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        return self.coordinator.data.get(self.entity_description.value_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes."""
        if not self.entity_description.extra_attribute_keys:
            return None
        return {
            key: self.coordinator.data.get(key)
            for key in self.entity_description.extra_attribute_keys
        }
