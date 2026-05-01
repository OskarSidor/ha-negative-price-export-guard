# Home Assistant: ochrana exportu pri záporných spotových cenách

Automatizácia pre Home Assistant, ktorá pomáha majiteľom fotovoltiky obmedziť zbytočný export elektriny do siete počas záporných spotových cien. Projekt vznikol pre slovenské podmienky, hlavne pre prípady, keď dodávateľ nepočíta elektrinu dodanú do virtuálnej batérie alebo podobnej služby počas záporných cien.

Typický príklad: počas slnečného dňa sa batéria nabije doplna, fotovoltika má prebytok, ale OKTE spotová cena je záporná. Ak sa elektrina vtedy odošle do siete, môže mať nulovú hodnotu pre virtuálnu batériu. Tento balík sa snaží vytvoriť miesto v batérii ešte pred záporným cenovým oknom a zároveň pri plnej batérii zabrániť zbytočnému obmedzovaniu PV výroby.

English version: [README.en.md](README.en.md)

## Čo projekt robí

- Počíta aktuálnu OKTE spotovú cenu z atribútu `prices`, nie iba zo stavu senzora.
- Sleduje budúce cenové obdobia pod nastavenou hranicou do 18:00.
- Učí sa spotrebu domu v solárnom okne 07:00-18:00 z posledných dní.
- Používa Solcast dennú predpoveď, detailnú predpoveď a novú entitu zostávajúcej výroby dnes.
- Odhaduje zostávajúcu spotrebu domu vrátane minimálnej základnej spotreby.
- Počíta očakávaný prebytok až po zohľadnení zostávajúcej kapacity batérie na nabíjanie.
- Prepína menič do `Export First` iba vtedy, keď treba strategicky vytvoriť miesto v batérii.
- Pri vypnutom skorom exporte z batérie obmedzí výkon len na aktuálny PV prebytok, bez vynútenia minimálneho exportného výkonu.
- Pri plnej batérii v režime `Zero Export To CT` nastaví bezpečný exportný limit, aby menič zbytočne neobmedzoval PV výrobu.
- Počíta energiu exportovanú počas záporných cien, energiu exportovanú automatizáciou, odhad úspory a stratený potenciál.

## Pre koho je to vhodné

Projekt je určený hlavne pre používateľov, ktorí majú:

- fotovoltiku s batériou,
- Home Assistant,
- Deye alebo podobný hybridný menič dostupný cez Solarman alebo inú integráciu,
- spotové ceny z OKTE,
- predpoveď výroby zo Solcastu,
- dodávateľa alebo službu virtuálnej batérie, kde export počas záporných cien nemá hodnotu.

Balík je pripravený pre Deye/Solarman názvy entít, ale dá sa prispôsobiť aj iným meničom, ak v Home Assistant existujú podobné entity.

## Požiadavky

### Integrácie

