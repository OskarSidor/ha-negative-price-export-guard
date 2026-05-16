# Detailed Setup Guide

This guide covers both supported ways to use Negative Price Export Guard in Home Assistant.

The recommended path is installing the **custom integration** through HACS. During onboarding, the integration asks for the required entities, validates important units, creates UI-adjustable tuning entities, and keeps the logic in Python.

The alternative path is the **YAML package**. It remains available for advanced users who prefer a fully visible YAML implementation, but it requires manual entity replacement and more careful maintenance. It may also be useful for owners of inverter brands other than Deye who need to adapt the code for their inverter.

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

## 4. Custom Integration Setup (Recommended)

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
- energy sensors use the `kWh` unit,
- power sensors and export-power numbers use the `W` unit,
- battery SOC uses the `%` unit.

### Created Entities

The integration creates entities with the `negative_price_export_guard_` object ID. Important examples:

| Entity | Meaning |
|---|---|
| `switch.negative_price_export_guard_ochrana_exportu_zapnuta` | Main enable/disable switch for active inverter control |
| `switch.negative_price_export_guard_povolit_skory_export_z_baterie` | Allows strategic early export from battery |
| `binary_sensor.negative_price_export_guard_export_pozadovany` | Whether the integration wants `Export First` |
| `binary_sensor.negative_price_export_guard_export_je_aktivne_riadeny` | Whether the integration is actively controlling export |
| `number.negative_price_export_guard_minimalna_rezerva_baterie` | Minimum battery reserve |
| `number.negative_price_export_guard_rezerva_odhadu_spotreby` | Remaining-load safety margin |
| `number.negative_price_export_guard_typicka_minimalna_spotreba_domu` | Minimum house load including inverter self-consumption |
| `number.negative_price_export_guard_minimalny_ocakavany_prebytok` | Minimum expected surplus before intervention |
| `number.negative_price_export_guard_minimalny_riadeny_vykon_exportu` | Minimum export power when battery export is allowed |
| `number.negative_price_export_guard_maximalny_riadeny_vykon_exportu` | Maximum controlled export power, set according to your grid limit |
| `number.negative_price_export_guard_minimalna_spotova_cena_pre_export` | Price floor below which export is considered unwanted |
| `time.negative_price_export_guard_zaciatok_solarneho_okna` | Start of the daytime learning/control window |
| `time.negative_price_export_guard_koniec_solarneho_okna` | End of the daytime learning/control window |
| `sensor.negative_price_export_guard_odporucany_vykon_exportu` | Recommended strategic export power |
| `sensor.negative_price_export_guard_ocakavany_vykon_spotreby_domu` | Current expected house load from the load curve |
| `sensor.negative_price_export_guard_priemer_spotreby_v_solarnom_okne_7d` | 7-day average plus load-curve attributes |

![Example entity overview](Screenshots/Export_optimizer_entities.png)

### Recommended First Values

Start conservatively:

| Entity | Suggested value |
|---|---:|
| `number.negative_price_export_guard_minimalna_rezerva_baterie` | `30-40` |
| `number.negative_price_export_guard_rezerva_odhadu_spotreby` | `1-2` |
| `number.negative_price_export_guard_typicka_minimalna_spotreba_domu` | your normal base load, for example `200-700 W` |
| `number.negative_price_export_guard_minimalny_ocakavany_prebytok` | `1` |
| `number.negative_price_export_guard_minimalny_riadeny_vykon_exportu` | `500 W` |
| `number.negative_price_export_guard_maximalny_riadeny_vykon_exportu` | start low, then increase gradually |
| `number.negative_price_export_guard_minimalna_spotova_cena_pre_export` | `0 EUR/MWh` |

Keep `switch.negative_price_export_guard_ochrana_exportu_zapnuta` off until you have checked the calculated sensors. Then enable it for a real test window.

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

`sensor.negative_price_export_guard_priemer_spotreby_v_solarnom_okne_7d` contains these attributes:

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
  title: Export Optimizer
  show_header_toggle: false
filter:
  include:
    - entity_id: /negative_price_export_guard/
      sort:
        method: entity_id
