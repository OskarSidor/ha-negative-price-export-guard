# Home Assistant: export protection during negative spot prices

A Home Assistant project that helps battery-backed solar PV owners maximize export during positive market prices and reduce unnecessary grid export during negative spot-price periods. It was created after changes to Magna Energia's Požičovňa elektriny rules in Slovakia, where electricity exported during negative prices is not counted into Požičovňa.

Typical problem: the battery becomes full in the morning or during a sunny day, the PV system has surplus production, but the OKTE spot price is negative. This project tries to create battery headroom before the negative-price window and, when the battery is already full, reduce unnecessary PV curtailment.

The project was created primarily for Deye inverters, but with adjustments it may later work with other inverter brands as well.

Slovak version: [README.md](README.md)

## Recommended Setup Method

The recommended method is the **custom integration** in [`custom_components/negative_price_export_guard`](custom_components/negative_price_export_guard). During onboarding, Home Assistant asks you to select the source entities from your own installation, validates important units, and creates tuning entities that can be adjusted from the UI.

The original **YAML package** [`Packages/negative_price_export_guard.yaml`](Packages/negative_price_export_guard.yaml) is still available. Use it if you do not want a custom integration or if you prefer to inspect and modify the full logic directly in YAML. With the YAML package, all entity IDs must be adjusted manually in the file.

## What It Does

- Calculates the current OKTE spot price from the `prices` attribute, not only from the sensor state.
- Looks for future price periods below the configured export floor until the end of the solar window.
- Learns house consumption during the solar window from the previous 7 days.
- Builds an expected house-load curve from historical consumption in 15-minute intervals.
- Uses the Solcast daily forecast, detailed forecast, and remaining-production-today sensor.
- Calculates expected surplus after accounting for remaining load and remaining battery capacity.
- Switches the inverter to `Export First` mode only when it needs to strategically create battery headroom.
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

The recommended path is HACS:

1. In HACS, open `Integrations -> three dots -> Custom repositories`.
2. Enter `OskarSidor/ha-negative-price-export-guard` or `https://github.com/OskarSidor/ha-negative-price-export-guard` in the `Repository` field.
3. Select `Integration` as the category and add the repository.
4. Install `Negative Price Export Guard` from HACS.
5. Restart Home Assistant.
6. Open `Settings -> Devices & services -> Add integration`.
7. Search for `Negative Price Export Guard`.
8. Select the required source entities in the setup flow.
9. After setup, check the created entities starting with `negative_price_export_guard_`.
10. Start with the guard disabled or with a low maximum export power, then observe behavior during the next negative-price window.

Without HACS, copy `custom_components/negative_price_export_guard` to `config/custom_components/negative_price_export_guard`, then restart Home Assistant.

The detailed guide for both the custom integration and the YAML package is in [Docs/Setup.md](Docs/Setup.md).

## YAML Version Of The Project

The YAML version remains part of the repository, but it is the manual way to use this project. After copying the package file, you must replace entity IDs for your installation and run the Home Assistant configuration check.

Use it mainly if you do not want the custom integration or if you want to customize the logic directly in YAML.

## Screenshots

Expected house-load curve:

![Expected house-load curve](Docs/Screenshots/Krivka_spotreby.png)

Other useful real-performance screenshots would be a daily PV/battery/grid export chart or a savings and wasted-potential comparison.

## Main Custom Integration Controls

| Entity | Meaning |
|---|---|
| `switch.negative_price_export_guard_ochrana_exportu_zapnuta` | Main enable/disable switch for export control |
| `switch.negative_price_export_guard_povolit_skory_export_z_baterie` | Allows strategic early export from the battery |
| `number.negative_price_export_guard_minimalna_rezerva_baterie` | Minimum battery reserve |
| `number.negative_price_export_guard_rezerva_odhadu_spotreby` | Consumption estimate margin |
| `number.negative_price_export_guard_typicka_minimalna_spotreba_domu` | Minimum expected house load including inverter self-consumption |
| `number.negative_price_export_guard_minimalny_ocakavany_prebytok` | Minimum expected surplus before intervention |
| `number.negative_price_export_guard_minimalny_riadeny_vykon_exportu` | Lower export limit when battery export is allowed |
| `number.negative_price_export_guard_maximalny_riadeny_vykon_exportu` | Upper controlled export limit |
| `number.negative_price_export_guard_minimalna_spotova_cena_pre_export` | Price threshold below which export is considered unwanted |

## Safety Notes

- Test with a low maximum export power first.
- Verify that your inverter really interprets `Export First` and `Zero Export To CT` as expected.
- Check whether changing the export limit has side effects in other inverter modes.
- This project is not financial, legal, or electrical engineering advice.
- Use it at your own risk.
