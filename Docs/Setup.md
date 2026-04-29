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

The package expects a daily forecast entity like:

```yaml
sensor.solcast_pv_forecast_predpoved_dnes
```

The entity should expose a `detailedForecast` attribute. The package uses that detailed forecast to estimate PV production before and during the next price window below your configured floor.

### Inverter Integration

The package was developed around Deye/Solarman-style entities.

Recommended Solarman integration:

- [ha-solarman](https://github.com/davidrapan/ha-solarman)

At minimum, Home Assistant must be able to read battery SOC, PV power, house load power, daily PV production, daily house load consumption, total grid export, and it must be able to change inverter work mode and set the grid export power limit.

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
| Solcast forecast today | `sensor.solcast_pv_forecast_predpoved_dnes` |
| Daily house load consumption | `sensor.inverter_today_load_consumption` |
| Total grid export | `sensor.inverter_total_energy_export` |
| Daily PV production | `sensor.inverter_today_production` |
| Battery SOC | `sensor.inverter_battery` |
| Battery capacity | `sensor.inverter_battery_capacity` |
| Current PV power | `sensor.inverter_pv_power` |
| Current load power | `sensor.inverter_load_power` |
| Inverter mode select | `select.inverter_work_mode` |
| Export power limit | `number.inverter_export_surplus_power` |
| Energy value helper | `input_number.cena_elektriny_nocny_tarif` |

If your entities use different names, replace all occurrences in the package. Do not try to put entity IDs into `input_text` helpers for triggers; Home Assistant triggers need real entity IDs in the YAML.

## 5. Check Units

The package assumes:

| Entity | Expected unit |
|---|---|
| `sensor.inverter_pv_power` | W |
| `sensor.inverter_load_power` | W |
| `number.inverter_export_surplus_power` | W |
| `sensor.inverter_today_load_consumption` | kWh |
| `sensor.inverter_today_production` | kWh |
| `sensor.inverter_total_energy_export` | kWh |
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

## 8. Restart And Verify New Entities

After restart, search for entities starting with:

```text
export_optimizer_
```

The most important ones are:

```text
sensor.export_optimizer_okte_spotova_cena
sensor.export_optimizer_recommended_export_power
binary_sensor.export_optimizer_export_wanted
input_boolean.export_optimizer_export_guard_enabled
input_boolean.export_optimizer_allow_battery_early_export
input_boolean.export_optimizer_export_guard_active
input_number.export_optimizer_typical_idle_power_w
```

## 9. First-Day Behavior And Learning

The package records the house load counter at 07:00 and evaluates the 07:00-18:00 consumption window at 18:00. The sensor `sensor.export_optimizer_solar_window_load_7d_average` stores the last seven daily samples in the `past_consumption` attribute and uses them for the average.

On the first day, the average has little or no history. Expect the estimate to improve after several sunny days.

## 10. Recommended Initial Tuning

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

## 11. Battery-Saving Mode

If you turn off:

```text
input_boolean.export_optimizer_allow_battery_early_export
```

then the recommended export power is capped to the current live PV surplus:

```text
PV power - house load power - 200 W
```

This reduces battery cycling, but it may not create enough headroom before a long or strong negative-price period.

## 12. How To Tune

### If Energy Still Exports During Negative Prices

Try these in order:

- Increase `input_number.export_optimizer_max_export_power_w` if the inverter is allowed to export more.
- Increase `input_number.export_optimizer_export_surplus_threshold_kwh` if you want the algorithm to create more buffer before the negative window.
- Enable `input_boolean.export_optimizer_allow_battery_early_export` if battery-saving mode is too restrictive.
- Check whether Solcast is underestimating production or whether your battery capacity/SOC entities are inaccurate.

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

### If The Remaining Load Estimate Falls Too Low

Increase:

```text
input_number.export_optimizer_typical_idle_power_w
```

This is useful when the learned daily consumption is mostly already used, but the house still has a predictable base load until 18:00.

### If The Automation Starts Too Often

Increase:

```text
input_number.export_optimizer_export_surplus_threshold_kwh
```

This makes the automation ignore smaller expected surpluses.

### If PV Is Curtailed When The Battery Is Full

Increase:

```text
input_number.export_optimizer_max_export_power_w
```

The automation includes logic to set the export limit to the maximum value when the battery is full and the inverter is in `Zero Export To CT`, as long as the spot price is non-negative.

## 13. Suggested Dashboard

A simple debug dashboard should include:

```text
sensor.export_optimizer_okte_spotova_cena
sensor.export_optimizer_negative_price_minutes_until_18
sensor.export_optimizer_recommended_export_power
binary_sensor.export_optimizer_export_wanted
input_boolean.export_optimizer_export_guard_enabled
input_boolean.export_optimizer_allow_battery_early_export
input_boolean.export_optimizer_export_guard_active
sensor.export_optimizer_remaining_solar_window_load_estimate
sensor.export_optimizer_expected_surplus_today
sensor.export_optimizer_battery_target_soc
input_number.export_optimizer_typical_idle_power_w
number.inverter_export_surplus_power
select.inverter_work_mode
sensor.inverter_battery
sensor.inverter_pv_power
sensor.inverter_load_power
```

This makes it much easier to see why the automation is or is not active.

## 14. Accounting Sensors

The package creates cumulative sensors for tracking results:

| Entity | Meaning |
|---|---|
| `sensor.export_optimizer_exported_energy_during_negative_spot_price` | kWh exported during negative spot prices |
| `sensor.export_optimizer_exported_energy_by_automation` | kWh exported while the automation was actively controlling export |
| `sensor.export_optimizer_automation_export_savings` | Estimated value saved by automated export |
| `sensor.export_optimizer_negative_price_wasted_potential` | Estimated value lost due to export during negative prices |

These are cumulative sensors. For daily values, use graph/statistics cards that calculate a daily difference.

## 15. Performance Notes

The package uses trigger-based template sensors on purpose. Avoid turning templates containing these into regular triggerless template sensors:

```text
now()
today_at()
state_attr(... prices ...)
state_attr(... detailedForecast ...)
```

Those functions and loops can cause frequent template recalculation and high CPU usage on smaller Home Assistant systems.

## 16. Safety Checklist

Before leaving the automation enabled unattended:

- Confirm the inverter mode changes are correct.
- Confirm export power limits are reasonable for your inverter and grid connection.
- Confirm negative spot-price periods force the inverter back to `Zero Export To CT`.
- Confirm `sensor.export_optimizer_okte_spotova_cena` matches the real current OKTE period.
- Confirm the battery reserve is high enough for your household.
- Start with a low max export power and increase gradually.

## 17. Adapting To Other Countries Or Providers

The idea is not Slovakia-specific, but the price source and supplier rules are. To adapt it elsewhere, replace the OKTE price entity, price parsing if needed, the value calculation, inverter mode names, and the solar window if local PV production differs.

The core concept remains the same: create battery headroom before negative-price windows, avoid strategic export during negative prices, and track whether the tuning is working.
