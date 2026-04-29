# Home Assistant: ochrana exportu pri záporných spotových cenách

Automatizácia pre Home Assistant, ktorá pomáha majiteľom fotovoltiky obmedziť export elektriny do siete počas záporných spotových cien. Projekt vznikol pre slovenské podmienky, hlavne pre situácie, keď dodávateľ nepočíta elektrinu dodanú do virtuálnej batérie alebo podobnej služby počas záporných cien.

Typický príklad: počas slnečného dňa sa batéria nabije doplna, fotovoltika má prebytok, ale OKTE spotová cena je záporná. Ak sa elektrina vtedy odošle do siete, môže mať nulovú hodnotu pre virtuálnu batériu. Tento balík sa snaží vytvoriť miesto v batérii ešte pred záporným cenovým oknom, aby sa počas záporných cien čo najviac energie uložilo lokálne namiesto posielania do siete.

English version: [README.en.md](README.en.md)

## Čo projekt robí

- Počíta aktuálnu OKTE spotovú cenu z atribútu `prices`, nie iba zo stavu senzora.
- Sleduje budúce záporné spotové ceny do 17:00.
- Učí sa spotrebu domu v solárnom okne 07:00-17:00 z posledných dní.
- Používa dennú predpoveď výroby zo Solcastu vrátane detailnej predpovede.
- Vypočíta odporúčaný výkon exportu pred záporným cenovým oknom.
- Prepína menič do režimu `Export First` iba vtedy, keď treba strategicky vytvoriť miesto v batérii.
- Po skončení potreby riadeného exportu vráti menič do `Zero Export To CT`.
- Má prepínač, ktorým sa dá zakázať skorý export z batérie a povoliť iba export aktuálneho PV prebytku.
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

## Ako logika funguje

Automatizácia rozlišuje bežný export prebytkov od strategického exportu z batérie.

V normálnom stave je menič v režime `Zero Export To CT`. Ak váš menič v tomto režime stále dokáže posielať skutočný PV prebytok do siete, automatizácia ho necháva tak. Do režimu `Export First` prepína iba vtedy, keď pred budúcim záporným cenovým oknom potrebuje uvoľniť miesto v batérii.

Zjednodušene:

1. Zistí, či ešte dnes do 17:00 príde záporná spotová cena.
2. Odhadne, koľko PV energie príde pred týmto záporným oknom a počas neho.
3. Odhadne zostávajúcu spotrebu domu v solárnom okne.
4. Skontroluje aktuálny stav batérie a cieľovú rezervu.
5. Vypočíta, koľko energie treba vopred exportovať, aby batéria mala miesto na výrobu počas záporných cien.
6. Nastaví limit exportu cez `number.inverter_export_surplus_power`.
7. Prepne menič do `Export First` iba počas potrebného strategického exportu.
8. Pri zápornej cene alebo po skončení potreby exportu vráti menič do `Zero Export To CT`.

## Požiadavky

### Integrácie

Potrebujete funkčné entity z týchto zdrojov:

- **OKTE DAM** alebo podobná integrácia so spotovými cenami a atribútom `prices`.
- **Solcast** s dennou predpoveďou a atribútom `detailedForecast`.
- **Solarman / Deye** alebo iná integrácia meniča, ktorá vie čítať stav batérie a meniť režim exportu.

### Očakávané entity

Balík štandardne očakáva tieto entity:

| Účel | Predvolená entita |
|---|---|
| OKTE ceny s atribútom `prices` | `sensor.okte_ceny_elektriny_prices` |
| Solcast predpoveď dnes | `sensor.solcast_pv_forecast_predpoved_dnes` |
| Denná spotreba domu v kWh | `sensor.inverter_today_load_consumption` |
| Celkový export do siete v kWh | `sensor.inverter_total_energy_export` |
| Denná PV výroba v kWh | `sensor.inverter_today_production` |
| Stav batérie v % | `sensor.inverter_battery` |
| Kapacita batérie v kWh | `sensor.inverter_battery_capacity` |
| Aktuálny PV výkon vo W | `sensor.inverter_pv_power` |
| Aktuálna spotreba domu vo W | `sensor.inverter_load_power` |
| Režim meniča | `select.inverter_work_mode` |
| Limit exportu do siete | `number.inverter_export_surplus_power` |
| Nočný tarif pre odhad hodnoty energie | `input_number.cena_elektriny_nocny_tarif` |

