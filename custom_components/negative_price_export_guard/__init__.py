"""Negative Price Export Guard integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)

from .const import PLATFORMS, REFRESH_LISTENER_OPTION_KEYS
from .coordinator import NegativePriceExportGuardCoordinator

type NegativePriceExportGuardConfigEntry = ConfigEntry[
    NegativePriceExportGuardCoordinator
]


@callback
def _tracked_entity_ids(entry: NegativePriceExportGuardConfigEntry) -> list[str]:
    """Return configured external entities that should refresh the coordinator."""
    options = {**entry.data, **entry.options}
    return sorted(
        {
            entity_id
            for key in REFRESH_LISTENER_OPTION_KEYS
            if isinstance((entity_id := options.get(key)), str) and entity_id
        }
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: NegativePriceExportGuardConfigEntry
) -> bool:
    """Set up Negative Price Export Guard from a config entry."""
    coordinator = NegativePriceExportGuardCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    tracked_entity_ids = _tracked_entity_ids(entry)
    if tracked_entity_ids:

        @callback
        def _handle_source_state_change(_event: object) -> None:
            coordinator.async_schedule_refresh()

        entry.async_on_unload(
            async_track_state_change_event(
                hass,
                tracked_entity_ids,
                _handle_source_state_change,
            )
        )

    @callback
    def _handle_quarter_hour_boundary(*_: object) -> None:
        coordinator.async_schedule_refresh(delay=0.5, replace=True)

    entry.async_on_unload(
        async_track_time_change(
            hass,
            _handle_quarter_hour_boundary,
            minute=(0, 15, 30, 45),
            second=0,
        )
    )
    entry.async_on_unload(coordinator.async_cancel_scheduled_refresh)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: NegativePriceExportGuardConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
