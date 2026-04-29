# Detailed Setup Guide

This guide walks through installing and tuning the negative-price export guard package in Home Assistant.

The main README gives the short version. This file is intentionally more detailed and is meant for the first deployment or for adapting the package to a different inverter setup.

## 1. Confirm The Required Integrations

Before copying the package, make sure the required integrations are already working.

### OKTE Prices

Recommended integration:

- [OKTE DAM](https://github.com/rgildein/okte-home-assistant)

The package expects an OKTE price entity like:

```yaml
sensor.okte_ceny_elektriny_prices
```

This entity must expose a `prices` attribute containing 15-minute periods with timestamps and prices.

The package does not rely only on the OKTE sensor state, because that state may update later than the actual 15-minute price boundary. Instead, it calculates the current price from the `prices` attribute.

### Solcast PV Forecast

Recommended integration:

- [Solcast Solar](https://github.com/BJReplay/ha-solcast-solar)

The package expects a daily forecast entity like:

```yaml
sensor.solcast_pv_forecast_predpoved_dnes
```

The entity should expose a `detailedForecast` attribute. The package uses that detailed forecast to estimate how much PV production is expected before and during the next negative-price window.

### Inverter Integration

The package was developed around Deye/Solarman-style entities.

Recommended Solarman integration:

- [ha-solarman](https://github.com/davidrapan/ha-solarman)

At minimum, Home Assistant must be able to:

- read battery SOC,
- read current PV power,
- read current house load power,
- read daily PV production,
- read daily house load consumption,
- read total grid export,
- change the inverter work mode,
- set the grid export power limit.

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

The package expects this helper by default:

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

If you use a different helper entity, change `input_text.export_optimizer_entity_energy_value_helper` after installing the package.

## 4. Map Your Entity IDs

The package keeps all external entity IDs in one configuration section at the beginning of `negative_price_export_guard.yaml`.

Look for the `input_text:` block and adjust these values if your entities have different names:

| Mapping helper | Default value |
|---|---|
| `input_text.export_optimizer_entity_okte_prices` | `sensor.okte_ceny_elektriny_prices` |
| `input_text.export_optimizer_entity_solcast_forecast_today` | `sensor.solcast_pv_forecast_predpoved_dnes` |
| `input_text.export_optimizer_entity_today_load_consumption` | `sensor.inverter_today_load_consumption` |
| `input_text.export_optimizer_entity_total_energy_export` | `sensor.inverter_total_energy_export` |
| `input_text.export_optimizer_entity_today_production` | `sensor.inverter_today_production` |
| `input_text.export_optimizer_entity_battery_soc` | `sensor.inverter_battery` |
| `input_text.export_optimizer_entity_battery_capacity` | `sensor.inverter_battery_capacity` |
| `input_text.export_optimizer_entity_pv_power` | `sensor.inverter_pv_power` |
| `input_text.export_optimizer_entity_load_power` | `sensor.inverter_load_power` |
| `input_text.export_optimizer_entity_inverter_work_mode` | `select.inverter_work_mode` |
| `input_text.export_optimizer_entity_export_surplus_power` | `number.inverter_export_surplus_power` |
| `input_text.export_optimizer_entity_energy_value_helper` | `input_number.cena_elektriny_nocny_tarif` |
| `input_text.export_optimizer_mode_export_first` | `Export First` |
| `input_text.export_optimizer_mode_zero_export` | `Zero Export To CT` |

You can change these values directly in the YAML before the first install, or later from Home Assistant as text helpers. This is usually easier than searching through the whole package.

## 5. Check Units

This is important.

The package assumes:

| Mapping helper | Expected unit of the referenced entity |
|---|---|
| `input_text.export_optimizer_entity_pv_power` | W |
| `input_text.export_optimizer_entity_load_power` | W |
| `input_text.export_optimizer_entity_export_surplus_power` | W |
| `input_text.export_optimizer_entity_today_load_consumption` | kWh |
| `input_text.export_optimizer_entity_today_production` | kWh |
| `input_text.export_optimizer_entity_total_energy_export` | kWh |
| `input_text.export_optimizer_entity_battery_soc` | % |
| `input_text.export_optimizer_entity_battery_capacity` | kWh |

If your inverter exposes power in kW instead of W, you must adjust the calculations that use PV power, load power, and export power.

## 6. Confirm Inverter Mode Names

The package expects these options by default:

```text
Export First
Zero Export To CT
```

Check this in Home Assistant Developer Tools. If your inverter uses different option text, change:

```text
input_text.export_optimizer_mode_export_first
input_text.export_optimizer_mode_zero_export
```

## 7. Run A Configuration Check

In Home Assistant:

```text
Settings -> Developer Tools -> YAML -> Check configuration
```

Do not restart until this passes.

If the check fails, the most common causes are:

- entity IDs that do not exist,
- duplicated YAML keys from manual editing,
- indentation issues,
- inverter mode option names that do not match your integration.

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
```

## 9. First-Day Behavior

On the first day, the 7-day solar-window consumption average has no history yet. The package uses a fallback value until it collects real samples.

The daily learning logic records the house load at 07:00 and samples the 07:00-18:00 consumption window at 18:00.

Expect the estimate to improve after several days.

## 10. Recommended Initial Tuning

Start conservatively:

| Helper | Suggested value |
|---|---:|
| `input_number.export_optimizer_min_reserve_soc` | `40` |
| `input_number.export_optimizer_consumption_margin_kwh` | `2` |
| `input_number.export_optimizer_export_surplus_threshold_kwh` | `1` |
| `input_number.export_optimizer_min_export_power_w` | `500` |
| `input_number.export_optimizer_max_export_power_w` | `3000` |
| `input_number.export_optimizer_price_floor` | `0` |

Then observe at least a few sunny days with negative or near-zero price periods.

## 11. How To Tune

### If Energy Still Exports During Negative Prices

Increase one or more of:

```text
input_number.export_optimizer_max_export_power_w
input_number.export_optimizer_consumption_margin_kwh
input_number.export_optimizer_export_surplus_threshold_kwh
```

Also check whether your Solcast forecast is underestimating production.

### If The Battery Discharges Too Much

Increase:

```text
input_number.export_optimizer_min_reserve_soc
```

or disable:

```text
input_boolean.export_optimizer_allow_battery_early_export
```

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

## 12. Suggested Dashboard

A simple debug dashboard should include:

```text
sensor.export_optimizer_okte_spotova_cena
sensor.export_optimizer_negative_price_minutes_until_18
sensor.export_optimizer_recommended_export_power
binary_sensor.export_optimizer_export_wanted
input_boolean.export_optimizer_export_guard_enabled
input_boolean.export_optimizer_allow_battery_early_export
input_boolean.export_optimizer_export_guard_active
sensor.export_optimizer_expected_surplus_today
sensor.export_optimizer_battery_target_soc
input_text.export_optimizer_entity_okte_prices
input_text.export_optimizer_entity_inverter_work_mode
input_text.export_optimizer_entity_export_surplus_power
```

This makes it much easier to see why the automation is or is not active.

## 13. Accounting Sensors

The package creates cumulative sensors for tracking results:

| Entity | Meaning |
|---|---|
| `sensor.export_optimizer_exported_energy_during_negative_spot_price` | kWh exported during negative spot prices |
| `sensor.export_optimizer_exported_energy_by_automation` | kWh exported while the automation was actively controlling export |
| `sensor.export_optimizer_automation_export_savings` | Estimated value saved by automated export |
| `sensor.export_optimizer_negative_price_wasted_potential` | Estimated value lost due to export during negative prices |

These are cumulative sensors. For daily values, use graph/statistics cards that calculate a daily difference.

## 14. Performance Notes

The package uses trigger-based template sensors on purpose.

Avoid turning these templates into regular triggerless template sensors if they contain:

```text
now()
today_at()
state_attr(... prices ...)
state_attr(... detailedForecast ...)
```

Those functions and loops can cause frequent template recalculation and high CPU usage on smaller Home Assistant systems.

## 15. Safety Checklist

Before leaving the automation enabled unattended:

- Confirm the inverter mode changes are correct.
- Confirm export power limits are reasonable for your inverter and grid connection.
- Confirm negative spot-price periods force the inverter back to `Zero Export To CT`.
- Confirm `sensor.export_optimizer_okte_spotova_cena` matches the real current OKTE period.
- Confirm the battery reserve is high enough for your household.
- Start with a low max export power and increase gradually.

## 16. Adapting To Other Countries Or Providers

The idea is not Slovakia-specific, but the price source and supplier rules are.

To adapt it elsewhere, update:

- the mapped spot-price entity,
- the price attribute parsing if needed,
- the buyout/virtual-battery value helper,
- the inverter mode names,
- the solar window end time if local PV production differs.

The core concept remains the same: create battery headroom before negative-price windows, avoid strategic export during negative prices, and track whether the tuning is working.