Ak sa vaše entity volajú inak, upravte ich v súbore [`Packages/negative_price_export_guard.yaml`](Packages/negative_price_export_guard.yaml).

## Inštalácia

1. V Home Assistant povoľte používanie packages, ak ich ešte nepoužívate.

   V `configuration.yaml` pridajte napríklad:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

2. V adresári s konfiguráciou Home Assistant vytvorte priečinok:

   ```text
   packages
   ```

3. Skopírujte súbor:

   ```text
   Packages/negative_price_export_guard.yaml
   ```

   do svojho Home Assistant priečinka:

   ```text
   config/packages/negative_price_export_guard.yaml
   ```

4. Skontrolujte a upravte entity podľa svojej inštalácie.

5. V Home Assistant choďte do:

   ```text
   Nastavenia -> Vývojárske nástroje -> YAML -> Skontrolovať konfiguráciu
   ```

6. Ak je konfigurácia v poriadku, reštartujte Home Assistant.

7. Po reštarte skontrolujte nové entity začínajúce na `export_optimizer_`.

## Pomocník pre cenu energie

Balík očakáva helper:

```yaml
input_number.cena_elektriny_nocny_tarif
```

Tento helper reprezentuje konzervatívnu hodnotu energie v EUR/kWh, ktorú by ste inak mohli neskôr spotrebovať z virtuálnej batérie. Používa sa na výpočet strateneho potenciálu pri exporte počas záporných cien.

Ak ho ešte nemáte, vytvorte ho v UI:

```text
Nastavenia -> Zariadenia a služby -> Pomocníci -> Vytvoriť pomocníka -> Číslo
```

Odporúčaný začiatok môže byť napríklad hodnota vášho nočného tarifu v EUR/kWh.

## Dôležité ovládacie prvky

Po inštalácii vzniknú viaceré pomocníky. Najdôležitejšie sú:

| Entita | Význam |
|---|---|
| `input_boolean.export_optimizer_export_guard_enabled` | Hlavné zapnutie/vypnutie celej ochrany |
| `input_boolean.export_optimizer_allow_battery_early_export` | Povolenie strategického exportu z batérie |
| `input_number.export_optimizer_min_reserve_soc` | Minimálna rezerva batérie, ktorú nechcete vybiť |
| `input_number.export_optimizer_consumption_margin_kwh` | Bezpečnostná rezerva pre odhad spotreby |
| `input_number.export_optimizer_export_surplus_threshold_kwh` | Minimálny prebytok, od ktorého sa oplatí zasiahnuť |
| `input_number.export_optimizer_min_export_power_w` | Spodný limit riadeného exportu |
| `input_number.export_optimizer_max_export_power_w` | Horný limit riadeného exportu a limit pri plnej batérii |
| `input_number.export_optimizer_price_floor` | Cena, od ktorej sa ešte považuje export za bezpečný |

## Odporúčané úvodné nastavenie

Na začiatok odporúčam opatrné hodnoty:

| Nastavenie | Odporúčaná hodnota |
|---|---:|
| Minimálna rezerva batérie | `40 %` |
| Rezerva odhadu spotreby | `2 kWh` |
| Minimálny očakávaný prebytok | `1 kWh` |
| Minimálny riadený export | `500 W` |
| Maximálny riadený export | `3000 W` |
| Minimálna spotová cena pre export | `0 EUR/MWh` |

Po niekoľkých slnečných dňoch sledujte správanie a hodnoty upravte.

## Režim bez skorého exportu z batérie

Ak vypnete:

```text
Export Optimizér - povoliť skorý export z batérie
```

automatizácia sa pokúsi obmedziť export z batérie a nastaví export približne podľa aktuálneho PV prebytku:

```text
PV výkon - spotreba domu - 200 W
```

Tento režim môže byť vhodný, ak chcete šetriť batériu a nechcete ju zbytočne cyklovať. Na druhej strane môže byť menej účinný pri príprave na dlhé alebo silné záporné cenové okno.

## Čo sledovať po spustení

Tieto entity sú najdôležitejšie pri ladení:

