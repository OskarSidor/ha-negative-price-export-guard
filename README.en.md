# Home Assistant: export protection during negative spot prices

A Home Assistant automation package that helps solar PV owners avoid exporting electricity to the grid during negative spot-price periods. The project was created for Slovak conditions, especially for cases where a supplier does not count electricity exported during negative prices into a virtual battery or similar credit-based service.

Typical example: on a sunny day the battery reaches 100%, the PV system has surplus production, but the OKTE spot price is negative. If electricity is exported to the grid at that moment, it may have zero value for the virtual battery. This package tries to create battery headroom before the negative-price window, so more solar energy can be stored locally during negative prices instead of being sent to the grid.

Slovak version: [README.md](README.md)

## What It Does

- Calculates the current OKTE spot price from the `prices` attribute, not only from the sensor state.
- Looks for future price periods below the configured export floor until 18:00.
- Learns house consumption during the solar window, 07:00-18:00, from previous days.
- Uses the daily Solcast PV forecast, including the `detailedForecast` attribute.
- Adds a minimum expected base load from `input_number.export_optimizer_typical_idle_power_w`.
- Calculates a recommended export power before a negative or otherwise unwanted price window.
- Switches the inverter to `Export First` only when it needs to strategically create battery headroom.
- Returns the inverter to `Zero Export To CT` when controlled export is no longer needed.
- Includes a toggle to disable early battery export and use only current PV surplus instead.
- Raises the export limit when the battery is full in `Zero Export To CT`, so the inverter does not unnecessarily curtail PV production during non-negative prices.
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

## How The Logic Works

The automation separates normal PV surplus export from strategic battery/headroom export.

Normally, the inverter stays in `Zero Export To CT`. If your inverter still exports real PV surplus in this mode, the automation leaves it there. It switches to `Export First` only when it needs to create battery headroom before a future negative-price window.

In simplified terms:

1. It checks whether another period below the configured price floor is expected before 18:00.
2. It estimates how much PV energy will arrive before and during that period.
3. It estimates the remaining house consumption in the solar window, including a minimum base-load estimate.
4. It checks the current battery SOC and target reserve.
5. It calculates how much energy should be exported early so the battery can absorb PV during negative prices.
6. It sets the grid export limit through `number.inverter_export_surplus_power`.
7. It switches the inverter to `Export First` only during required strategic export.
8. During negative prices, or after strategic export is no longer needed, it returns the inverter to `Zero Export To CT`.

## Requirements

### Integrations

