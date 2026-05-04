"""Number platform for Negative Price Export Guard."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_CONSUMPTION_MARGIN_KWH,
    CONF_EXPORT_SURPLUS_THRESHOLD_KWH,
    CONF_MAX_EXPORT_POWER_W,
    CONF_MIN_EXPORT_POWER_W,
    CONF_MIN_RESERVE_SOC,
    CONF_PRICE_FLOOR,
    CONF_TYPICAL_IDLE_POWER_W,
    DEFAULT_CONSUMPTION_MARGIN_KWH,
    DEFAULT_EXPORT_SURPLUS_THRESHOLD_KWH,
    DEFAULT_MAX_EXPORT_POWER_W,
    DEFAULT_MIN_EXPORT_POWER_W,
    DEFAULT_MIN_RESERVE_SOC,
    DEFAULT_PRICE_FLOOR,
    DEFAULT_TYPICAL_IDLE_POWER_W,
    DOMAIN,
)
from .coordinator import NegativePriceExportGuardCoordinator


@dataclass(frozen=True, kw_only=True)
class ExportGuardNumberEntityDescription(NumberEntityDescription):
    """Describe an export guard number."""

    option_key: str
    default: float


NUMBERS: tuple[ExportGuardNumberEntityDescription, ...] = (
    ExportGuardNumberEntityDescription(
        key="min_reserve_soc",
        translation_key="min_reserve_soc",
        option_key=CONF_MIN_RESERVE_SOC,
        default=DEFAULT_MIN_RESERVE_SOC,
        native_min_value=10,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement="%",
    ),
    ExportGuardNumberEntityDescription(
        key="consumption_margin_kwh",
        translation_key="consumption_margin_kwh",
        option_key=CONF_CONSUMPTION_MARGIN_KWH,
        default=DEFAULT_CONSUMPTION_MARGIN_KWH,
        native_min_value=0,
        native_max_value=10,
        native_step=0.5,
        native_unit_of_measurement="kWh",
    ),
    ExportGuardNumberEntityDescription(
        key="export_surplus_threshold_kwh",
        translation_key="export_surplus_threshold_kwh",
        option_key=CONF_EXPORT_SURPLUS_THRESHOLD_KWH,
        default=DEFAULT_EXPORT_SURPLUS_THRESHOLD_KWH,
        native_min_value=0,
        native_max_value=10,
        native_step=0.25,
        native_unit_of_measurement="kWh",
    ),
    ExportGuardNumberEntityDescription(
        key="price_floor",
        translation_key="price_floor",
        option_key=CONF_PRICE_FLOOR,
        default=DEFAULT_PRICE_FLOOR,
        native_min_value=-50,
        native_max_value=50,
        native_step=0.1,
        native_unit_of_measurement="EUR/MWh",
    ),
    ExportGuardNumberEntityDescription(
        key="min_export_power_w",
        translation_key="min_export_power_w",
        option_key=CONF_MIN_EXPORT_POWER_W,
        default=DEFAULT_MIN_EXPORT_POWER_W,
        native_min_value=0,
        native_max_value=5000,
        native_step=100,
        native_unit_of_measurement="W",
    ),
    ExportGuardNumberEntityDescription(
        key="max_export_power_w",
        translation_key="max_export_power_w",
        option_key=CONF_MAX_EXPORT_POWER_W,
        default=DEFAULT_MAX_EXPORT_POWER_W,
        native_min_value=500,
        native_max_value=20000,
        native_step=100,
        native_unit_of_measurement="W",
    ),
    ExportGuardNumberEntityDescription(
        key="typical_idle_power_w",
        translation_key="typical_idle_power_w",
        option_key=CONF_TYPICAL_IDLE_POWER_W,
        default=DEFAULT_TYPICAL_IDLE_POWER_W,
        native_min_value=0,
        native_max_value=2000,
        native_step=10,
        native_unit_of_measurement="W",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities."""
    coordinator: NegativePriceExportGuardCoordinator = entry.runtime_data
    async_add_entities(
        ExportGuardNumber(coordinator, entry, description) for description in NUMBERS
    )


class ExportGuardNumber(
    CoordinatorEntity[NegativePriceExportGuardCoordinator], NumberEntity
):
    """A user-tunable number stored in config entry options."""

    entity_description: ExportGuardNumberEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NegativePriceExportGuardCoordinator,
        entry: ConfigEntry,
        description: ExportGuardNumberEntityDescription,
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_suggested_object_id = f"export_optimizer_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
        }

    @property
    def native_value(self) -> float:
        """Return the configured value."""
        return float(
            self.coordinator.options.get(
                self.entity_description.option_key,
                self.entity_description.default,
            )
        )

    async def async_set_native_value(self, value: float) -> None:
        """Update the configured value."""
        await self.coordinator.async_set_option(
            self.entity_description.option_key,
            value,
        )
