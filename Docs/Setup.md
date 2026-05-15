# Detailed Setup Guide

This guide covers both supported ways to use Negative Price Export Guard in Home Assistant.

The recommended path is the **custom integration**. It asks for the required entities during onboarding, validates important units, creates UI-adjustable tuning entities, and keeps the logic in Python.

The alternative path is the **YAML package**. It remains available for advanced users who prefer a fully visible YAML implementation, but it requires manual entity replacement and more careful maintenance.

## 1. Choose Your Setup Method

| Method | Recommended for | Main tradeoff |
|---|---|---|
| Custom integration | Most users | Easier setup, UI controls, entity validation |
| YAML package | Advanced/manual users | Fully visible YAML, but all entity IDs must be edited by hand |

Do not install both methods at the same time unless you deliberately disable one of them. Both can control the same inverter entities, so running both would be confusing and potentially unsafe.

## 2. Required Integrations

### OKTE Prices

Recommended integration:

- [OKTE DAM](https://github.com/rgildein/okte-home-assistant)

Required behavior:

- one sensor with current or upcoming OKTE prices,
- a `prices` attribute containing 15-minute periods,
- prices in `EUR/MWh`.

The default entity used by the project is:

```text
sensor.okte_ceny_elektriny_prices
```

The optimizer calculates the current price from the `prices` attribute because the raw sensor state may update later than the real 15-minute price boundary.

### Solcast PV Forecast

Recommended integration:

- [Solcast Solar](https://github.com/BJReplay/ha-solcast-solar)

Required entities:

```text
sensor.solcast_pv_forecast_predpoved_dnes
sensor.solcast_pv_forecast_predpoved_zostavajuca_dnes
```

The first entity must expose `detailedForecast`. The second entity should represent remaining forecasted production for today in `kWh`.

### Inverter Integration

The project was developed around Deye/Solarman-style entities.

Recommended Solarman integration:

- [ha-solarman](https://github.com/davidrapan/ha-solarman)

Home Assistant must be able to read battery SOC, PV power, house load power, daily production, daily load consumption, total grid export, current export settings, inverter work mode, and export power limits.

## 3. Required Source Entities

| Purpose | Default entity | Expected unit/domain |
|---|---|---|
| OKTE prices with `prices` attribute | `sensor.okte_ceny_elektriny_prices` | `EUR/MWh` |
| Solcast forecast today with `detailedForecast` | `sensor.solcast_pv_forecast_predpoved_dnes` | `kWh` |
| Solcast remaining production today | `sensor.solcast_pv_forecast_predpoved_zostavajuca_dnes` | `kWh` |
| Daily house load consumption | `sensor.inverter_today_load_consumption` | `kWh` |
| Total grid export | `sensor.inverter_total_energy_export` | `kWh` |
| Daily PV production | `sensor.inverter_today_production` | `kWh` |
| Battery SOC | `sensor.inverter_battery` | `%` |
| Battery capacity | `sensor.inverter_battery_capacity` | `kWh` |
| Current PV power | `sensor.inverter_pv_power` | `W` |
| Current house load power | `sensor.inverter_load_power` | `W` |
| Inverter work mode | `select.inverter_work_mode` | `select` |
| PV surplus export switch | `switch.inverter_export_surplus` | `switch` |
| Current grid export limit | `number.inverter_export_surplus_power` | `W` |
| Maximum inverter/grid export limit | `number.solarny_menic_grid_max_export_power` | `W` |
| Optional night tariff for value estimation | `input_number.cena_elektriny_nocny_tarif` | `EUR/kWh` |

If the optional night-tariff helper is not configured in the custom integration, the integration falls back to `0.054 EUR/kWh`.

## 4. Custom Integration Setup Recommended

### Install

Recommended HACS installation:

1. In HACS, open `Integrations`.
2. Open the three-dot menu and choose `Custom repositories`.
3. Enter `OskarSidor/ha-negative-price-export-guard` or `https://github.com/OskarSidor/ha-negative-price-export-guard` in the `Repository` field.
4. Select `Integration` as the category and add the repository.
5. Find and install `Negative Price Export Guard` in HACS.
6. Restart Home Assistant.

Manual alternative without HACS:

1. Copy `custom_components/negative_price_export_guard` into:

   ```text
   config/custom_components/negative_price_export_guard
   ```

2. Restart Home Assistant.

### Add The Integration

In Home Assistant:

```text
Settings -> Devices & services -> Add integration -> Negative Price Export Guard
```

During onboarding, select your source entities. The form includes default entity IDs and filters many dropdowns by expected domain or device class, so the correct entities should be easier to find.

The setup flow validates:

- required entities exist,
- OKTE sensor has a `prices` attribute,
- Solcast forecast has a `detailedForecast` attribute,
- energy sensors use `kWh`,
- power sensors and export-power numbers use `W`,
- battery SOC uses `%`.

### Created Entities

The integration creates entities with `export_optimizer_` object IDs. Important examples:

| Entity | Meaning |
|---|---|
| `switch.export_optimizer_guard_enabled` | Main enable/disable switch for active inverter control |
| `switch.export_optimizer_allow_battery_early_export` | Allows strategic early export from battery |
| `binary_sensor.export_optimizer_export_wanted` | Whether the integration wants `Export First` |
| `binary_sensor.export_optimizer_export_active` | Whether the integration is actively controlling export |
| `number.export_optimizer_min_reserve_soc` | Minimum battery reserve |
| `number.export_optimizer_consumption_margin_kwh` | Remaining-load safety margin |
| `number.export_optimizer_typical_idle_power_w` | Minimum expected house load including inverter self-consumption |
| `number.export_optimizer_export_surplus_threshold_kwh` | Minimum expected surplus before intervention |
| `number.export_optimizer_min_export_power_w` | Minimum export power when battery export is allowed |
| `number.export_optimizer_max_export_power_w` | Maximum controlled export power |
| `number.export_optimizer_price_floor` | Price floor below which export is considered unwanted |
| `time.export_optimizer_solar_window_start` | Start of the daytime learning/control window |
| `time.export_optimizer_solar_window_end` | End of the daytime learning/control window |
| `sensor.export_optimizer_recommended_export_power` | Recommended strategic export power |
| `sensor.export_optimizer_expected_load_power` | Current expected house load from the load curve |
| `sensor.export_optimizer_solar_window_load_7d_average` | 7-day average plus load-curve attributes |

![Example entity overview](Screenshots/Export_optimizer_entities.png)

### Recommended First Values

Start conservatively:

| Entity | Suggested value |
|---|---:|
| `number.export_optimizer_min_reserve_soc` | `30-40` |
| `number.export_optimizer_consumption_margin_kwh` | `1-2` |
| `number.export_optimizer_typical_idle_power_w` | your normal base load, for example `200-700 W` |
| `number.export_optimizer_export_surplus_threshold_kwh` | `1` |
| `number.export_optimizer_min_export_power_w` | `500 W` |
| `number.export_optimizer_max_export_power_w` | start low, then increase gradually |
| `number.export_optimizer_price_floor` | `0 EUR/MWh` |

Keep `switch.export_optimizer_guard_enabled` off until you have checked the calculated sensors. Then enable it for a real test window.

## 5. YAML Package Setup Manual

Use this path only if you want the YAML implementation.

### Enable Packages

In `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Create this folder if needed:

```text
config/packages
```

Copy:

```text
Packages/negative_price_export_guard.yaml
```

into:

```text
config/packages/negative_price_export_guard.yaml
```

### Edit Entity IDs

Open the YAML file and replace every default source entity with your own entity IDs. Do not use `input_text` indirection for trigger entity IDs. Home Assistant triggers need real entity IDs in YAML.

The YAML package creates `input_number`, `input_boolean`, `input_datetime`, template sensors, binary sensors, and automations. This differs from the custom integration, which creates `number`, `switch`, `time`, `sensor`, and `binary_sensor` entities.

### Run A Config Check

Before restart:

```text
Settings -> Developer Tools -> YAML -> Check configuration
```

Do not restart until the check passes.

### YAML-Specific Controls

| YAML entity | Meaning |
|---|---|
| `input_boolean.export_optimizer_export_guard_enabled` | Main enable/disable helper |
| `input_boolean.export_optimizer_allow_battery_early_export` | Allows strategic early battery export |
| `input_number.export_optimizer_min_reserve_soc` | Minimum battery reserve |
| `input_number.export_optimizer_consumption_margin_kwh` | Remaining-load margin |
| `input_number.export_optimizer_typical_idle_power_w` | Minimum expected house load |
| `input_number.export_optimizer_max_export_power_w` | Maximum controlled export power |
| `input_number.export_optimizer_price_floor` | Export price floor |

## 6. How The Logic Works

1. The system records the house-load counter at the start of the solar window.
2. Every 15 minutes during the solar window, it stores the previous interval's load delta.
3. At the end of the solar window, it archives the completed daily curve.
4. It keeps up to 7 days of load curves and creates an average 15-minute `load_curve`.
5. It estimates remaining load from the curve, plus the configured safety margin and minimum idle power.
6. It combines remaining load, Solcast remaining production, battery SOC, and battery capacity to estimate true surplus.
7. If a future negative-price block is expected, it calculates how much export is needed before that block.
8. If battery export is disabled or SOC is at/below target, recommended export is capped to live PV surplus and does not force the minimum export power.
9. If the current price is below the floor, the inverter is kept in `Zero Export To CT`.
10. If battery SOC is full, the export limit can be raised to reduce PV curtailment.

## 7. Load Curve

`sensor.export_optimizer_solar_window_load_7d_average` contains these attributes:

| Attribute | Meaning |
|---|---|
| `past_consumption` | Last 7 total solar-window consumption samples |
| `today_load_curve` | Today's measured 15-minute intervals so far |
| `past_load_curves` | Last 7 completed daily 15-minute curves |
| `load_curve` | Average 15-minute curve used by the optimizer |
| `last_interval_total_kwh` | Internal counter snapshot |
| `current_interval_index` | Current 15-minute interval in the solar window |

Example curve item:

```yaml
index: 0
start: "07:00:00"
end: "07:15:00"
consumption_kwh: 0.12
power_w: 480
samples: 4
```

![Expected house load curve](Screenshots/Krivka_spotreby.png)

## 8. Dashboard Cards

### Entity Overview With Auto Entities

Install [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) first.

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
```

For the YAML package, you may hide technical helpers that users normally do not edit:

```yaml
filter:
  exclude:
    - entity_id: input_number.export_optimizer_solar_window_start_load_kwh
    - entity_id: input_datetime.export_optimizer_solar_window_start_recorded
```

### Load Curve With ApexCharts

Install [apexcharts-card](https://github.com/RomRider/apexcharts-card) first.

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Krivka očakávanej spotreby domu počas dňa
  show_states: false
graph_span: 11h
span:
  start: day
  offset: +7h
now:
  show: true
  label: Teraz
apex_config:
  chart:
    height: 300
  legend:
    show: true
  stroke:
    curve: smooth
  yaxis:
    title:
      text: W
series:
  - entity: sensor.export_optimizer_solar_window_load_7d_average
    name: Očakávaná spotreba
    type: line
    color: "#f59e0b"
    stroke_width: 4
    show:
      legend_value: false
    data_generator: |
      const curve = entity.attributes.load_curve || [];
      const now = new Date();
      return curve.map((item) => {
        const [h, m, s] = (item.start || "00:00:00").split(":").map(Number);
        const date = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, s || 0);
        return [date.getTime(), Number(item.power_w || 0)];
      });
  - entity: sensor.export_optimizer_solar_window_load_7d_average
    name: Dnes namerané
    type: line
    stroke_width: 2
    opacity: 0.9
    show:
      legend_value: false
    data_generator: |
      const intervals = entity.attributes.today_load_curve?.intervals || [];
      const now = new Date();
      return intervals.map((item) => {
        const [h, m, s] = (item.start || "00:00:00").split(":").map(Number);
        const date = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, s || 0);
        return [date.getTime(), Number(item.consumption_kwh || 0) * 4000];
      });
```

You can add past-day series from `past_load_curves` in the same way if you want to compare history.

## 9. Accounting Sensors

The project exposes cumulative result sensors:

| Entity | Meaning |
|---|---|
| `sensor.export_optimizer_exported_energy_during_negative_spot_price` | kWh exported during negative spot prices |
| `sensor.export_optimizer_exported_energy_by_automation` | kWh exported while active control was on |
| `sensor.export_optimizer_automation_export_savings` | Estimated saved value |
| `sensor.export_optimizer_negative_price_wasted_potential` | Estimated lost value during negative prices |

For daily values, use graph/statistics cards that calculate a daily difference.

## 10. Troubleshooting

### Spot Price Does Not Match The Current Time

Use `sensor.export_optimizer_okte_spot_price` in the custom integration or `sensor.export_optimizer_okte_spotova_cena` in the YAML package. These read the OKTE `prices` attribute.

### Battery Discharges More Than Desired

Increase the minimum reserve SOC or disable early battery export:

```text
switch.export_optimizer_allow_battery_early_export
```

For YAML, the equivalent is:

```text
input_boolean.export_optimizer_allow_battery_early_export
```

### PV Is Curtailed When The Battery Is Full

Check:

```text
switch.inverter_export_surplus
number.inverter_export_surplus_power
number.solarny_menic_grid_max_export_power
number.export_optimizer_max_export_power_w
```

For YAML, the project maximum is:

```text
input_number.export_optimizer_max_export_power_w
```

### Home Assistant CPU Usage Is High

Do not convert trigger-based templates containing `now()`, `today_at()`, `prices`, or `detailedForecast` into triggerless template sensors. The YAML package intentionally uses trigger-based templates to avoid constant recalculation. The custom integration uses entity listeners and scheduled refreshes instead.

## 11. Safety Checklist

Before leaving active control enabled unattended:

- Confirm the selected inverter entities are correct.
- Confirm `Export First` and `Zero Export To CT` behave as expected on your inverter.
- Confirm export limits are safe for your inverter and grid connection.
- Confirm the OKTE price sensor matches the real current price period.
- Confirm the Solcast remaining-production value is realistic.
- Confirm the expected load curve becomes plausible after several days.
- Start with a low maximum export power and increase gradually.

## 12. Adapting To Other Countries Or Providers

The core idea is not Slovakia-specific, but the price source and supplier rules are local. To adapt it elsewhere, replace the spot-price source, value calculation, inverter mode names, export-control entities, and possibly the solar window.