- **[OKTE DAM](https://github.com/rgildein/okte-home-assistant)** or a similar integration with spot prices and a `prices` attribute.
- **[Solcast](https://github.com/BJReplay/ha-solcast-solar)** with a daily forecast and `detailedForecast` attribute.
- **[Solarman](https://github.com/davidrapan/ha-solarman) / Deye** or another inverter integration that can read battery state and change export behavior.

### Expected Entities

By default, the package expects these entities:

| Purpose | Default entity |
|---|---|
| OKTE prices with `prices` attribute | `sensor.okte_ceny_elektriny_prices` |
| Solcast forecast for today | `sensor.solcast_pv_forecast_predpoved_dnes` |
| Daily house load consumption in kWh | `sensor.inverter_today_load_consumption` |
| Total grid export in kWh | `sensor.inverter_total_energy_export` |
| Daily PV production in kWh | `sensor.inverter_today_production` |
| Battery SOC in % | `sensor.inverter_battery` |
| Battery capacity in kWh | `sensor.inverter_battery_capacity` |
| Current PV power in W | `sensor.inverter_pv_power` |
| Current house load power in W | `sensor.inverter_load_power` |
| Inverter work mode | `select.inverter_work_mode` |
| Grid export limit | `number.inverter_export_surplus_power` |
| Night tariff used for value estimation | `input_number.cena_elektriny_nocny_tarif` |

If your entities have different names, edit them in [`Packages/negative_price_export_guard.yaml`](Packages/negative_price_export_guard.yaml).

## Installation

1. Enable Home Assistant packages if you do not already use them.

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

2. Create the `packages` folder in your Home Assistant configuration directory.

3. Copy `Packages/negative_price_export_guard.yaml` into `config/packages/negative_price_export_guard.yaml`.

4. Check and adjust entity IDs for your own installation.

5. In Home Assistant, go to `Settings -> Developer Tools -> YAML -> Check configuration`.

6. If the configuration check passes, restart Home Assistant.

7. After restart, check the new entities starting with `export_optimizer_`.

For a more detailed setup walkthrough, see [Docs/Setup.md](Docs/Setup.md).

## Important Controls

| Entity | Meaning |
|---|---|
| `input_boolean.export_optimizer_export_guard_enabled` | Main enable/disable toggle for the protection logic |
| `input_boolean.export_optimizer_allow_battery_early_export` | Allows strategic early export from the battery |
| `input_number.export_optimizer_min_reserve_soc` | Minimum battery reserve you do not want to discharge below |
| `input_number.export_optimizer_consumption_margin_kwh` | Safety margin for the consumption estimate |
| `input_number.export_optimizer_typical_idle_power_w` | Minimum expected house load, including inverter self-consumption, for the rest of the solar window |
| `input_number.export_optimizer_export_surplus_threshold_kwh` | Minimum expected surplus before the automation intervenes |
| `input_number.export_optimizer_min_export_power_w` | Lower limit for controlled export |
| `input_number.export_optimizer_max_export_power_w` | Upper limit for controlled export and full-battery export limit |
| `input_number.export_optimizer_price_floor` | Price threshold at which export is still considered safe |

## Recommended Starting Values

| Setting | Recommended value |
|---|---:|
| Minimum battery reserve | `40 %` |
| Consumption estimate margin | `2 kWh` |
| Typical minimum house load | `200-500 W`, depending on the house and inverter |
| Minimum expected surplus | `1 kWh` |
| Minimum controlled export | `500 W` |
| Maximum controlled export | `3000 W` |
| Minimum spot price for export | `0 EUR/MWh` |

After a few sunny days, inspect the behavior and tune the values.

## Battery-Saving Mode

If you turn off `Export Optimizer - allow early battery export`, the automation tries to avoid discharging the battery and limits export roughly to the current live PV surplus:

```text
PV power - house load power - 200 W
```

This mode can be useful if you want to reduce battery cycling. It may be less effective before long or strong negative-price periods.

## What To Watch After Startup

| Entity | Meaning |
|---|---|
| `sensor.export_optimizer_okte_spotova_cena` | Current spot price calculated from OKTE attributes |
| `sensor.export_optimizer_negative_price_minutes_until_18` | Remaining minutes below the price floor until 18:00 |
| `sensor.export_optimizer_recommended_export_power` | Recommended strategic export power |
| `binary_sensor.export_optimizer_export_wanted` | Whether the automation wants `Export First` |
| `input_boolean.export_optimizer_export_guard_active` | Whether the automation is currently controlling export |
| `sensor.export_optimizer_remaining_solar_window_load_estimate` | Remaining load estimate including the minimum base load |
| `sensor.export_optimizer_expected_surplus_today` | Estimated surplus energy until the end of the solar window |
| `sensor.export_optimizer_battery_target_soc` | Battery SOC target based on estimated production and consumption |
| `sensor.export_optimizer_exported_energy_by_automation` | Energy exported by the automation |
| `sensor.export_optimizer_exported_energy_during_negative_spot_price` | Energy exported during negative spot prices |
| `sensor.export_optimizer_automation_export_savings` | Estimated rescued value |
| `sensor.export_optimizer_negative_price_wasted_potential` | Estimated lost value during negative prices |

## Screenshot Placeholders

### 1. Daily PV, Load, Battery, And Grid Flow Chart

<!-- TODO: Add a screenshot of a daily graph showing PV production, house load, grid flow, and battery charge/discharge during a day with negative prices. -->

This image should show that energy was exported before the negative-price window, while more production was stored in the battery during negative prices.

### 2. OKTE Price Detail And Negative-Price Window

<!-- TODO: Add a screenshot of OKTE prices or a spot-price chart with the negative period clearly visible. -->

This image should explain why the automation started exporting before the negative period.

### 3. Automation Helper Sensors

<!-- TODO: Add a screenshot of a small dashboard containing export_optimizer_recommended_export_power, export_optimizer_export_wanted, export_optimizer_remaining_solar_window_load_estimate, and export_optimizer_negative_price_minutes_until_18. -->

This image should show the automation's decision-making state while preparing for negative prices.

### 4. Savings And Wasted Potential

<!-- TODO: Add a screenshot of cumulative estimated savings and wasted potential. -->

This image can show whether the automation is tuned well. Ideally, estimated savings should grow over time while wasted potential stays low.

## Troubleshooting

### The Spot Price Does Not Match The Current Time

Use `sensor.export_optimizer_okte_spotova_cena`, not the raw OKTE sensor state. This derived sensor calculates the current price from the `prices` attribute and handles time zones.

### Home Assistant CPU Usage Is High

Check that you did not move templates containing `now()` into regular triggerless template sensors. This package intentionally uses trigger-based template sensors to avoid excessive recalculation.

### The Inverter Does Not Switch Mode

Check that the options in `select.inverter_work_mode` exactly match `Export First` and `Zero Export To CT`. If your inverter exposes different option names, edit the automation.

### Power Values Look Wrong

The package assumes `sensor.inverter_pv_power`, `sensor.inverter_load_power`, and `number.inverter_export_surplus_power` are in watts. If your inverter uses kW, adjust the calculations.

### The Battery Discharges More Than Desired

Increase `input_number.export_optimizer_min_reserve_soc` or turn off `input_boolean.export_optimizer_allow_battery_early_export`.

## Safety Notes

- Test with a low maximum export power first.
- Verify that your inverter really interprets `Export First` and `Zero Export To CT` as expected.
- Check whether changing `number.inverter_export_surplus_power` has side effects in other inverter modes.
- This project is not financial, legal, or electrical engineering advice.
- Use it at your own risk.

## Project Status

This is currently a practical Home Assistant package, not a HACS integration. It is meant to be copied, adapted, and tuned for each installation.

Suggestions, fixes, and real-world feedback are welcome.