| Entita | Čo znamená |
|---|---|
| `sensor.export_optimizer_okte_spotova_cena` | Aktuálna spotová cena vypočítaná z OKTE atribútov |
| `sensor.export_optimizer_negative_price_minutes_until_17` | Koľko minút záporných cien ešte zostáva do 17:00 |
| `sensor.export_optimizer_recommended_export_power` | Odporúčaný výkon strategického exportu |
| `binary_sensor.export_optimizer_export_wanted` | Či má automatizácia prepnúť do `Export First` |
| `input_boolean.export_optimizer_export_guard_active` | Či automatizácia práve riadi export |
| `sensor.export_optimizer_expected_surplus_today` | Odhadovaný prebytok energie do konca solárneho okna |
| `sensor.export_optimizer_battery_target_soc` | Cieľová hranica SOC podľa odhadu spotreby a výroby |
| `sensor.export_optimizer_exported_energy_by_automation` | Energia exportovaná automatizáciou |
| `sensor.export_optimizer_exported_energy_during_negative_spot_price` | Energia exportovaná počas záporných cien |
| `sensor.export_optimizer_automation_export_savings` | Odhad zachránenej hodnoty |
| `sensor.export_optimizer_negative_price_wasted_potential` | Odhad stratenej hodnoty pri záporných cenách |

## Screenshoty na doplnenie

Tu sú miesta, kde sa oplatí neskôr doplniť reálne screenshoty z Home Assistant.

### 1. Denný graf výroby, spotreby, batérie a siete

<!-- TODO: Sem doplniť screenshot grafu, kde vidno PV výrobu, spotrebu domu, tok do siete a tok z/do batérie počas dňa so zápornými cenami. -->

Tento obrázok by mal ukázať, že energia bola exportovaná pred záporným cenovým oknom a počas záporných cien sa viac ukladala do batérie.

### 2. Detail OKTE cien a záporného cenového okna

<!-- TODO: Sem doplniť screenshot OKTE cien alebo graf spotovej ceny s vyznačeným záporným obdobím. -->

Tento obrázok pomôže vysvetliť, prečo automatizácia začala exportovať ešte pred obedom alebo pred záporným obdobím.

### 3. Stav pomocných senzorov automatizácie

<!-- TODO: Sem doplniť screenshot dashboardu s entitami export_optimizer_recommended_export_power, export_optimizer_export_wanted, export_optimizer_expected_surplus_today a export_optimizer_negative_price_minutes_until_17. -->

Tento obrázok by mal ukázať rozhodovaciu logiku automatizácie v čase, keď sa pripravuje na záporné ceny.

### 4. Úspora a stratený potenciál

<!-- TODO: Sem doplniť screenshot grafu kumulatívnej úspory a strateneho potenciálu. -->

Tento obrázok môže ukázať, či je automatizácia dobre naladená. Ideálne by úspora mala časom rásť a stratený potenciál by mal byť čo najnižší.

## Časté problémy

### Spotová cena nesedí s aktuálnym časom

Používajte `sensor.export_optimizer_okte_spotova_cena`, nie priamo stav OKTE senzora. Tento senzor počíta cenu z atribútu `prices` a berie do úvahy časové pásmo.

### Home Assistant má vysoké CPU využitie

Skontrolujte, či ste nepresunuli výpočty s `now()` do bežných template senzorov bez triggerov. Tento balík používa trigger-based template senzory zámerne, aby sa neprepočítavali príliš často.

### Menič neprepína režim

Skontrolujte, či možnosti v `select.inverter_work_mode` presne zodpovedajú textom:

```text
Export First
Zero Export To CT
```

Ak má váš menič iné názvy režimov, upravte ich v automatizácii.

### Hodnoty výkonu sú nesprávne

Balík predpokladá, že tieto entity sú vo wattoch:

```text
sensor.inverter_pv_power
sensor.inverter_load_power
number.inverter_export_surplus_power
```

Ak váš menič používa kW, budete musieť upraviť prepočty.

### Batéria sa vybíja viac, ako chcete

Zvýšte:

```text
input_number.export_optimizer_min_reserve_soc
```

alebo vypnite:

```text
input_boolean.export_optimizer_allow_battery_early_export
```

## Bezpečnostné poznámky

- Najprv testujte s nízkym maximálnym exportným výkonom.
- Overte, že váš menič naozaj chápe `Export First` a `Zero Export To CT` tak, ako očakávate.
- Skontrolujte, či zmena `number.inverter_export_surplus_power` nemá vedľajšie účinky aj v iných režimoch meniča.
- Tento projekt nie je finančné, právne ani elektrotechnické odporúčanie.
- Používate ho na vlastnú zodpovednosť.

## Stav projektu

Projekt je zatiaľ praktický Home Assistant package, nie HACS integrácia. Je určený na jednoduché kopírovanie, úpravu a ladenie podľa vlastnej inštalácie.

Návrhy, opravy a skúsenosti z reálnych inštalácií sú vítané.
