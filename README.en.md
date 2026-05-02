# Home Assistant: export protection during negative spot prices

A Home Assistant automation package that helps solar PV owners avoid unnecessary electricity export during negative spot-price periods. The project was created for Slovak conditions, especially for cases where a supplier does not count electricity exported during negative prices into a virtual battery or similar credit-based service.

Typical example: on a sunny day the battery reaches 100%, the PV system has surplus production, but the OKTE spot price is negative. If electricity is exported to the grid at that moment, it may have zero value for the virtual battery. This package tries to create battery headroom before the negative-price window and, when the battery is already full, avoid unnecessary PV curtailment.

Slovak version: [README.md](README.md)

## What It Does

- Calculates the current OKTE spot price from the `prices` attribute, not only from the sensor state.
- Looks for future price periods below the configured export floor until 18:00.
- Learns house consumption during the solar window, 07:00-18:00, from the previous 7 days.
- Builds a 15-minute house-load curve and uses it instead of a flat daytime average.
- Exposes the current expected house-load power through `sensor.export_optimizer_expected_load_power`.
- Uses the Solcast daily forecast, detailed forecast, and remaining-production-today sensor.
- Calculates expected surplus after accounting for remaining load and remaining battery capacity.
- Switches the inverter to `Export First` only when it needs to strategically create battery headroom.
- In battery-saving mode, caps export to live PV surplus without forcing the minimum export power.
- When the battery is full in `Zero Export To CT`, raises the export limit to avoid unnecessary PV curtailment.
- Tracks exported energy during negative prices, energy exported by the automation, estimated savings, and wasted potential.

## Who This Is For

This project is mainly intended for users who have:

- solar PV with a battery,
- Home Assistant,
- a Deye or similar hybrid inverter exposed through Solarman or another integration,
- OKTE spot prices,
- a Solcast PV forecast,
- a supplier or virtual battery service where exports during negative prices have no value.

The package is prepared around Deye/Solarman-style entities, but it can be adapted to other inverters if Home Assistant exposes equivalent entities.

## Requirements

### Integrations

