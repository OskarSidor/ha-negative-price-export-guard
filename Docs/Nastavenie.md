# Podrobný návod na nastavenie

Tento návod opisuje oba podporované spôsoby použitia Negative Price Export Guard v Home Assistant.

Odporúčaný spôsob je **custom integrácia**. Pri prvom nastavení sa spýta na potrebné entity, overí dôležité jednotky, vytvorí ovládacie entity v UI a logiku drží v Pythone.

Alternatívny spôsob je **YAML package**. Ostáva dostupný pre pokročilých používateľov, ktorí chcú mať celú logiku viditeľnú v YAML, ale vyžaduje ručnú výmenu entity ID a pozornejšiu údržbu.

## 1. Vyberte spôsob nastavenia

| Spôsob | Pre koho je vhodný | Hlavný kompromis |
|---|---|---|
| Custom integrácia | Väčšina používateľov | Jednoduchšie nastavenie, UI ovládanie, kontrola entít |
| YAML package | Pokročilí používatelia | Celá logika je v YAML, ale entity ID sa upravujú ručne |

Neinštalujte oba spôsoby naraz, pokiaľ jeden z nich zámerne nevypnete. Oba môžu ovládať rovnaké entity meniča, takže súčasné spustenie by bolo neprehľadné a potenciálne nebezpečné.

## 2. Požadované integrácie

### OKTE ceny

Odporúčaná integrácia:

