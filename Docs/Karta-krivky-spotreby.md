# Karta krivky očakávanej spotreby

Táto karta zobrazuje očakávanú 15-minútovú krivku spotreby domu, dnešnú zatiaľ nameranú spotrebu a posledné dve historické krivky s nižšou opacitou. Používa atribúty zo senzora `sensor.export_optimizer_solar_window_load_7d_average`.

Vyžaduje custom kartu [apexcharts-card](https://github.com/RomRider/apexcharts-card), ktorú je možné nainštalovať napríklad cez HACS.

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

      function point(item) {
        const [h, m, s] = (item.start || "00:00:00").split(":").map(Number);
        const date = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, s || 0);
        return [date.getTime(), Number(item.power_w || 0)];
      }

      return curve.map(point);
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

      function point(item) {
        const [h, m, s] = (item.start || "00:00:00").split(":").map(Number);
        const date = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, s || 0);
        return [date.getTime(), Number(item.consumption_kwh || 0) * 4000];
      }

      return intervals.map(point);
  - entity: sensor.export_optimizer_solar_window_load_7d_average
    name: Včera
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
  - entity: sensor.export_optimizer_solar_window_load_7d_average
    name: Predvčerom
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

## Poznámky

- Karta zámerne vypína hodnoty v legende cez `legend_value: false`, pretože pôvodný senzor má jednotku kWh, ale graf generuje hodnoty vo wattoch.
- Staré alebo neúplné krivky môžu po prvom nasadení vyzerať zvláštne, hlavne ak bol balík zapnutý až počas dňa. Po niekoľkých celých dňoch od 07:00 do 18:00 sa graf ustáli.
- Ak chcete zobraziť viac historických dní, skopírujte sériu `Včera` alebo `Predvčerom` a zmeňte index v `past_load_curves`, napríklad na `[2]`, `[3]` a ďalej.