```

For the YAML package, use the `export_optimizer` filter and hide technical helpers that users normally do not edit:

```yaml
filter:
  include:
    - entity_id: /export_optimizer/
      sort:
        method: entity_id
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
  title: Expected house-load curve during the day
  show_states: false
graph_span: 11h
span:
  start: day
  offset: +7h
now:
  show: true
  label: Now
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
    labels:
      formatter: |
        EVAL:function(value) {
          return Math.round(value);
        }
  tooltip:
    x:
      format: HH:mm
    "y":
      formatter: |
        EVAL:function(value) {
          return Math.round(value) + " W";
        }
series:
  - entity: sensor.negative_price_export_guard_priemer_spotreby_v_solarnom_okne_7d
    name: Expected load
    type: line
    color: "#f59e0b"
    stroke_width: 4
    show:
      legend_value: false
    data_generator: |
      const curve = entity.attributes.load_curve || [];
      const now = new Date();

      function point(item) {
        const [h, m, s] = (item.start || "00:00:00").split(":").map(Number);
        const date = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, s || 0);
        return [date.getTime(), Number(item.power_w || 0)];
      }

      return curve.map(point);
  - entity: sensor.negative_price_export_guard_priemer_spotreby_v_solarnom_okne_7d
    name: Measured today
    type: line
    stroke_width: 2
    opacity: 0.9
    show:
      legend_value: false
    data_generator: |
      const intervals = entity.attributes.today_load_curve?.intervals || [];
      const now = new Date();

      function point(item) {
        const [h, m, s] = (item.start || "00:00:00").split(":").map(Number);
        const date = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, s || 0);
        return [date.getTime(), Number(item.consumption_kwh || 0) * 4000];
      }

      return intervals.map(point);
  - entity: sensor.negative_price_export_guard_priemer_spotreby_v_solarnom_okne_7d
    name: Yesterday
    type: line
    color: "#94a3b8"
    opacity: 0.4
    stroke_width: 2
    show:
      legend_value: false
    data_generator: |
      const day = (entity.attributes.past_load_curves || [])[0];
      if (!day?.intervals) return [];
      const now = new Date();

      function point(item) {
        const [h, m, s] = (item.start || "00:00:00").split(":").map(Number);
        const date = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, s || 0);
        return [date.getTime(), Number(item.consumption_kwh || 0.5) * 4000];
      }

      return day.intervals.map(point);
  - entity: sensor.negative_price_export_guard_priemer_spotreby_v_solarnom_okne_7d
    name: Day before yesterday
    type: line
    color: "#94a3b8"
    opacity: 0.4
    stroke_width: 2
    show:
      legend_value: false
    data_generator: |
      const day = (entity.attributes.past_load_curves || [])[1];
      if (!day?.intervals) return [];
      const now = new Date();

      function point(item) {
        const [h, m, s] = (item.start || "00:00:00").split(":").map(Number);
        const date = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, s || 0);
        return [date.getTime(), Number(item.consumption_kwh || 0) * 4000];
      }

      return day.intervals.map(point);
```

You can add more past-day series from `past_load_curves` in the same way if you want to compare more history.

## 9. Accounting Sensors

The project exposes cumulative result sensors:

| Entity | Meaning |
|---|---|
| `sensor.negative_price_export_guard_exportovana_energia_pri_zapornej_spotovej_cene` | kWh exported during negative spot prices |
| `sensor.negative_price_export_guard_energia_exportovana_automatizaciou` | kWh exported while active control was on |
| `sensor.negative_price_export_guard_uspora_z_riadeneho_exportu` | Estimated saved value |
| `sensor.negative_price_export_guard_premrhany_potencial_pri_zapornej_cene` | Estimated lost value during negative prices |

For daily values, use graph/statistics cards that calculate a daily difference.

## 10. Troubleshooting

### Spot Price Does Not Match The Current Time

Use `sensor.negative_price_export_guard_okte_spotova_cena` in the custom integration or `sensor.export_optimizer_okte_spotova_cena` in the YAML package. These read the OKTE `prices` attribute.

### Battery Discharges More Than Desired

Increase the minimum reserve SOC or disable early battery export:

```text
switch.negative_price_export_guard_povolit_skory_export_z_baterie
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
number.negative_price_export_guard_maximalny_riadeny_vykon_exportu
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
