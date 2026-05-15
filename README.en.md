# Home Assistant: export protection during negative spot prices

A Home Assistant project that helps solar PV owners avoid unnecessary grid export during negative spot-price periods. It was created for Slovak conditions, especially for virtual battery or credit-based services where electricity exported during negative prices may have no value.

Typical problem: on a sunny day the battery reaches 100%, the PV system has surplus production, but the OKTE spot price is negative. This project tries to create battery headroom before the negative-price window and, when the battery is already full, reduce unnecessary PV curtailment.

Slovak version: [README.md](README.md)

## Recommended Setup Method

The recommended method is the **custom integration** in [`custom_components/negative_price_export_guard`](custom_components/negative_price_export_guard). During onboarding, Home Assistant asks you to select the source entities from your own installation, validates important units, and creates tuning entities that can be adjusted from the UI.

The original **YAML package** [`Packages/negative_price_export_guard.yaml`](Packages/negative_price_export_guard.yaml) is still available. Use it if you do not want a custom integration or if you prefer to inspect and modify the full logic directly in YAML. With the YAML package, all entity IDs must be adjusted manually in the file.

## What It Does

- Calculates the current OKTE spot price from the `prices` attribute, not only from the sensor state.
- Looks for future price periods below the configured export floor until the end of the solar window.
- Learns house consumption during the solar window from the previous 7 days.
- Builds a 15-minute expected house-load curve.
- Uses the Solcast daily forecast, detailed forecast, and remaining-production-today sensor.
- Calculates expected surplus after accounting for remaining load and remaining battery capacity.
- Switches the inverter to `Export First` only when it needs to strategically create battery headroom.
- In battery-saving mode, caps export to live PV surplus.
- When the battery is full, it can raise the export limit to reduce unnecessary PV curtailment.
- Tracks energy exported during negative prices, energy exported by automation, estimated savings, and wasted potential.

## Requirements

The project expects these kinds of integrations:

- [OKTE DAM](https://github.com/rgildein/okte-home-assistant) or a similar spot-price source with a `prices` attribute.
- [Solcast Solar](https://github.com/BJReplay/ha-solcast-solar) with daily forecast, `detailedForecast`, and a remaining-production-today sensor.
- [ha-solarman](https://github.com/davidrapan/ha-solarman), Deye, or another inverter integration that can read battery state, PV power, house load, and control inverter mode and export limit.

The most important source entities are OKTE prices, Solcast forecast, daily house load, total grid export, battery SOC, PV power, house load power, inverter mode, and export-limit number. The full list is in [Docs/Setup.md](Docs/Setup.md).

## Quick Custom Integration Install

1. Copy `custom_components/negative_price_export_guard` to `config/custom_components/negative_price_export_guard`, or add this repository as a HACS custom repository if you install it that way.
2. Restart Home Assistant.
3. Open `Settings -> Devices & services -> Add integration`.
4. Search for `Negative Price Export Guard`.
5. Select the required source entities in the setup flow.
6. After setup, check the created entities starting with `export_optimizer_`.
7. Start with the guard disabled or with a low maximum export power, then observe behavior during the next negative-price window.

The detailed guide for both the custom integration and the YAML package is in [Docs/Setup.md](Docs/Setup.md).

## YAML Package

The YAML version remains part of the repository, but it is the manual path. After copying the package file, you must replace entity IDs for your installation and run the Home Assistant configuration check.

Use it mainly if you do not want the custom integration or if you want to customize the logic directly in YAML.

## Screenshots

Project entity overview:

![Export Optimizer entity overview](Docs/Screenshots/Export_optimizer_entities.png)

Expected house-load curve:

![Expected house-load curve](Docs/Screenshots/Krivka_spotreby.png)

Other useful real-performance screenshots would be a daily PV/battery/grid export chart or a savings and wasted-potential comparison.

## Main Custom Integration Controls

| Entity | Meaning |
|---|---|
| `switch.export_optimizer_guard_enabled` | Main enable/disable switch for export control |
| `switch.export_optimizer_allow_battery_early_export` | Allows strategic early export from the battery |
| `number.export_optimizer_min_reserve_soc` | Minimum battery reserve |
| `number.export_optimizer_consumption_margin_kwh` | Consumption estimate margin |
| `number.export_optimizer_typical_idle_power_w` | Minimum expected house load including inverter self-consumption |
| `number.export_optimizer_export_surplus_threshold_kwh` | Minimum expected surplus before intervention |
| `number.export_optimizer_min_export_power_w` | Lower export limit when battery export is allowed |
| `number.export_optimizer_max_export_power_w` | Upper controlled export limit |
| `number.export_optimizer_price_floor` | Price threshold below which export is considered unwanted |

## Safety Notes

- Test with a low maximum export power first.
- Verify that your inverter really interprets `Export First` and `Zero Export To CT` as expected.
- Check whether changing the export limit has side effects in other inverter modes.
- This project is not financial, legal, or electrical engineering advice.
- Use it at your own risk.
