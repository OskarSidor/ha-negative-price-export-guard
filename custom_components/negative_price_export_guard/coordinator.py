"""Coordinator for Negative Price Export Guard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_CURRENT_INTERVAL_INDEX,
    ATTR_LAST_INTERVAL_TOTAL_KWH,
    ATTR_LOAD_CURVE,
    ATTR_PAST_CONSUMPTION,
    ATTR_PAST_LOAD_CURVES,
    ATTR_TODAY_LOAD_CURVE,
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
    CONF_TOTAL_ENERGY_EXPORT_SENSOR,
    CONF_TYPICAL_IDLE_POWER_W,
    DEFAULT_BATTERY_CAPACITY_KWH,
    DEFAULT_CONSUMPTION_MARGIN_KWH,
    DEFAULT_EXPORT_SURPLUS_THRESHOLD_KWH,
    DEFAULT_MAX_EXPORT_POWER_W,
    DEFAULT_MIN_EXPORT_POWER_W,
    DEFAULT_MIN_RESERVE_SOC,
    DEFAULT_NIGHT_TARIFF_EUR_KWH,
    DEFAULT_PRICE_FLOOR,
    DEFAULT_SOLAR_WINDOW_END,
    DEFAULT_SOLAR_WINDOW_START,
    DEFAULT_TYPICAL_IDLE_POWER_W,
    DOMAIN,
    INTERVAL_MINUTES,
    INTERVALS_PER_SOLAR_WINDOW,
    MIN_COMPLETE_LOAD_CURVE_INTERVALS,
    MODE_EXPORT_FIRST,
    MODE_ZERO_EXPORT_TO_CT,
)

_LOGGER = logging.getLogger(__name__)
STORAGE_VERSION = 1

KEY_AUTOMATION_EXPORT_SAVINGS = "automation_export_savings"
KEY_EXPORTED_ENERGY_BY_AUTOMATION = "exported_energy_by_automation"
KEY_EXPORTED_ENERGY_NEGATIVE_PRICE = "exported_energy_during_negative_spot_price"
KEY_LAST_TOTAL_ENERGY_EXPORT = "last_total_energy_export_kwh"
KEY_NEGATIVE_PRICE_WASTED_POTENTIAL = "negative_price_wasted_potential"


@dataclass(slots=True)
class SourceState:
    """A source entity state."""

    state: str | None
    attributes: dict[str, Any]


def _parse_time(value: str, fallback: str) -> datetime.time:
    """Parse a Home Assistant time selector value."""
    for candidate in (value, fallback):
        for time_format in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(candidate, time_format).time()
            except ValueError:
                continue
    return datetime.strptime(DEFAULT_SOLAR_WINDOW_START, "%H:%M:%S").time()


def _float_state(hass: HomeAssistant, entity_id: str | None, default: float = 0) -> float:
    """Read a float state."""
    if not entity_id:
        return default
    state = hass.states.get(entity_id)
    if state is None:
        return default
    try:
        return float(state.state)
    except (TypeError, ValueError):
        return default


def _source(hass: HomeAssistant, entity_id: str | None) -> SourceState:
    """Read a source state and attributes."""
    if not entity_id:
        return SourceState(None, {})
    state = hass.states.get(entity_id)
    if state is None:
        return SourceState(None, {})
    return SourceState(state.state, dict(state.attributes))


def _as_local(value: str | datetime | None) -> datetime | None:
    """Convert an ISO timestamp to local time."""
    if value is None:
        return None
    parsed = dt_util.parse_datetime(value) if isinstance(value, str) else value
    if parsed is None:
        return None
    return dt_util.as_local(parsed)


class NegativePriceExportGuardCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Collect source data and calculate export guard values."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )
        self.config_entry = entry
        self._control_active = False
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}_{entry.entry_id}"
        )
        self._history: dict[str, Any] = {}
        self._pending_refresh_unsub: CALLBACK_TYPE | None = None

    async def async_config_entry_first_refresh(self) -> None:
        """Load storage before the first refresh."""
        self._history = await self._store.async_load() or {}
        self._control_active = bool(self._history.get("control_active", False))
        await super().async_config_entry_first_refresh()

    @property
    def options(self) -> dict[str, Any]:
        """Return merged config data and options."""
        return {**self.config_entry.data, **self.config_entry.options}

    async def async_set_option(self, key: str, value: Any) -> None:
        """Update one runtime option."""
        options = dict(self.config_entry.options)
        options[key] = value
        self.hass.config_entries.async_update_entry(self.config_entry, options=options)
        self.async_cancel_scheduled_refresh()
        await self.async_request_refresh()

    @callback
    def async_schedule_refresh(
        self, delay: float = 5, *, replace: bool = False
    ) -> None:
        """Schedule one debounced coordinator refresh."""
        if self._pending_refresh_unsub is not None:
            if not replace:
                return
            self._pending_refresh_unsub()
            self._pending_refresh_unsub = None

        @callback
        def _request_refresh(_now: datetime) -> None:
            self._pending_refresh_unsub = None
            self.hass.async_create_task(self.async_request_refresh())

        self._pending_refresh_unsub = async_call_later(
            self.hass,
            delay,
            _request_refresh,
        )

    @callback
    def async_cancel_scheduled_refresh(self) -> None:
        """Cancel a pending debounced refresh."""
        if self._pending_refresh_unsub is None:
            return
        self._pending_refresh_unsub()
        self._pending_refresh_unsub = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Update calculated data."""
        now = dt_util.now()
        options = self.options
        history_changed = self._update_load_history(now, options)

        price = self._current_spot_price(now, options)
        negative_minutes = self._negative_price_minutes_until_window_end(now, options)
        load_curve = self._build_load_curve(now, options)
        remaining_load = self._remaining_load_estimate(now, options, load_curve)
        remaining_pv = _float_state(
            self.hass, options.get(CONF_SOLCAST_REMAINING_TODAY_SENSOR), 0
        )
        battery_capacity = _float_state(
            self.hass,
            options.get(CONF_BATTERY_CAPACITY_SENSOR),
            DEFAULT_BATTERY_CAPACITY_KWH,
        )
        battery_soc = _float_state(self.hass, options.get(CONF_BATTERY_SOC_SENSOR), 0)
        min_reserve_soc = float(
            options.get(CONF_MIN_RESERVE_SOC, DEFAULT_MIN_RESERVE_SOC)
        )
        battery_above_reserve = max(
            ((battery_soc - min_reserve_soc) / 100) * battery_capacity,
            0,
        )
        expected_surplus = round(battery_above_reserve + remaining_pv - remaining_load, 2)
        uncovered_load = max(remaining_load - remaining_pv, 0)
        battery_target_soc = min(
            min_reserve_soc + (uncovered_load / battery_capacity * 100),
            95,
        )
        recommended_export_power = self._recommended_export_power(
            now,
            options,
            remaining_load,
            remaining_pv,
            battery_capacity,
            battery_soc,
            battery_target_soc,
        )
        expected_load_power = self._expected_load_power(now, options, load_curve)
        solar_window_load_average = self._solar_window_load_average()
        future_negative = negative_minutes > 0
        threshold = float(
            options.get(
                CONF_EXPORT_SURPLUS_THRESHOLD_KWH,
                DEFAULT_EXPORT_SURPLUS_THRESHOLD_KWH,
            )
        )
        floor = float(options.get(CONF_PRICE_FLOOR, DEFAULT_PRICE_FLOOR))
        battery_export_allowed = bool(options.get(CONF_ALLOW_BATTERY_EARLY_EXPORT, True))
        soc_ok = battery_soc >= battery_target_soc if battery_export_allowed else True
        export_wanted = (
            bool(options.get(CONF_GUARD_ENABLED, True))
            and self._in_solar_window(now, options)
            and price >= floor
            and future_negative
            and soc_ok
            and expected_surplus > threshold
            and recommended_export_power > 0
        )

        data = {
            "okte_spot_price": round(price, 3),
            "negative_price_minutes_until_window_end": negative_minutes,
            "solar_window_load_7d_average": solar_window_load_average,
            "solar_window_load_today": self._solar_window_load_today(options),
            "remaining_solar_window_load_estimate": remaining_load,
            "expected_load_power": expected_load_power,
            "battery_target_soc": round(battery_target_soc),
            "expected_surplus_today": expected_surplus,
            "recommended_export_power": round(recommended_export_power),
            "export_wanted": export_wanted,
            "export_active": self._control_active,
            "sell_price": self._sell_price(price, options),
            KEY_EXPORTED_ENERGY_NEGATIVE_PRICE: round(
                float(self._history.get(KEY_EXPORTED_ENERGY_NEGATIVE_PRICE, 0)),
                4,
            ),
            KEY_EXPORTED_ENERGY_BY_AUTOMATION: round(
                float(self._history.get(KEY_EXPORTED_ENERGY_BY_AUTOMATION, 0)),
                4,
            ),
            KEY_AUTOMATION_EXPORT_SAVINGS: round(
                float(self._history.get(KEY_AUTOMATION_EXPORT_SAVINGS, 0)),
                4,
            ),
            KEY_NEGATIVE_PRICE_WASTED_POTENTIAL: round(
                float(self._history.get(KEY_NEGATIVE_PRICE_WASTED_POTENTIAL, 0)),
                4,
            ),
            ATTR_PAST_CONSUMPTION: self._history.get(ATTR_PAST_CONSUMPTION, []),
            ATTR_TODAY_LOAD_CURVE: self._history.get(
                ATTR_TODAY_LOAD_CURVE,
                {"date": now.date().isoformat(), "intervals": []},
            ),
            ATTR_PAST_LOAD_CURVES: self._history.get(ATTR_PAST_LOAD_CURVES, []),
            ATTR_LOAD_CURVE: load_curve,
            ATTR_LAST_INTERVAL_TOTAL_KWH: self._history.get(
                ATTR_LAST_INTERVAL_TOTAL_KWH
            ),
            ATTR_CURRENT_INTERVAL_INDEX: self._current_interval_index(now, options),
        }

        was_control_active = self._control_active
        try:
            await self._async_apply_control(options, data)
        except HomeAssistantError as err:
            _LOGGER.warning("Failed to apply export guard control: %s", err)
        data["export_active"] = self._control_active
        if self._update_export_accounting(price, options, was_control_active):
            data[KEY_EXPORTED_ENERGY_NEGATIVE_PRICE] = round(
                float(self._history.get(KEY_EXPORTED_ENERGY_NEGATIVE_PRICE, 0)),
                4,
            )
            data[KEY_EXPORTED_ENERGY_BY_AUTOMATION] = round(
                float(self._history.get(KEY_EXPORTED_ENERGY_BY_AUTOMATION, 0)),
                4,
            )
            data[KEY_AUTOMATION_EXPORT_SAVINGS] = round(
                float(self._history.get(KEY_AUTOMATION_EXPORT_SAVINGS, 0)),
                4,
            )
            data[KEY_NEGATIVE_PRICE_WASTED_POTENTIAL] = round(
                float(self._history.get(KEY_NEGATIVE_PRICE_WASTED_POTENTIAL, 0)),
                4,
            )
            history_changed = True
        if self._history.get("control_active") != self._control_active:
            self._history["control_active"] = self._control_active
            history_changed = True

        if history_changed:
            await self._store.async_save(self._history)

        return data

    async def _async_apply_control(
        self,
        options: dict[str, Any],
        data: dict[str, Any],
    ) -> None:
        """Apply the calculated export mode to the inverter."""
        work_mode_entity = options.get(CONF_INVERTER_WORK_MODE_SELECT)
        export_power_entity = options.get(CONF_EXPORT_SURPLUS_POWER_NUMBER)
        if not work_mode_entity or not export_power_entity:
            return

        price = float(data.get("okte_spot_price", 999))
        floor = float(options.get(CONF_PRICE_FLOOR, DEFAULT_PRICE_FLOOR))
        battery_soc = _float_state(self.hass, options.get(CONF_BATTERY_SOC_SENSOR), 0)
        export_surplus_on = (
            _source(self.hass, options.get(CONF_EXPORT_SURPLUS_SWITCH)).state == "on"
        )
        work_mode = _source(self.hass, work_mode_entity).state
        guard_enabled = bool(options.get(CONF_GUARD_ENABLED, True))
        full_battery = battery_soc >= 99

        if full_battery and export_surplus_on:
            full_battery_target = self._max_allowed_export_power(options)
        else:
            full_battery_target = 0

        if not guard_enabled:
            if self._control_active:
                await self._async_select_work_mode(
                    work_mode_entity,
                    work_mode,
                    MODE_ZERO_EXPORT_TO_CT,
                )
                if full_battery_target > 0:
                    await self._async_set_export_power_if_needed(
                        export_power_entity,
                        full_battery_target,
                    )
            self._control_active = False
            return

        if price < floor:
            await self._async_select_work_mode(
                work_mode_entity,
                work_mode,
                MODE_ZERO_EXPORT_TO_CT,
            )
            if full_battery_target > 0:
                await self._async_set_export_power_if_needed(
                    export_power_entity,
                    full_battery_target,
                )
            self._control_active = False
            return

        if (
            full_battery_target > 0
            and work_mode == MODE_ZERO_EXPORT_TO_CT
            and not bool(data.get("export_wanted"))
        ):
            await self._async_set_export_power_if_needed(
                export_power_entity,
                full_battery_target,
            )
            self._control_active = False
            return

        if bool(data.get("export_wanted")):
            target = float(data.get("recommended_export_power", 0))
            if full_battery:
                target = min(
                    max(target, self._live_surplus_power(options)),
                    self._max_allowed_export_power(options),
                )
            await self._async_set_export_power_if_needed(export_power_entity, target)
            await self._async_select_work_mode(
                work_mode_entity,
                work_mode,
                MODE_EXPORT_FIRST,
            )
            self._control_active = True
            return

        if self._control_active:
            await self._async_select_work_mode(
                work_mode_entity,
                work_mode,
                MODE_ZERO_EXPORT_TO_CT,
            )
            self._control_active = False

    async def _async_select_work_mode(
        self,
        entity_id: str,
        current_mode: str | None,
        target_mode: str,
    ) -> None:
        """Set inverter work mode if needed."""
        if current_mode == target_mode:
            return
        await self.hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": entity_id, "option": target_mode},
            blocking=True,
        )

    async def _async_set_export_power_if_needed(
        self,
        entity_id: str,
        target_w: float,
    ) -> None:
        """Set export power if the difference is meaningful."""
        if target_w <= 0:
            return
        current_w = _float_state(self.hass, entity_id, 0)
        if abs(current_w - target_w) <= 50:
            return
        await self.hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": entity_id, "value": round(target_w)},
            blocking=True,
        )

    def _max_allowed_export_power(self, options: dict[str, Any]) -> float:
        """Return the configured hard export-power ceiling."""
        return min(
            float(options.get(CONF_MAX_EXPORT_POWER_W, DEFAULT_MAX_EXPORT_POWER_W)),
            _float_state(
                self.hass,
                options.get(CONF_GRID_MAX_EXPORT_POWER_NUMBER),
                DEFAULT_MAX_EXPORT_POWER_W,
            ),
        )

    def _live_surplus_power(self, options: dict[str, Any]) -> float:
        """Return current PV surplus with a small buffer."""
        return max(
            _float_state(self.hass, options.get(CONF_PV_POWER_SENSOR), 0)
            - _float_state(self.hass, options.get(CONF_LOAD_POWER_SENSOR), 0)
            - 200,
            0,
        )

    def _update_export_accounting(
        self,
        spot_price: float,
        options: dict[str, Any],
        was_control_active: bool,
    ) -> bool:
        """Update cumulative export accounting from total export delta."""
        total_export = _float_state(
            self.hass,
            options.get(CONF_TOTAL_ENERGY_EXPORT_SENSOR),
            -1,
        )
        if total_export < 0:
            return False

        previous_export = self._history.get(KEY_LAST_TOTAL_ENERGY_EXPORT)
        self._history[KEY_LAST_TOTAL_ENERGY_EXPORT] = total_export
        if previous_export is None:
            return True

        delta = total_export - float(previous_export)
        if delta <= 0:
            return delta < 0

        if spot_price < 0:
            self._history[KEY_EXPORTED_ENERGY_NEGATIVE_PRICE] = (
                float(self._history.get(KEY_EXPORTED_ENERGY_NEGATIVE_PRICE, 0)) + delta
            )
            self._history[KEY_NEGATIVE_PRICE_WASTED_POTENTIAL] = (
                float(self._history.get(KEY_NEGATIVE_PRICE_WASTED_POTENTIAL, 0))
                + delta * self._hypothetical_negative_price_value(options)
            )

        if was_control_active:
            self._history[KEY_EXPORTED_ENERGY_BY_AUTOMATION] = (
                float(self._history.get(KEY_EXPORTED_ENERGY_BY_AUTOMATION, 0)) + delta
            )
            self._history[KEY_AUTOMATION_EXPORT_SAVINGS] = (
                float(self._history.get(KEY_AUTOMATION_EXPORT_SAVINGS, 0))
                + delta * self._sell_price(spot_price, options)
            )

        return True

    def _window_bounds(
        self, now: datetime, options: dict[str, Any]
    ) -> tuple[datetime, datetime]:
        """Return today's solar window bounds."""
        start_time = _parse_time(
            options.get(CONF_SOLAR_WINDOW_START, DEFAULT_SOLAR_WINDOW_START),
            DEFAULT_SOLAR_WINDOW_START,
        )
        end_time = _parse_time(
            options.get(CONF_SOLAR_WINDOW_END, DEFAULT_SOLAR_WINDOW_END),
            DEFAULT_SOLAR_WINDOW_END,
        )
        return (
            datetime.combine(now.date(), start_time, tzinfo=now.tzinfo),
            datetime.combine(now.date(), end_time, tzinfo=now.tzinfo),
        )

    def _in_solar_window(self, now: datetime, options: dict[str, Any]) -> bool:
        """Return if now is inside the solar window."""
        start, end = self._window_bounds(now, options)
        return start <= now < end

    def _current_interval_index(
        self, now: datetime, options: dict[str, Any]
    ) -> int | None:
        """Return the current 15-minute interval index."""
        start, end = self._window_bounds(now, options)
        if now < start or now >= end:
            return None
        idx = int((now - start).total_seconds() / (INTERVAL_MINUTES * 60))
        return idx if 0 <= idx < INTERVALS_PER_SOLAR_WINDOW else None

    def _previous_interval_index(
        self, now: datetime, options: dict[str, Any]
    ) -> int | None:
        """Return the previous closed 15-minute interval index."""
        start, end = self._window_bounds(now, options)
        if now <= start:
            return None
        idx = int((min(now, end) - start).total_seconds() / (INTERVAL_MINUTES * 60)) - 1
        return idx if 0 <= idx < INTERVALS_PER_SOLAR_WINDOW else None

    def _solar_window_load_today(self, options: dict[str, Any]) -> float:
        """Return today's solar-window load."""
        start_total = float(self._history.get("solar_window_start_load_kwh", 0))
        current_total = _float_state(
            self.hass, options.get(CONF_TODAY_LOAD_CONSUMPTION_SENSOR), 0
        )
        return round(max(current_total - start_total, 0), 2)

    def _solar_window_load_average(self) -> float:
        """Return the average solar-window load from stored samples."""
        values = [
            float(item.get("consumption", 0))
            for item in self._history.get(ATTR_PAST_CONSUMPTION, [])
        ]
        return round(sum(values) / len(values), 2) if values else 8

    def _update_load_history(self, now: datetime, options: dict[str, Any]) -> bool:
        """Update persisted load history."""
        changed = False
        today = now.date().isoformat()
        current_total = _float_state(
            self.hass, options.get(CONF_TODAY_LOAD_CONSUMPTION_SENSOR), 0
        )
        start, end = self._window_bounds(now, options)

        if now >= start and self._history.get("solar_window_start_date") != today:
            self._history["solar_window_start_date"] = today
            self._history["solar_window_start_load_kwh"] = current_total
            self._history["solar_window_start_recorded"] = now.isoformat()
            self._history[ATTR_LAST_INTERVAL_TOTAL_KWH] = current_total
            self._history[ATTR_CURRENT_INTERVAL_INDEX] = None
            self._history[ATTR_TODAY_LOAD_CURVE] = {"date": today, "intervals": []}
            changed = True

        old_today = self._history.get(
            ATTR_TODAY_LOAD_CURVE, {"date": today, "intervals": []}
        )
        old_intervals = (
            old_today.get("intervals", []) if old_today.get("date") == today else []
        )
        previous_idx = self._previous_interval_index(now, options)

        if now > start and now <= end and previous_idx is not None:
            last_idx_value = self._history.get(ATTR_CURRENT_INTERVAL_INDEX)
            last_idx = int(last_idx_value) if last_idx_value is not None else None
            should_record_interval = last_idx is None or previous_idx > last_idx

            if should_record_interval:
                has_previous_baseline = (
                    last_idx is not None and last_idx == previous_idx - 1
                )
                first_sample_mid_window = (
                    len(old_intervals) == 0
                    and previous_idx > 0
                    and not has_previous_baseline
                )
                if not first_sample_mid_window:
                    previous_total = (
                        self._history.get("solar_window_start_load_kwh", current_total)
                        if len(old_intervals) == 0 and previous_idx == 0
                        else self._history.get(ATTR_LAST_INTERVAL_TOTAL_KWH, current_total)
                    )
                    delta = round(max(current_total - float(previous_total), 0), 3)
                    interval = self._interval_dict(start, previous_idx, delta)
                    intervals = [
                        item
                        for item in old_intervals
                        if int(item.get("index", -1)) != previous_idx
                    ]
                    intervals.append(interval)
                    intervals.sort(key=lambda item: int(item["index"]))
                    self._history[ATTR_TODAY_LOAD_CURVE] = {
                        "date": today,
                        "intervals": intervals,
                    }
                self._history[ATTR_LAST_INTERVAL_TOTAL_KWH] = current_total
                self._history[ATTR_CURRENT_INTERVAL_INDEX] = previous_idx
                changed = True

        if now >= end and self._history.get("last_archived_date") != today:
            intervals = self._history.get(ATTR_TODAY_LOAD_CURVE, {}).get(
                "intervals", []
            )
            if len(intervals) >= MIN_COMPLETE_LOAD_CURVE_INTERVALS:
                past_curves = [
                    item
                    for item in self._history.get(ATTR_PAST_LOAD_CURVES, [])
                    if item.get("date") != today
                ]
                self._history[ATTR_PAST_LOAD_CURVES] = (
                    [{"date": today, "intervals": intervals}] + past_curves
                )[:7]

                sample = self._solar_window_load_today(options)
                if sample > 0:
                    past_consumption = [
                        item
                        for item in self._history.get(ATTR_PAST_CONSUMPTION, [])
                        if item.get("date") != today
                    ]
                    self._history[ATTR_PAST_CONSUMPTION] = (
                        [{"date": today, "consumption": sample}] + past_consumption
                    )[:7]
            self._history["last_archived_date"] = today
            changed = True

        return changed

    def _interval_dict(
        self, window_start: datetime, idx: int, consumption_kwh: float
    ) -> dict[str, Any]:
        """Build one interval dictionary."""
        interval_start = window_start + timedelta(minutes=idx * INTERVAL_MINUTES)
        interval_end = interval_start + timedelta(minutes=INTERVAL_MINUTES)
        return {
            "index": idx,
            "start": interval_start.strftime("%H:%M:%S"),
            "end": interval_end.strftime("%H:%M:%S"),
            "consumption_kwh": consumption_kwh,
        }

    def _build_load_curve(
        self, now: datetime, options: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Build the expected 15-minute load curve."""
        start, _ = self._window_bounds(now, options)
        curves = self._history.get(ATTR_PAST_LOAD_CURVES, [])
        totals = [
            float(item.get("consumption", 0))
            for item in self._history.get(ATTR_PAST_CONSUMPTION, [])
        ]
        fallback_total = sum(totals) / len(totals) if totals else 8
        fallback_interval = fallback_total / INTERVALS_PER_SOLAR_WINDOW
        result: list[dict[str, Any]] = []

        for idx in range(INTERVALS_PER_SOLAR_WINDOW):
            values: list[float] = []
            for day in curves:
                for item in day.get("intervals", []):
                    if int(item.get("index", -1)) == idx:
                        values.append(float(item.get("consumption_kwh", 0)))
            avg = sum(values) / len(values) if values else fallback_interval
            interval_start = start + timedelta(minutes=idx * INTERVAL_MINUTES)
            interval_end = interval_start + timedelta(minutes=INTERVAL_MINUTES)
            result.append(
                {
                    "index": idx,
                    "start": interval_start.strftime("%H:%M:%S"),
                    "end": interval_end.strftime("%H:%M:%S"),
                    "consumption_kwh": round(avg, 3),
                    "power_w": round(avg * 4000),
                    "samples": len(values),
                }
            )
        return result

    def _expected_load_power(
        self, now: datetime, options: dict[str, Any], load_curve: list[dict[str, Any]]
    ) -> float:
        """Return expected load power for the current interval."""
        idx = self._current_interval_index(now, options)
        if idx is None:
            return 0
        for item in load_curve:
            if int(item.get("index", -1)) == idx:
                return float(item.get("power_w", 0))
        return 0

    def _remaining_load_estimate(
        self, now: datetime, options: dict[str, Any], load_curve: list[dict[str, Any]]
    ) -> float:
        """Estimate remaining load until the solar window end."""
        _, end = self._window_bounds(now, options)
        if now >= end:
            return 0
        margin = float(
            options.get(CONF_CONSUMPTION_MARGIN_KWH, DEFAULT_CONSUMPTION_MARGIN_KWH)
        )
        idle_power = float(
            options.get(CONF_TYPICAL_IDLE_POWER_W, DEFAULT_TYPICAL_IDLE_POWER_W)
        )
        hours_left = max((end - now).total_seconds() / 3600, 0)
        minimum_baseload = idle_power * hours_left / 1000
        remaining = self._curve_energy_between(load_curve, now, end)
        return round(max(remaining + margin, minimum_baseload), 2)

    def _curve_energy_between(
        self,
        load_curve: list[dict[str, Any]],
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """Integrate curve energy between two times."""
        total = 0.0
        for item in load_curve:
            interval_start = datetime.combine(
                start_time.date(),
                datetime.strptime(item["start"], "%H:%M:%S").time(),
                tzinfo=start_time.tzinfo,
            )
            interval_end = datetime.combine(
                start_time.date(),
                datetime.strptime(item["end"], "%H:%M:%S").time(),
                tzinfo=start_time.tzinfo,
            )
            a = max(interval_start, start_time)
            b = min(interval_end, end_time)
            duration = (interval_end - interval_start).total_seconds()
            if b > a and duration > 0:
                total += float(item.get("consumption_kwh", 0)) * (
                    (b - a).total_seconds() / duration
                )
        return total

    def _current_spot_price(self, now: datetime, options: dict[str, Any]) -> float:
        """Read current OKTE price from the prices attribute."""
        source = _source(self.hass, options.get(CONF_OKTE_PRICE_SENSOR))
        prices = source.attributes.get("prices") or []
        for item in prices:
            start = _as_local(item.get("start"))
            if start is None:
                continue
            if start <= now < start + timedelta(minutes=15):
                return float(item.get("price", 999))
        try:
            return float(source.state)
        except (TypeError, ValueError):
            return 999

    def _negative_price_minutes_until_window_end(
        self, now: datetime, options: dict[str, Any]
    ) -> int:
        """Count negative-price minutes until the solar window end."""
        _, end = self._window_bounds(now, options)
        floor = float(options.get(CONF_PRICE_FLOOR, DEFAULT_PRICE_FLOOR))
        source = _source(self.hass, options.get(CONF_OKTE_PRICE_SENSOR))
        minutes = 0
        for item in source.attributes.get("prices") or []:
            start = _as_local(item.get("start"))
            if start is None:
                continue
            if start >= now and start < end and float(item.get("price", 999)) < floor:
                minutes += 15
        return minutes

    def _recommended_export_power(
        self,
        now: datetime,
        options: dict[str, Any],
        remaining_load: float,
        remaining_pv: float,
        battery_capacity: float,
        battery_soc: float,
        battery_target_soc: float,
    ) -> float:
        """Calculate recommended strategic export power."""
        floor = float(options.get(CONF_PRICE_FLOOR, DEFAULT_PRICE_FLOOR))
        price = self._current_spot_price(now, options)
        if price < floor or not self._in_solar_window(now, options):
            return 0

        neg_start = self._next_negative_block_start(now, options)
        if neg_start is None:
            return 0

        minutes_before_negative = max((neg_start - now).total_seconds() / 60, 0)
        if minutes_before_negative <= 0:
            return 0

        threshold = float(
            options.get(
                CONF_EXPORT_SURPLUS_THRESHOLD_KWH,
                DEFAULT_EXPORT_SURPLUS_THRESHOLD_KWH,
            )
        )
        max_w = min(
            float(options.get(CONF_MAX_EXPORT_POWER_W, DEFAULT_MAX_EXPORT_POWER_W)),
            _float_state(
                self.hass,
                options.get(CONF_GRID_MAX_EXPORT_POWER_NUMBER),
                DEFAULT_MAX_EXPORT_POWER_W,
            ),
        )
        battery_now = battery_capacity * battery_soc / 100
        total_excess = max(
            battery_now + remaining_pv - remaining_load - battery_capacity + threshold,
            0,
        )
        available_export = max_w * minutes_before_negative / 60 / 1000
        energy_needed = min(total_excess, available_export)
        raw_w = energy_needed * 1000 / (minutes_before_negative / 60)
        live_surplus = max(
            _float_state(self.hass, options.get(CONF_PV_POWER_SENSOR), 0)
            - _float_state(self.hass, options.get(CONF_LOAD_POWER_SENSOR), 0)
            - 200,
            0,
        )

        battery_can_be_used = (
            bool(options.get(CONF_ALLOW_BATTERY_EARLY_EXPORT, True))
            and battery_soc > battery_target_soc
        )
        if not battery_can_be_used:
            raw_w = min(raw_w, live_surplus)

        if raw_w <= 0:
            return 0
        min_w = float(options.get(CONF_MIN_EXPORT_POWER_W, DEFAULT_MIN_EXPORT_POWER_W))
        if battery_can_be_used:
            return min(max(raw_w, min_w), max_w)
        return min(raw_w, max_w)

    def _next_negative_block_start(
        self, now: datetime, options: dict[str, Any]
    ) -> datetime | None:
        """Find the next negative-price block start."""
        _, end = self._window_bounds(now, options)
        floor = float(options.get(CONF_PRICE_FLOOR, DEFAULT_PRICE_FLOOR))
        source = _source(self.hass, options.get(CONF_OKTE_PRICE_SENSOR))
        for item in source.attributes.get("prices") or []:
            start = _as_local(item.get("start"))
            if start is None:
                continue
            interval_end = start + timedelta(minutes=15)
            if (
                interval_end > now
                and start < end
                and float(item.get("price", 999)) < floor
            ):
                return max(start, now)
        return None

    def _sell_price(self, spot_price: float, options: dict[str, Any]) -> float:
        """Estimate sell price in EUR/kWh."""
        if spot_price < 0:
            return 0
        return round(
            _float_state(
                self.hass,
                options.get(CONF_NIGHT_TARIFF_NUMBER),
                DEFAULT_NIGHT_TARIFF_EUR_KWH,
            )
            * 0.88,
            5,
        )

    def _hypothetical_negative_price_value(self, options: dict[str, Any]) -> float:
        """Estimate value lost when export happens during negative spot price."""
        return round(
            _float_state(
                self.hass,
                options.get(CONF_NIGHT_TARIFF_NUMBER),
                DEFAULT_NIGHT_TARIFF_EUR_KWH,
            )
            * 0.88,
            5,
        )
