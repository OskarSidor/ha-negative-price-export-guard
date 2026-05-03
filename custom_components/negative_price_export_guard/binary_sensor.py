"""Binary sensor platform for Negative Price Export Guard."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NegativePriceExportGuardCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors."""
    coordinator: NegativePriceExportGuardCoordinator = entry.runtime_data
    async_add_entities([ExportWantedBinarySensor(coordinator, entry)])


class ExportWantedBinarySensor(
    CoordinatorEntity[NegativePriceExportGuardCoordinator], BinarySensorEntity
):
    """Binary sensor showing whether strategic export is wanted."""

    _attr_has_entity_name = True
    _attr_translation_key = "export_wanted"

    def __init__(
        self,
        coordinator: NegativePriceExportGuardCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_export_wanted"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
        }

    @property
    def is_on(self) -> bool:
        """Return true if export is wanted."""
        return bool(self.coordinator.data.get("export_wanted"))