- **[OKTE DAM](https://github.com/rgildein/okte-home-assistant)** or a similar integration with spot prices and a `prices` attribute.
- **[Solcast](https://github.com/BJReplay/ha-solcast-solar)** with daily forecast, `detailedForecast`, and remaining-production-today sensor.
- **[Solarman](https://github.com/davidrapan/ha-solarman) / Deye** or another inverter integration that can read battery state, change export mode, and set export limits.

### Expected Entities

| Purpose | Default entity |
|---|---|
| OKTE prices with `prices` attribute | `sensor.okte_ceny_elektriny_prices` |
| Solcast forecast for today with `detailedForecast` | `sensor.solcast_pv_forecast_predpoved_dnes` |
| Solcast remaining production today | `sensor.solcast_pv_forecast_predpoved_zostavajuca_dnes` |
| Daily house load consumption in kWh | `sensor.inverter_today_load_consumption` |
| Total grid export in kWh | `sensor.inverter_total_energy_export` |
| Daily PV production in kWh | `sensor.inverter_today_production` |
| Battery SOC in % | `sensor.inverter_battery` |
| Battery capacity in kWh | `sensor.inverter_battery_capacity` |
| Current PV power in W | `sensor.inverter_pv_power` |
| Current house load power in W | `sensor.inverter_load_power` |
| Inverter work mode | `select.inverter_work_mode` |
| PV surplus export switch | `switch.inverter_export_surplus` |
| Current grid export limit | `number.inverter_export_surplus_power` |
| Maximum inverter/grid export limit | `number.solarny_menic_grid_max_export_power` |
| Night tariff used for value estimation | `input_number.cena_elektriny_nocny_tarif` |

If your entities have different names, edit them in [`Packages/negative_price_export_guard.yaml`](Packages/negative_price_export_guard.yaml). Do not use `input_text` indirection for trigger entity IDs; Home Assistant triggers need real entity IDs in YAML.

## How The Logic Works

1. At 07:00, the package records the daily house-load counter.
2. Every 15 minutes during 07:00-18:00, it stores the load-counter delta for the previous interval.
3. At 18:00, it stores the completed daily curve and keeps the last 7 daily curves in `past_load_curves`.
4. From those curves, it calculates the `load_curve` attribute: expected consumption and power for each 15-minute interval.
5. Every 10 minutes, and when important entities change, it recalculates remaining load, target SOC, expected surplus, and recommended export power.
6. If the current spot price is below the configured floor, the inverter is returned to `Zero Export To CT`.
7. If headroom is needed before a future negative-price window, the automation sets the export power and switches to `Export First`.
8. If the battery is full, surplus export is enabled, and strategic export is not wanted, the export limit is raised to reduce PV curtailment.

## Installation

1. Enable Home Assistant packages if you do not already use them.

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

2. Copy `Packages/negative_price_export_guard.yaml` into `config/packages/negative_price_export_guard.yaml`.
3. Check and adjust entity IDs for your own installation.
4. Run `Settings -> Developer Tools -> YAML -> Check configuration`.
5. If the configuration check passes, restart Home Assistant.
6. After restart, check the new entities starting with `export_optimizer_`.

For a more detailed setup walkthrough, see [Docs/Setup.md](Docs/Setup.md).

## Project Entities Card

To quickly find and adjust all entities created by this project, add this Lovelace card using [auto-entities](https://github.com/thomasloven/lovelace-auto-entities). The `custom:auto-entities` card must be installed in Home Assistant, for example through HACS.

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

The card filters entities by `export_optimizer` in the entity ID. It intentionally hides the technical morning-load value and its timestamp, because those are managed automatically.

## Important Controls

| Entity | Meaning |
|---|---|
| `input_boolean.export_optimizer_export_guard_enabled` | Main enable/disable toggle for the protection logic |
| `input_boolean.export_optimizer_allow_battery_early_export` | Allows strategic early export from the battery |
| `input_number.export_optimizer_min_reserve_soc` | Minimum battery reserve |
| `input_number.export_optimizer_consumption_margin_kwh` | Safety margin for the consumption estimate |
| `input_number.export_optimizer_typical_idle_power_w` | Minimum expected house load, including inverter self-consumption |
| `input_number.export_optimizer_export_surplus_threshold_kwh` | Minimum expected surplus before the automation intervenes |
| `input_number.export_optimizer_min_export_power_w` | Lower limit for controlled battery export |
| `input_number.export_optimizer_max_export_power_w` | Upper limit for controlled export and full-battery export limit |
| `input_number.export_optimizer_price_floor` | Price threshold at which export is still considered safe |

## What To Watch After Startup

| Entity | Meaning |
|---|---|
| `sensor.export_optimizer_okte_spotova_cena` | Current spot price calculated from OKTE attributes |
| `sensor.export_optimizer_negative_price_minutes_until_18` | Remaining minutes below the price floor until 18:00 |
| `sensor.export_optimizer_solar_window_load_7d_average` | Solar-window load average plus load-curve attributes |
| `sensor.export_optimizer_expected_load_power` | Expected house-load power for the current 15-minute interval |
| `sensor.export_optimizer_remaining_solar_window_load_estimate` | Remaining load estimate from the 15-minute curve |
| `sensor.export_optimizer_recommended_export_power` | Recommended strategic export power |
| `binary_sensor.export_optimizer_export_wanted` | Whether the automation wants `Export First` |
| `input_boolean.export_optimizer_export_guard_active` | Whether the automation is currently controlling export |
| `sensor.export_optimizer_expected_surplus_today` | Surplus after subtracting load and remaining battery capacity |
| `sensor.export_optimizer_battery_target_soc` | Battery SOC target based on estimated production and consumption |
| `sensor.export_optimizer_exported_energy_by_automation` | Energy exported by the automation |
| `sensor.export_optimizer_exported_energy_during_negative_spot_price` | Energy exported during negative spot prices |
| `sensor.export_optimizer_automation_export_savings` | Estimated rescued value |
| `sensor.export_optimizer_negative_price_wasted_potential` | Estimated lost value during negative prices |

## Load Curve

`sensor.export_optimizer_solar_window_load_7d_average` includes these useful attributes:

| Attribute | Meaning |
|---|---|
| `past_consumption` | Last 7 total daily solar-window load samples |
| `today_load_curve` | Today's already measured 15-minute intervals |
| `past_load_curves` | Last 7 completed daily 15-minute curves |
| `load_curve` | Average 15-minute curve used for remaining-load calculations |
| `current_interval_index` | Current 15-minute interval in the 07:00-18:00 window |

On the first day, the curve falls back to the daily average. It becomes more useful after each completed solar day, especially in homes with repeatable daytime load patterns.

## Troubleshooting

### The Spot Price Does Not Match The Current Time

Use `sensor.export_optimizer_okte_spotova_cena`, not the raw OKTE sensor state.

### PV Is Curtailed When The Battery Is Full

Check that these entities exist and have sensible values:

```text
switch.inverter_export_surplus
number.solarny_menic_grid_max_export_power
input_number.export_optimizer_max_export_power_w
```

### The Battery Discharges More Than Desired

Increase `input_number.export_optimizer_min_reserve_soc` or turn off `input_boolean.export_optimizer_allow_battery_early_export`.

### Home Assistant CPU Usage Is High

Do not convert trigger-based templates containing `now()`, `today_at()`, `prices`, or `detailedForecast` into triggerless template sensors. The load curve is intentionally calculated on a 15-minute trigger to avoid unnecessary recalculation.

## Screenshot Placeholders

### 1. Daily PV, Load, Battery, And Grid Flow Chart

<!-- TODO: Add a screenshot of a daily graph showing PV production, house load, grid flow, and battery charge/discharge during a day with negative prices. -->

### 2. OKTE Price Detail And Negative-Price Window

<!-- TODO: Add a screenshot of OKTE prices or a spot-price chart with the negative period clearly visible. -->

### 3. Automation Helper Sensors

<!-- TODO: Add a screenshot of a small dashboard containing export_optimizer_recommended_export_power, export_optimizer_export_wanted, export_optimizer_remaining_solar_window_load_estimate, export_optimizer_expected_load_power, and export_optimizer_negative_price_minutes_until_18. -->

### 4. House Load Curve

<!-- TODO: Add a screenshot of the load_curve attribute or a chart of expected 15-minute house load during the solar window. -->

### 5. Savings And Wasted Potential

<!-- TODO: Add a screenshot of cumulative estimated savings and wasted potential. -->

## Safety Notes

- Test with a low maximum export power first.
- Verify that your inverter really interprets `Export First` and `Zero Export To CT` as expected.
- Check whether changing `number.inverter_export_surplus_power` has side effects in other inverter modes.
- This project is not financial, legal, or electrical engineering advice.
- Use it at your own risk.
