"""Time platform for Negative Price Export Guard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time

from homeassistant.components.time import TimeEntity, TimeEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_SOLAR_WINDOW_END,
    CONF_SOLAR_WINDOW_START,
    DEFAULT_SOLAR_WINDOW_END,
    DEFAULT_SOLAR_WINDOW_START,
    DOMAIN,
)
from .coordinator import NegativePriceExportGuardCoordinator


@dataclass(frozen=True, kw_only=True)
class ExportGuardTimeEntityDescription(TimeEntityDescription):
    """Describe an export guard time entity."""

    option_key: str
    default: str


TIMES: tuple[ExportGuardTimeEntityDescription, ...] = (
    ExportGuardTimeEntityDescription(
        key="solar_window_start",
        translation_key="solar_window_start",
        option_key=CONF_SOLAR_WINDOW_START,
        default=DEFAULT_SOLAR_WINDOW_START,
        icon="mdi:weather-sunset-up",
    ),
    ExportGuardTimeEntityDescription(
        key="solar_window_end",
        translation_key="solar_window_end",
        option_key=CONF_SOLAR_WINDOW_END,
        default=DEFAULT_SOLAR_WINDOW_END,
        icon="mdi:weather-sunset-down",
    ),
)


def _parse_time(value: str) -> time:
    """Parse a stored time value."""
    for time_format in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(value, time_format).time()
        except ValueError:
            continue
    return datetime.strptime(DEFAULT_SOLAR_WINDOW_START, "%H:%M:%S").time()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up time entities."""
    coordinator: NegativePriceExportGuardCoordinator = entry.runtime_data
    async_add_entities(
        ExportGuardTime(coordinator, entry, description) for description in TIMES
    )


class ExportGuardTime(CoordinatorEntity[NegativePriceExportGuardCoordinator], TimeEntity):
    """A user-tunable time stored in config entry options."""

    entity_description: ExportGuardTimeEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NegativePriceExportGuardCoordinator,
        entry: ConfigEntry,
        description: ExportGuardTimeEntityDescription,
    ) -> None:
        """Initialize the time entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
        }

    @property
    def native_value(self) -> time:
        """Return the configured time."""
        value = self.coordinator.options.get(
            self.entity_description.option_key,
            self.entity_description.default,
        )
        return _parse_time(str(value))

    async def async_set_value(self, value: time) -> None:
        """Update the configured time."""
        await self.coordinator.async_set_option(
            self.entity_description.option_key,
            value.isoformat(),
        )