- [OKTE DAM](https://github.com/rgildein/okte-home-assistant)

Požiadavky:

- senzor s aktuálnymi alebo budúcimi OKTE cenami,
- atribút `prices` s 15-minútovými obdobiami,
- ceny v `EUR/MWh`.

Predvolená entita projektu je:

```text
sensor.okte_ceny_elektriny_prices
```

Optimalizér počíta aktuálnu cenu z atribútu `prices`, pretože stav pôvodného senzora sa môže aktualizovať neskôr ako reálna 15-minútová hranica ceny.

### Solcast predpoveď výroby

Odporúčaná integrácia:

- [Solcast Solar](https://github.com/BJReplay/ha-solcast-solar)

Požadované entity:

```text
sensor.solcast_pv_forecast_predpoved_dnes
sensor.solcast_pv_forecast_predpoved_zostavajuca_dnes
```

Prvá entita musí mať atribút `detailedForecast`. Druhá entita má predstavovať zostávajúcu predpoveď výroby pre dnešok v `kWh`.

### Integrácia meniča

Projekt vznikol okolo entít typu Deye/Solarman.

Odporúčaná Solarman integrácia:

- [ha-solarman](https://github.com/davidrapan/ha-solarman)

Home Assistant musí vedieť čítať SOC batérie, PV výkon, spotrebu domu, dennú výrobu, dennú spotrebu, celkový export do siete, aktuálne nastavenia exportu, režim meniča a limity exportného výkonu.

## 3. Požadované zdrojové entity

| Účel | Predvolená entita | Očakávaná jednotka/doména |
|---|---|---|
| OKTE ceny s atribútom `prices` | `sensor.okte_ceny_elektriny_prices` | `EUR/MWh` |
| Solcast predpoveď dnes s `detailedForecast` | `sensor.solcast_pv_forecast_predpoved_dnes` | `kWh` |
| Solcast zostávajúca výroba dnes | `sensor.solcast_pv_forecast_predpoved_zostavajuca_dnes` | `kWh` |
| Denná spotreba domu | `sensor.inverter_today_load_consumption` | `kWh` |
| Celkový export do siete | `sensor.inverter_total_energy_export` | `kWh` |
| Denná PV výroba | `sensor.inverter_today_production` | `kWh` |
| SOC batérie | `sensor.inverter_battery` | `%` |
| Kapacita batérie | `sensor.inverter_battery_capacity` | `kWh` |
| Aktuálny PV výkon | `sensor.inverter_pv_power` | `W` |
| Aktuálna spotreba domu | `sensor.inverter_load_power` | `W` |
| Režim meniča | `select.inverter_work_mode` | `select` |
| Prepínač exportu PV prebytkov | `switch.inverter_export_surplus` | `switch` |
| Aktuálny limit exportu do siete | `number.inverter_export_surplus_power` | `W` |
| Maximálny povolený export meniča alebo siete | `number.solarny_menic_grid_max_export_power` | `W` |
| Voliteľný nočný tarif pre odhad hodnoty energie | `input_number.cena_elektriny_nocny_tarif` | `EUR/kWh` |

Ak voliteľný pomocník nočného tarifu nie je v custom integrácii nastavený, integrácia použije fallback `0.054 EUR/kWh`.

## 4. Nastavenie custom integrácie odporúčané

### Inštalácia

Použite jeden z týchto spôsobov:

1. Skopírujte `custom_components/negative_price_export_guard` do:

   ```text
   config/custom_components/negative_price_export_guard
   ```

2. Alebo pridajte tento repozitár ako custom repository v HACS a nainštalujte ho ako integráciu.

Po inštalácii reštartujte Home Assistant.

### Pridanie integrácie

V Home Assistant:

```text
Nastavenia -> Zariadenia a služby -> Pridať integráciu -> Negative Price Export Guard
```

V sprievodcovi vyberte zdrojové entity. Formulár obsahuje predvolené entity ID a veľa rozbaľovacích polí filtruje podľa očakávanej domény alebo device class, takže správne entity by sa mali hľadať ľahšie.

Sprievodca overí:

- či existujú povinné entity,
- či OKTE senzor má atribút `prices`,
- či Solcast predpoveď má atribút `detailedForecast`,
- či energetické senzory používajú `kWh`,
- či výkonové senzory a exportné čísla používajú `W`,
- či SOC batérie používa `%`.

### Vytvorené entity

Integrácia vytvára entity s objektovým ID `export_optimizer_`. Dôležité príklady:

| Entita | Význam |
|---|---|
| `switch.export_optimizer_guard_enabled` | Hlavné zapnutie alebo vypnutie aktívneho riadenia meniča |
| `switch.export_optimizer_allow_battery_early_export` | Povolenie skorého strategického exportu z batérie |
| `binary_sensor.export_optimizer_export_wanted` | Či integrácia požaduje `Export First` |
| `binary_sensor.export_optimizer_export_active` | Či integrácia práve aktívne riadi export |
| `number.export_optimizer_min_reserve_soc` | Minimálna rezerva batérie |
| `number.export_optimizer_consumption_margin_kwh` | Bezpečnostná rezerva odhadu spotreby |
| `number.export_optimizer_typical_idle_power_w` | Minimálna spotreba domu vrátane vlastnej spotreby meniča |
| `number.export_optimizer_export_surplus_threshold_kwh` | Minimálny očakávaný prebytok pred zásahom |
| `number.export_optimizer_min_export_power_w` | Minimálny exportný výkon pri povolenom exporte z batérie |
| `number.export_optimizer_max_export_power_w` | Maximálny riadený exportný výkon |
| `number.export_optimizer_price_floor` | Cenová hranica, pod ktorou je export nežiaduci |
| `time.export_optimizer_solar_window_start` | Začiatok denného učiaceho a riadiaceho okna |
| `time.export_optimizer_solar_window_end` | Koniec denného učiaceho a riadiaceho okna |
| `sensor.export_optimizer_recommended_export_power` | Odporúčaný strategický exportný výkon |
| `sensor.export_optimizer_expected_load_power` | Aktuálny očakávaný výkon spotreby z krivky |
| `sensor.export_optimizer_solar_window_load_7d_average` | 7d priemer a atribúty krivky spotreby |

![Prehľad entít projektu](Screenshots/Export_optimizer_entities.png)

### Odporúčané prvé hodnoty

Začnite konzervatívne:

| Entita | Odporúčaná hodnota |
|---|---:|
| `number.export_optimizer_min_reserve_soc` | `30-40` |
| `number.export_optimizer_consumption_margin_kwh` | `1-2` |
| `number.export_optimizer_typical_idle_power_w` | bežný základný odber, napríklad `200-700 W` |
| `number.export_optimizer_export_surplus_threshold_kwh` | `1` |
| `number.export_optimizer_min_export_power_w` | `500 W` |
| `number.export_optimizer_max_export_power_w` | začnite nízko a zvyšujte postupne |
| `number.export_optimizer_price_floor` | `0 EUR/MWh` |

Nechajte `switch.export_optimizer_guard_enabled` vypnutý, kým neskontrolujete vypočítané senzory. Potom ho zapnite na reálne testovacie okno.

## 5. Nastavenie YAML package manuálne

Túto cestu použite iba vtedy, ak chcete YAML implementáciu.

### Povolenie packages

V `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Ak treba, vytvorte priečinok:

```text
config/packages
```

Skopírujte:

```text
Packages/negative_price_export_guard.yaml
```

do:

```text
config/packages/negative_price_export_guard.yaml
```

### Úprava entity ID

Otvorte YAML súbor a nahraďte všetky predvolené zdrojové entity vlastnými entity ID. Nepoužívajte `input_text` na nepriame pomenovanie entít v triggeroch. Home Assistant triggery potrebujú reálne entity ID priamo v YAML.

YAML package vytvára `input_number`, `input_boolean`, `input_datetime`, template senzory, binary senzory a automatizácie. Custom integrácia namiesto toho vytvára `number`, `switch`, `time`, `sensor` a `binary_sensor` entity.

### Kontrola konfigurácie

Pred reštartom:

```text
Nastavenia -> Vývojárske nástroje -> YAML -> Skontrolovať konfiguráciu
```

Nereštartujte, kým kontrola neprejde.

### YAML ovládacie entity

| YAML entita | Význam |
|---|---|
| `input_boolean.export_optimizer_export_guard_enabled` | Hlavné zapnutie alebo vypnutie |
| `input_boolean.export_optimizer_allow_battery_early_export` | Povolenie skorého exportu z batérie |
| `input_number.export_optimizer_min_reserve_soc` | Minimálna rezerva batérie |
| `input_number.export_optimizer_consumption_margin_kwh` | Rezerva odhadu spotreby |
| `input_number.export_optimizer_typical_idle_power_w` | Minimálna očakávaná spotreba domu |
| `input_number.export_optimizer_max_export_power_w` | Maximálny riadený exportný výkon |
| `input_number.export_optimizer_price_floor` | Cenová hranica exportu |

## 6. Ako logika funguje

1. Systém zaznamená počítadlo spotreby domu na začiatku solárneho okna.
2. Každých 15 minút počas solárneho okna uloží spotrebu za predchádzajúci interval.
3. Na konci solárneho okna uloží dokončenú dennú krivku.
4. Drží najviac 7 dní kriviek a vytvára priemernú 15-minútovú `load_curve`.
5. Odhaduje zostávajúcu spotrebu z krivky, bezpečnostnej rezervy a minimálneho základného odberu.
6. Kombinuje zostávajúcu spotrebu, Solcast zostávajúcu výrobu, SOC a kapacitu batérie.
7. Ak sa očakáva budúci záporný cenový blok, vypočíta potrebný export pred týmto blokom.
8. Ak je export z batérie vypnutý alebo SOC je na cieľovej hodnote či nižšie, odporúčaný export sa obmedzí na živý PV prebytok a nevynucuje minimálny exportný výkon.
9. Ak je aktuálna cena pod hranicou, menič ostáva v `Zero Export To CT`.
10. Ak je batéria plná, exportný limit sa môže zvýšiť, aby sa znížilo krátenie PV výroby.

## 7. Krivka spotreby

`sensor.export_optimizer_solar_window_load_7d_average` obsahuje tieto atribúty:

| Atribút | Význam |
|---|---|
| `past_consumption` | Posledných 7 denných súčtov spotreby v solárnom okne |
| `today_load_curve` | Dnešné zatiaľ namerané 15-minútové intervaly |
| `past_load_curves` | Posledných 7 dokončených denných 15-minútových kriviek |
| `load_curve` | Priemerná 15-minútová krivka používaná optimalizérom |
| `last_interval_total_kwh` | Interný stav počítadla |
| `current_interval_index` | Aktuálny 15-minútový interval v solárnom okne |

Príklad položky krivky:

```yaml
index: 0
start: "07:00:00"
end: "07:15:00"
consumption_kwh: 0.12
power_w: 480
samples: 4
```

![Krivka očakávanej spotreby](Screenshots/Krivka_spotreby.png)

## 8. Dashboard karty

### Prehľad entít cez Auto Entities

Najprv nainštalujte [auto-entities](https://github.com/thomasloven/lovelace-auto-entities).

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

Pri YAML package môžete skryť technických pomocníkov, ktorých bežne netreba upravovať:

```yaml
filter:
  exclude:
    - entity_id: input_number.export_optimizer_solar_window_start_load_kwh
    - entity_id: input_datetime.export_optimizer_solar_window_start_recorded
```

### Krivka spotreby cez ApexCharts

Najprv nainštalujte [apexcharts-card](https://github.com/RomRider/apexcharts-card).

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

Série pre predchádzajúce dni môžete doplniť z atribútu `past_load_curves`.

## 9. Účtovné senzory

Projekt vystavuje kumulatívne senzory výsledkov:

| Entita | Význam |
|---|---|
| `sensor.export_optimizer_exported_energy_during_negative_spot_price` | kWh exportované počas záporných spotových cien |
| `sensor.export_optimizer_exported_energy_by_automation` | kWh exportované počas aktívneho riadenia |
| `sensor.export_optimizer_automation_export_savings` | Odhad zachránenej hodnoty |
| `sensor.export_optimizer_negative_price_wasted_potential` | Odhad stratenej hodnoty počas záporných cien |

Na denné hodnoty použite grafy alebo štatistiky, ktoré počítajú denný rozdiel.

## 10. Riešenie problémov

### Spotová cena nesedí s aktuálnym časom

Použite `sensor.export_optimizer_okte_spot_price` v custom integrácii alebo `sensor.export_optimizer_okte_spotova_cena` v YAML package. Tieto senzory čítajú OKTE atribút `prices`.

### Batéria sa vybíja viac, ako chcete

Zvýšte minimálnu rezervu SOC alebo vypnite skorý export z batérie:

```text
switch.export_optimizer_allow_battery_early_export
```

Pri YAML package je ekvivalent:

```text
input_boolean.export_optimizer_allow_battery_early_export
```

### PV sa kráti pri plnej batérii

Skontrolujte:

```text
switch.inverter_export_surplus
number.inverter_export_surplus_power
number.solarny_menic_grid_max_export_power
number.export_optimizer_max_export_power_w
```

Pri YAML package je projektové maximum:

```text
input_number.export_optimizer_max_export_power_w
```

### Home Assistant má vysoké CPU využitie

Nemeňte trigger-based šablóny s `now()`, `today_at()`, `prices` alebo `detailedForecast` na template senzory bez triggerov. YAML package používa trigger-based šablóny zámerne, aby sa veľké výpočty neprepočítavali stále. Custom integrácia používa entity listenery a plánované refresh intervaly.

## 11. Bezpečnostný checklist

Predtým, než necháte aktívne riadenie bežať bez dozoru:

- Overte, že zvolené entity meniča sú správne.
- Overte, že `Export First` a `Zero Export To CT` fungujú na vašom meniči očakávane.
- Overte, že exportné limity sú bezpečné pre menič a pripojenie do siete.
- Overte, že OKTE senzor zodpovedá reálnemu aktuálnemu cenovému obdobiu.
- Overte, že Solcast zostávajúca výroba je realistická.
- Overte, že krivka očakávanej spotreby je po pár dňoch učenia rozumná.
- Začnite s nízkym maximálnym exportným výkonom a zvyšujte postupne.

## 12. Prispôsobenie iným krajinám alebo dodávateľom

Základná myšlienka nie je striktne slovenská, ale zdroj cien a pravidlá dodávateľa sú lokálne. Pri použití inde treba nahradiť zdroj spotových cien, výpočet hodnoty energie, názvy režimov meniča, entity riadenia exportu a prípadne solárne okno.
