"""Switch platform for Negative Price Export Guard."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_ALLOW_BATTERY_EARLY_EXPORT,
    CONF_GUARD_ENABLED,
    DEFAULT_ALLOW_BATTERY_EARLY_EXPORT,
    DEFAULT_GUARD_ENABLED,
    DOMAIN,
)
from .coordinator import NegativePriceExportGuardCoordinator


@dataclass(frozen=True, kw_only=True)
class ExportGuardSwitchEntityDescription(SwitchEntityDescription):
    """Describe an export guard switch."""

    option_key: str
    default: bool


SWITCHES: tuple[ExportGuardSwitchEntityDescription, ...] = (
    ExportGuardSwitchEntityDescription(
        key="guard_enabled",
        translation_key="guard_enabled",
        option_key=CONF_GUARD_ENABLED,
        default=DEFAULT_GUARD_ENABLED,
        icon="mdi:shield-sun",
    ),
    ExportGuardSwitchEntityDescription(
        key="allow_battery_early_export",
        translation_key="allow_battery_early_export",
        option_key=CONF_ALLOW_BATTERY_EARLY_EXPORT,
        default=DEFAULT_ALLOW_BATTERY_EARLY_EXPORT,
        icon="mdi:battery-arrow-down",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    coordinator: NegativePriceExportGuardCoordinator = entry.runtime_data
    async_add_entities(
        ExportGuardSwitch(coordinator, entry, description)
        for description in SWITCHES
    )


class ExportGuardSwitch(
    CoordinatorEntity[NegativePriceExportGuardCoordinator], SwitchEntity
):
    """A user-tunable switch stored in config entry options."""

    entity_description: ExportGuardSwitchEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NegativePriceExportGuardCoordinator,
        entry: ConfigEntry,
        description: ExportGuardSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_suggested_object_id = f"export_optimizer_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
        }

    @property
    def is_on(self) -> bool:
        """Return if the switch is on."""
        return bool(
            self.coordinator.options.get(
                self.entity_description.option_key,
                self.entity_description.default,
            )
        )

    async def async_turn_on(self, **kwargs: object) -> None:
        """Turn on the switch."""
        await self.coordinator.async_set_option(
            self.entity_description.option_key,
            True,
        )

    async def async_turn_off(self, **kwargs: object) -> None:
        """Turn off the switch."""
        await self.coordinator.async_set_option(
            self.entity_description.option_key,
            False,
        )
