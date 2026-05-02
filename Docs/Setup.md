# Detailed Setup Guide

This guide walks through installing and tuning the negative-price export guard package in Home Assistant. The main README gives the short version; this file is for first deployment, adaptation to another inverter, and tuning.

## 1. Confirm The Required Integrations

### OKTE Prices

Recommended integration:

- [OKTE DAM](https://github.com/rgildein/okte-home-assistant)

The package expects an OKTE price entity like:

```yaml
sensor.okte_ceny_elektriny_prices
```

This entity must expose a `prices` attribute containing 15-minute periods with timestamps and prices. The package calculates the current price from this attribute instead of relying only on the entity state, because the state may update later than the real 15-minute price boundary.

### Solcast PV Forecast

Recommended integration:

- [Solcast Solar](https://github.com/BJReplay/ha-solcast-solar)

The package expects two Solcast entities:

```yaml
sensor.solcast_pv_forecast_predpoved_dnes
sensor.solcast_pv_forecast_predpoved_zostavajuca_dnes
```

The first one must expose `detailedForecast`; the second one should represent remaining forecasted production for today in kWh. The package uses the detailed forecast for timing around the next negative-price window and the remaining-production sensor for whole-day surplus and battery-capacity calculations.

### Inverter Integration

The package was developed around Deye/Solarman-style entities.

Recommended Solarman integration:

- [ha-solarman](https://github.com/davidrapan/ha-solarman)

At minimum, Home Assistant must be able to read battery SOC, PV power, house load power, daily PV production, daily house load consumption, total grid export, current export settings, and it must be able to change inverter work mode and set the grid export power limit.

## 2. Enable Home Assistant Packages

If you do not already use packages, add this to `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Then create the folder:

```text
config/packages
```

Copy the package file into it:

```text
config/packages/negative_price_export_guard.yaml
```

## 3. Create The Energy Value Helper

The package expects this helper:

```yaml
input_number.cena_elektriny_nocny_tarif
```

Create it from the Home Assistant UI:

```text
Settings -> Devices & services -> Helpers -> Create helper -> Number
```

Suggested settings:

| Field | Value |
|---|---|
| Name | Cena elektriny nočný tarif |
| Minimum | `0` |
| Maximum | something above your tariff, for example `1` |
| Step | `0.001` |
| Unit | `EUR/kWh` |
| Mode | box |

This value is used to estimate what exported energy would have been worth if it had counted into your virtual battery. If you are unsure, start with your approximate night tariff in EUR/kWh.

## 4. Map Your Entity IDs

Open `negative_price_export_guard.yaml` and check every entity in the expected-entities section.

| Purpose | Default entity |
|---|---|
| OKTE prices | `sensor.okte_ceny_elektriny_prices` |
| Solcast forecast today with detailed forecast | `sensor.solcast_pv_forecast_predpoved_dnes` |
| Solcast remaining production today | `sensor.solcast_pv_forecast_predpoved_zostavajuca_dnes` |
| Daily house load consumption | `sensor.inverter_today_load_consumption` |
| Total grid export | `sensor.inverter_total_energy_export` |
| Daily PV production | `sensor.inverter_today_production` |
| Battery SOC | `sensor.inverter_battery` |
| Battery capacity | `sensor.inverter_battery_capacity` |
| Current PV power | `sensor.inverter_pv_power` |
| Current load power | `sensor.inverter_load_power` |
| Inverter mode select | `select.inverter_work_mode` |
| PV surplus export switch | `switch.inverter_export_surplus` |
| Export power limit | `number.inverter_export_surplus_power` |
| Maximum inverter/grid export limit | `number.solarny_menic_grid_max_export_power` |
| Energy value helper | `input_number.cena_elektriny_nocny_tarif` |

If your entities use different names, replace all occurrences in the package. Do not try to put entity IDs into `input_text` helpers for triggers; Home Assistant triggers need real entity IDs in the YAML.

## 5. Check Units

The package assumes:

| Entity | Expected unit |
|---|---|
| `sensor.inverter_pv_power` | W |
| `sensor.inverter_load_power` | W |
| `number.inverter_export_surplus_power` | W |
| `number.solarny_menic_grid_max_export_power` | W |
| `sensor.inverter_today_load_consumption` | kWh |
| `sensor.inverter_today_production` | kWh |
| `sensor.inverter_total_energy_export` | kWh |
| `sensor.solcast_pv_forecast_predpoved_zostavajuca_dnes` | kWh |
| `sensor.inverter_battery` | % |
| `sensor.inverter_battery_capacity` | kWh |

If your inverter exposes power in kW instead of W, adjust the calculations that use PV power, load power, and export power.

## 6. Confirm Inverter Mode Names

The package expects these exact options in `select.inverter_work_mode`:

```text
Export First
Zero Export To CT
```

Check this in Home Assistant Developer Tools. If your inverter uses different option text, update the automation actions.

## 7. Run A Configuration Check

In Home Assistant:

```text
Settings -> Developer Tools -> YAML -> Check configuration
```

Do not restart until this passes. Common causes of validation errors are wrong entity IDs, duplicated YAML keys, indentation issues, invalid options under YAML helpers, and inverter mode option names that do not match your integration.

## 8. Restart And Verify Entities

After restart, verify the external entities above and search for package-created entities starting with:

```text
export_optimizer_
```

The most important created entities are:

```text
sensor.export_optimizer_okte_spotova_cena
sensor.export_optimizer_solar_window_load_7d_average
sensor.export_optimizer_expected_load_power
sensor.export_optimizer_remaining_solar_window_load_estimate
sensor.export_optimizer_recommended_export_power
sensor.export_optimizer_expected_surplus_today
binary_sensor.export_optimizer_export_wanted
input_boolean.export_optimizer_export_guard_enabled
input_boolean.export_optimizer_allow_battery_early_export
input_boolean.export_optimizer_export_guard_active
input_number.export_optimizer_typical_idle_power_w
```

The old package-created sensor `sensor.export_optimizer_remaining_pv_forecast_today` is no longer used. The package now uses the Solcast remaining-production sensor directly.

## 9. First-Day Behavior And Learning

The package records the house-load counter at 07:00. During the 07:00-18:00 solar window, it stores one load delta every 15 minutes. At 18:00, it saves the completed daily curve and keeps the last seven completed daily curves.

`sensor.export_optimizer_solar_window_load_7d_average` has these learning attributes:

| Attribute | Meaning |
|---|---|
| `past_consumption` | Last 7 total solar-window consumption samples |
| `today_load_curve` | Today's already measured 15-minute intervals |
| `past_load_curves` | Last 7 completed daily 15-minute curves |
| `load_curve` | Average 15-minute curve used by the optimizer |
| `last_interval_total_kwh` | Internal counter snapshot for the next interval delta |
| `current_interval_index` | Current 15-minute slot in the 07:00-18:00 window |

The `load_curve` entries contain:

```yaml
index: 0
start: "07:00:00"
end: "07:15:00"
consumption_kwh: 0.12
power_w: 480
samples: 4
```

`consumption_kwh` is the expected energy use in that 15-minute interval. `power_w` is the same value converted to average watts for easier dashboards and calculations.

On the first day, there is little or no history. The package falls back to the daily average spread across the solar window. The curve becomes better after every completed day and should be most useful after about a week.

## 10. Load-Curve Based Planning

The package no longer assumes that house load is constant through the solar window. These sensors use the 15-minute load curve:

| Entity | How it uses the curve |
|---|---|
| `sensor.export_optimizer_expected_load_power` | Shows expected house-load power for the current 15-minute slot |
| `sensor.export_optimizer_remaining_solar_window_load_estimate` | Sums the remaining intervals from `load_curve` and applies the safety margin |
| `sensor.export_optimizer_expected_surplus_today` | Uses the improved remaining-load estimate before calculating surplus |
| `sensor.export_optimizer_recommended_export_power` | Uses the improved load estimate when deciding whether to export before a negative-price block |

This is especially useful if the house has predictable daytime peaks, such as cooking, water heating, heat pump cycles, or EV/PHEV charging that sometimes happens inside the solar window.

## 11. Recommended Initial Tuning

Start conservatively:

| Helper | Suggested value |
|---|---:|
| `input_number.export_optimizer_min_reserve_soc` | `40` |
| `input_number.export_optimizer_consumption_margin_kwh` | `2` |
| `input_number.export_optimizer_typical_idle_power_w` | `200-500` |
| `input_number.export_optimizer_export_surplus_threshold_kwh` | `1` |
| `input_number.export_optimizer_min_export_power_w` | `500` |
| `input_number.export_optimizer_max_export_power_w` | `3000` |
| `input_number.export_optimizer_price_floor` | `0` |

The typical idle power should include the usual minimum house load and inverter self-consumption during the remaining solar window. It prevents the remaining-load estimate from falling unrealistically to zero too early in the day.

## 12. Expected Surplus Logic

`sensor.export_optimizer_expected_surplus_today` estimates only energy that is likely to be truly surplus after:

- remaining Solcast production,
- estimated remaining solar-window load from the 15-minute curve,
- remaining battery charging capacity.

This means the sensor may stay at `0` even on sunny days if the battery still has enough empty capacity to absorb the expected PV production.

## 13. Battery-Saving Mode

If you turn off:

```text
input_boolean.export_optimizer_allow_battery_early_export
```

then the recommended export power is capped to the current live PV surplus:

```text
PV power - house load power - 200 W
```

In this mode, the package does not force `input_number.export_optimizer_min_export_power_w`, because doing so could discharge the battery when live PV surplus is small.

## 14. Full-Battery Anti-Curtailment

When the battery is above 99%, `switch.inverter_export_surplus` is on, the inverter is in `Zero Export To CT`, and strategic export is not currently wanted, the package sets:

```text
number.inverter_export_surplus_power = min(
  number.solarny_menic_grid_max_export_power,
  input_number.export_optimizer_max_export_power_w
)
```

This helps avoid PV curtailment when the battery is full. This branch respects `input_boolean.export_optimizer_export_guard_enabled` and clears `input_boolean.export_optimizer_export_guard_active` if needed.

## 15. How To Tune

### If Energy Still Exports During Negative Prices

Try these in order:

- Check whether `sensor.export_optimizer_expected_load_power` looks realistic for the current time of day.
- Increase `input_number.export_optimizer_max_export_power_w` if the inverter and grid connection allow it.
- Enable `input_boolean.export_optimizer_allow_battery_early_export` if battery-saving mode is too restrictive.
- Check whether Solcast is underestimating production or whether battery capacity/SOC entities are inaccurate.
- Increase `input_number.export_optimizer_export_surplus_threshold_kwh` only if you want the algorithm to react to larger expected surpluses.

Do not blindly increase `input_number.export_optimizer_consumption_margin_kwh`: a higher consumption margin tells the algorithm to expect more local use, which can reduce early export.

### If The Battery Discharges Too Much

Increase:

```text
input_number.export_optimizer_min_reserve_soc
```

or disable:

```text
input_boolean.export_optimizer_allow_battery_early_export
```

### If PV Is Curtailed When The Battery Is Full

Check these first:

```text
switch.inverter_export_surplus
number.solarny_menic_grid_max_export_power
input_number.export_optimizer_max_export_power_w
```

Then increase `input_number.export_optimizer_max_export_power_w` if your inverter and grid connection allow it.

## 16. Suggested Dashboard

A simple debug dashboard should include:

```text
sensor.export_optimizer_okte_spotova_cena
sensor.export_optimizer_negative_price_minutes_until_18
sensor.export_optimizer_solar_window_load_7d_average
sensor.export_optimizer_expected_load_power
sensor.export_optimizer_remaining_solar_window_load_estimate
sensor.export_optimizer_recommended_export_power
binary_sensor.export_optimizer_export_wanted
input_boolean.export_optimizer_export_guard_enabled
input_boolean.export_optimizer_allow_battery_early_export
input_boolean.export_optimizer_export_guard_active
sensor.export_optimizer_expected_surplus_today
sensor.export_optimizer_battery_target_soc
input_number.export_optimizer_typical_idle_power_w
switch.inverter_export_surplus
number.inverter_export_surplus_power
number.solarny_menic_grid_max_export_power
select.inverter_work_mode
sensor.inverter_battery
sensor.inverter_pv_power
sensor.inverter_load_power
sensor.solcast_pv_forecast_predpoved_zostavajuca_dnes
```

For an easier setup, use [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) to automatically list all entities created by this project. The `custom:auto-entities` card must be installed in Home Assistant, for example through HACS.

```yaml
type: custom:auto-entities
card:
  type: entities
  title: Export Optimizér
  show_header_toggle: false
filter:
  include:
    - entity_id: /export_optimizer/
      sort:
        method: entity_id
  exclude:
    - options: {}
      entity_id: input_number.export_optimizer_solar_window_start_load_kwh
    - options: {}
      entity_id: input_datetime.export_optimizer_solar_window_start_recorded
```

The card filters entities by `export_optimizer` in the entity ID and hides the two technical morning-record helpers that users normally do not need to edit.

## 17. Accounting Sensors

The package creates cumulative sensors for tracking results:

| Entity | Meaning |
|---|---|
| `sensor.export_optimizer_exported_energy_during_negative_spot_price` | kWh exported during negative spot prices |
| `sensor.export_optimizer_exported_energy_by_automation` | kWh exported while the automation was actively controlling export |
| `sensor.export_optimizer_automation_export_savings` | Estimated value saved by automated export |
| `sensor.export_optimizer_negative_price_wasted_potential` | Estimated value lost due to export during negative prices |

These are cumulative sensors. For daily values, use graph/statistics cards that calculate a daily difference.

## 18. Performance Notes

The package uses trigger-based template sensors on purpose. Avoid turning templates containing these into regular triggerless template sensors:

```text
now()
today_at()
state_attr(... prices ...)
state_attr(... detailedForecast ...)
```

The load curve is also trigger-based and updates every 15 minutes. That is intentional: it stores useful history without recalculating large templates every minute.

## 19. Safety Checklist

Before leaving the automation enabled unattended:

- Confirm the inverter mode changes are correct.
- Confirm export power limits are reasonable for your inverter and grid connection.
- Confirm negative spot-price periods force the inverter back to `Zero Export To CT`.
- Confirm `sensor.export_optimizer_okte_spotova_cena` matches the real current OKTE period.
- Confirm the Solcast remaining-production sensor has the expected unit and value.
- Confirm `sensor.export_optimizer_expected_load_power` is plausible after a few days of learning.
- Confirm the battery reserve is high enough for your household.
- Start with a low max export power and increase gradually.

## 20. Adapting To Other Countries Or Providers

The idea is not Slovakia-specific, but the price source and supplier rules are. To adapt it elsewhere, replace the OKTE price entity, price parsing if needed, the value calculation, inverter mode names, export-control entities, and the solar window if local PV production differs.

The core concept remains the same: create battery headroom before negative-price windows, avoid strategic export during negative prices, prevent unnecessary curtailment when useful, learn the home's daytime load curve, and track whether the tuning is working.