- **[OKTE DAM](https://github.com/rgildein/okte-home-assistant)** alebo podobná integrácia so spotovými cenami a atribútom `prices`.
- **[Solcast](https://github.com/BJReplay/ha-solcast-solar)** s dennou predpoveďou, atribútom `detailedForecast` a senzorom zostávajúcej výroby dnes.
- **[Solarman](https://github.com/davidrapan/ha-solarman) / Deye** alebo iná integrácia meniča, ktorá vie čítať stav batérie, meniť režim exportu a nastavovať limity exportu.

### Očakávané entity

| Účel | Predvolená entita |
|---|---|
| OKTE ceny s atribútom `prices` | `sensor.okte_ceny_elektriny_prices` |
| Solcast predpoveď dnes s `detailedForecast` | `sensor.solcast_pv_forecast_predpoved_dnes` |
| Solcast zostávajúca výroba dnes | `sensor.solcast_pv_forecast_predpoved_zostavajuca_dnes` |
| Denná spotreba domu v kWh | `sensor.inverter_today_load_consumption` |
| Celkový export do siete v kWh | `sensor.inverter_total_energy_export` |
| Denná PV výroba v kWh | `sensor.inverter_today_production` |
| Stav batérie v % | `sensor.inverter_battery` |
| Kapacita batérie v kWh | `sensor.inverter_battery_capacity` |
| Aktuálny PV výkon vo W | `sensor.inverter_pv_power` |
| Aktuálna spotreba domu vo W | `sensor.inverter_load_power` |
| Režim meniča | `select.inverter_work_mode` |
| Prepínač exportu PV prebytkov | `switch.inverter_export_surplus` |
| Aktuálny limit exportu do siete | `number.inverter_export_surplus_power` |
| Maximálny povolený export meniča alebo siete | `number.solarny_menic_grid_max_export_power` |
| Nočný tarif pre odhad hodnoty energie | `input_number.cena_elektriny_nocny_tarif` |

Ak sa vaše entity volajú inak, upravte ich v súbore [`Packages/negative_price_export_guard.yaml`](Packages/negative_price_export_guard.yaml). Nepoužívajte `input_text` na nepriame pomenovanie entít v triggeroch; Home Assistant potrebuje v triggeroch reálne entity ID.

## Ako logika funguje

1. O 07:00 uloží stav denného počítadla spotreby domu.
2. O 18:00 uloží spotrebu za solárne okno a udržiava posledných 7 vzoriek v atribúte `past_consumption`.
3. Každých 10 minút a pri zmene dôležitých entít prepočíta zostávajúcu spotrebu, cieľové SOC, očakávaný prebytok a odporúčaný exportný výkon.
4. Ak príde cena pod nastavenou hranicou, menič sa vráti do `Zero Export To CT`.
5. Ak je potrebné vytvoriť miesto pred budúcim záporným oknom, automatizácia nastaví exportný výkon a prepne menič do `Export First`.
6. Ak je batéria plná, export prebytkov je zapnutý a strategický export nie je požadovaný, nastaví sa exportný limit na menšiu hodnotu z `input_number.export_optimizer_max_export_power_w` a `number.solarny_menic_grid_max_export_power`.

## Inštalácia

1. V Home Assistant povoľte používanie packages, ak ich ešte nepoužívate.

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

2. Skopírujte `Packages/negative_price_export_guard.yaml` do `config/packages/negative_price_export_guard.yaml`.
3. Skontrolujte a upravte entity podľa svojej inštalácie.
4. V Home Assistant spustite `Nastavenia -> Vývojárske nástroje -> YAML -> Skontrolovať konfiguráciu`.
5. Ak je konfigurácia v poriadku, reštartujte Home Assistant.
6. Po reštarte skontrolujte nové entity začínajúce na `export_optimizer_`.

Podrobnejší návod je v súbore [Docs/Nastavenie.md](Docs/Nastavenie.md).

## Karta s entitami projektu

Na rýchle vyhľadanie a úpravu všetkých entít vytvorených týmto projektom môžete použiť kartu cez [auto-entities](https://github.com/thomasloven/lovelace-auto-entities). Túto custom kartu je potrebné mať nainštalovanú v Home Assistant, napríklad cez HACS.

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

Karta filtruje entity podľa `export_optimizer` v entity ID. Zámerne skrýva technický záznam rannej spotreby a čas jeho uloženia, ktoré sa nastavujú automaticky.

## Dôležité ovládacie prvky

| Entita | Význam |
|---|---|
| `input_boolean.export_optimizer_export_guard_enabled` | Hlavné zapnutie/vypnutie ochrany |
| `input_boolean.export_optimizer_allow_battery_early_export` | Povolenie strategického exportu z batérie |
| `input_number.export_optimizer_min_reserve_soc` | Minimálna rezerva batérie |
| `input_number.export_optimizer_consumption_margin_kwh` | Bezpečnostná rezerva odhadu spotreby |
| `input_number.export_optimizer_typical_idle_power_w` | Minimálna očakávaná spotreba domu vrátane meniča |
| `input_number.export_optimizer_export_surplus_threshold_kwh` | Minimálny prebytok, od ktorého sa oplatí zasiahnuť |
| `input_number.export_optimizer_min_export_power_w` | Spodný limit riadeného exportu pri exporte z batérie |
| `input_number.export_optimizer_max_export_power_w` | Horný limit riadeného exportu a limit pri plnej batérii |
| `input_number.export_optimizer_price_floor` | Cena, od ktorej sa export považuje za bezpečný |

## Odporúčané úvodné nastavenie

| Nastavenie | Odporúčaná hodnota |
|---|---:|
| Minimálna rezerva batérie | `40 %` |
| Rezerva odhadu spotreby | `2 kWh` |
| Typická minimálna spotreba domu | `200-500 W` podľa domu a meniča |
| Minimálny očakávaný prebytok | `1 kWh` |
| Minimálny riadený export | `500 W` |
| Maximálny riadený export | `3000 W` |
| Minimálna spotová cena pre export | `0 EUR/MWh` |

## Čo sledovať po spustení

| Entita | Čo znamená |
|---|---|
| `sensor.export_optimizer_okte_spotova_cena` | Aktuálna spotová cena vypočítaná z OKTE atribútov |
| `sensor.export_optimizer_negative_price_minutes_until_18` | Koľko minút pod cenovou hranicou zostáva do 18:00 |
| `sensor.export_optimizer_recommended_export_power` | Odporúčaný výkon strategického exportu |
| `binary_sensor.export_optimizer_export_wanted` | Či má automatizácia prepnúť do `Export First` |
| `input_boolean.export_optimizer_export_guard_active` | Či automatizácia práve riadi export |
| `sensor.export_optimizer_remaining_solar_window_load_estimate` | Odhad zostávajúcej spotreby |
| `sensor.export_optimizer_expected_surplus_today` | Prebytok po odpočítaní spotreby a zostávajúcej kapacity batérie |
| `sensor.export_optimizer_battery_target_soc` | Cieľová hranica SOC podľa odhadu spotreby a výroby |
| `sensor.export_optimizer_exported_energy_by_automation` | Energia exportovaná automatizáciou |
| `sensor.export_optimizer_exported_energy_during_negative_spot_price` | Energia exportovaná počas záporných cien |
| `sensor.export_optimizer_automation_export_savings` | Odhad zachránenej hodnoty |
| `sensor.export_optimizer_negative_price_wasted_potential` | Odhad stratenej hodnoty pri záporných cenách |

## Časté problémy

### Spotová cena nesedí s aktuálnym časom

Používajte `sensor.export_optimizer_okte_spotova_cena`, nie priamo stav OKTE senzora.

### PV sa obmedzuje pri plnej batérii

Skontrolujte, či existujú a dávajú správne hodnoty:

```text
switch.inverter_export_surplus
number.solarny_menic_grid_max_export_power
input_number.export_optimizer_max_export_power_w
```

### Batéria sa vybíja viac, ako chcete

Zvýšte `input_number.export_optimizer_min_reserve_soc` alebo vypnite `input_boolean.export_optimizer_allow_battery_early_export`.

### Home Assistant má vysoké CPU využitie

Nemeňte trigger-based template senzory s `now()`, `today_at()`, `prices` alebo `detailedForecast` na bežné template senzory bez triggerov.

## Screenshoty na doplnenie

### 1. Denný graf výroby, spotreby, batérie a siete

<!-- TODO: Sem doplniť screenshot grafu, kde vidno PV výrobu, spotrebu domu, tok do siete a tok z/do batérie počas dňa so zápornými cenami. -->

### 2. Detail OKTE cien a záporného cenového okna

<!-- TODO: Sem doplniť screenshot OKTE cien alebo graf spotovej ceny s vyznačeným záporným obdobím. -->

### 3. Stav pomocných senzorov automatizácie

<!-- TODO: Sem doplniť screenshot dashboardu s entitami export_optimizer_recommended_export_power, export_optimizer_export_wanted, export_optimizer_remaining_solar_window_load_estimate a export_optimizer_negative_price_minutes_until_18. -->

### 4. Úspora a stratený potenciál

<!-- TODO: Sem doplniť screenshot grafu kumulatívnej úspory a strateného potenciálu. -->

## Bezpečnostné poznámky

- Najprv testujte s nízkym maximálnym exportným výkonom.
- Overte, že váš menič naozaj chápe `Export First` a `Zero Export To CT` tak, ako očakávate.
- Skontrolujte, či zmena `number.inverter_export_surplus_power` nemá vedľajšie účinky aj v iných režimoch meniča.
- Tento projekt nie je finančné, právne ani elektrotechnické odporúčanie.
- Používate ho na vlastnú zodpovednosť.
