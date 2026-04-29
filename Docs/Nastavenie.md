# Podrobný návod na nastavenie

Tento návod vás prevedie inštaláciou a ladením balíčka na ochranu exportu počas záporných spotových cien v Home Assistant. Hlavný README obsahuje kratšiu verziu; tento súbor je určený najmä na prvé nasadenie, prispôsobenie inému meniču a ladenie.

## 1. Skontrolujte požadované integrácie

### OKTE ceny

Odporúčaná integrácia:

- [OKTE DAM](https://github.com/rgildein/okte-home-assistant)

Balík očakáva entitu s OKTE cenami, napríklad:

```yaml
sensor.okte_ceny_elektriny_prices
```

Táto entita musí mať atribút `prices`, ktorý obsahuje 15-minútové obdobia s časmi a cenami. Balík počíta aktuálnu cenu z tohto atribútu, pretože stav senzora sa môže aktualizovať neskôr ako reálna 15-minútová hranica ceny.

### Solcast predpoveď výroby

Odporúčaná integrácia:

- [Solcast Solar](https://github.com/BJReplay/ha-solcast-solar)

Balík očakáva dennú predpoveď, napríklad:

```yaml
sensor.solcast_pv_forecast_predpoved_dnes
```

Entita by mala mať atribút `detailedForecast`. Balík ho používa na odhad výroby pred najbližším cenovým oknom pod nastavenou hranicou a počas neho.

### Integrácia meniča

Balík vznikol okolo entít typu Deye/Solarman.

Odporúčaná Solarman integrácia:

- [ha-solarman](https://github.com/davidrapan/ha-solarman)

Home Assistant musí vedieť minimálne čítať SOC batérie, PV výkon, spotrebu domu, dennú PV výrobu, dennú spotrebu domu, celkový export do siete a musí vedieť meniť režim meniča a nastavovať limit exportu do siete.

## 2. Povoľte Home Assistant packages

Ak ešte nepoužívate packages, pridajte do `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Potom vytvorte priečinok:

```text
config/packages
```

Do neho skopírujte package súbor:

```text
config/packages/negative_price_export_guard.yaml
```

## 3. Vytvorte pomocníka pre hodnotu energie

Balík očakáva tohto pomocníka:

```yaml
input_number.cena_elektriny_nocny_tarif
```

Vytvorte ho cez používateľské rozhranie Home Assistant:

```text
Nastavenia -> Zariadenia a služby -> Pomocníci -> Vytvoriť pomocníka -> Číslo
```

Odporúčané nastavenie:

| Pole | Hodnota |
|---|---|
| Názov | Cena elektriny nočný tarif |
| Minimum | `0` |
| Maximum | hodnota vyššia ako váš tarif, napríklad `1` |
| Krok | `0.001` |
| Jednotka | `EUR/kWh` |
| Režim | box |

Táto hodnota sa používa na odhad toho, akú hodnotu by exportovaná energia mala, keby sa započítala do virtuálnej batérie. Ak si nie ste istí, začnite približnou hodnotou vášho nočného tarifu v EUR/kWh.

## 4. Namapujte svoje entity

Otvorte `negative_price_export_guard.yaml` a skontrolujte každú entitu v časti očakávaných entít.

| Účel | Predvolená entita |
|---|---|
| OKTE ceny | `sensor.okte_ceny_elektriny_prices` |
| Solcast predpoveď dnes | `sensor.solcast_pv_forecast_predpoved_dnes` |
| Denná spotreba domu | `sensor.inverter_today_load_consumption` |
| Celkový export do siete | `sensor.inverter_total_energy_export` |
| Denná PV výroba | `sensor.inverter_today_production` |
| SOC batérie | `sensor.inverter_battery` |
| Kapacita batérie | `sensor.inverter_battery_capacity` |
| Aktuálny PV výkon | `sensor.inverter_pv_power` |
| Aktuálna spotreba domu | `sensor.inverter_load_power` |
| Výber režimu meniča | `select.inverter_work_mode` |
| Limit výkonu exportu | `number.inverter_export_surplus_power` |
| Pomocník hodnoty energie | `input_number.cena_elektriny_nocny_tarif` |

Ak sa vaše entity volajú inak, nahraďte všetky výskyty v package súbore. Nepokúšajte sa ukladať entity ID do `input_text` pomocníkov pre triggery; Home Assistant triggery potrebujú reálne entity ID priamo v YAML.

## 5. Skontrolujte jednotky

Balík predpokladá:

| Entita | Očakávaná jednotka |
|---|---|
| `sensor.inverter_pv_power` | W |
| `sensor.inverter_load_power` | W |
| `number.inverter_export_surplus_power` | W |
| `sensor.inverter_today_load_consumption` | kWh |
| `sensor.inverter_today_production` | kWh |
| `sensor.inverter_total_energy_export` | kWh |
| `sensor.inverter_battery` | % |
| `sensor.inverter_battery_capacity` | kWh |

Ak váš menič poskytuje výkon v kW namiesto W, musíte upraviť výpočty používajúce PV výkon, spotrebu domu a exportný výkon.

## 6. Skontrolujte názvy režimov meniča

Balík očakáva tieto presné možnosti v `select.inverter_work_mode`:

```text
Export First
Zero Export To CT
```

Skontrolujte ich vo Vývojárskych nástrojoch Home Assistant. Ak váš menič používa iné názvy možností, upravte akcie automatizácie.

## 7. Spustite kontrolu konfigurácie

V Home Assistant:

```text
Nastavenia -> Vývojárske nástroje -> YAML -> Skontrolovať konfiguráciu
```

Nereštartujte Home Assistant, kým kontrola neprejde. Najčastejšie príčiny chyby sú nesprávne entity ID, duplicitné YAML kľúče, nesprávne odsadenie, neplatné voľby pod YAML helpermi a názvy režimov meniča, ktoré nesedia s vašou integráciou.

## 8. Reštartujte a skontrolujte nové entity

Po reštarte vyhľadajte entity začínajúce na:

```text
export_optimizer_
```

Najdôležitejšie sú:

```text
sensor.export_optimizer_okte_spotova_cena
sensor.export_optimizer_recommended_export_power
binary_sensor.export_optimizer_export_wanted
input_boolean.export_optimizer_export_guard_enabled
input_boolean.export_optimizer_allow_battery_early_export
input_boolean.export_optimizer_export_guard_active
input_number.export_optimizer_typical_idle_power_w
```

## 9. Správanie počas prvého dňa a učenie

Balík zaznamená stav počítadla spotreby domu o 07:00 a o 18:00 vyhodnotí spotrebu za okno 07:00-18:00. Senzor `sensor.export_optimizer_solar_window_load_7d_average` ukladá posledných sedem denných vzoriek do atribútu `past_consumption` a používa ich na výpočet priemeru.

Prvý deň má priemer málo alebo žiadnu históriu. Odhad by sa mal zlepšiť po niekoľkých slnečných dňoch.

## 10. Odporúčané úvodné ladenie

Začnite konzervatívne:

| Pomocník | Odporúčaná hodnota |
|---|---:|
| `input_number.export_optimizer_min_reserve_soc` | `40` |
| `input_number.export_optimizer_consumption_margin_kwh` | `2` |
| `input_number.export_optimizer_typical_idle_power_w` | `200-500` |
| `input_number.export_optimizer_export_surplus_threshold_kwh` | `1` |
| `input_number.export_optimizer_min_export_power_w` | `500` |
| `input_number.export_optimizer_max_export_power_w` | `3000` |
| `input_number.export_optimizer_price_floor` | `0` |

Typická minimálna spotreba by mala zahŕňať bežnú minimálnu spotrebu domu a vlastnú spotrebu meniča počas zvyšku solárneho okna. Zabraňuje tomu, aby odhad zostávajúcej spotreby klesol nereálne na nulu príliš skoro počas dňa.

## 11. Režim šetrenia batérie

Ak vypnete:

```text
input_boolean.export_optimizer_allow_battery_early_export
```

odporúčaný výkon exportu sa obmedzí na aktuálny živý PV prebytok:

```text
PV výkon - spotreba domu - 200 W
```

Tým sa zníži cyklovanie batérie, ale nemusí sa vytvoriť dosť miesta pred dlhým alebo silným záporným cenovým obdobím.

## 12. Ako ladiť nastavenia

### Ak sa energia stále exportuje počas záporných cien

Skúste postupne:

- Zvýšiť `input_number.export_optimizer_max_export_power_w`, ak to váš menič a pripojenie povoľujú.
- Zvýšiť `input_number.export_optimizer_export_surplus_threshold_kwh`, ak chcete vytvoriť väčšiu rezervu pred záporným oknom.
- Zapnúť `input_boolean.export_optimizer_allow_battery_early_export`, ak je režim šetrenia batérie príliš obmedzujúci.
- Skontrolovať, či Solcast nepodhodnocuje výrobu alebo či entity kapacity/SOC batérie nie sú nepresné.

Nezvyšujte automaticky `input_number.export_optimizer_consumption_margin_kwh`: vyššia rezerva spotreby hovorí algoritmu, že očakáva viac lokálnej spotreby, čo môže znížiť skorý export.

### Ak sa batéria vybíja príliš veľa

Zvýšte:

```text
input_number.export_optimizer_min_reserve_soc
```

alebo vypnite:

```text
input_boolean.export_optimizer_allow_battery_early_export
```

### Ak odhad zostávajúcej spotreby klesá príliš nízko

Zvýšte:

```text
input_number.export_optimizer_typical_idle_power_w
```

Je to užitočné vtedy, keď naučená denná spotreba už bola väčšinou spotrebovaná, ale dom má stále predvídateľnú základnú spotrebu až do 18:00.

### Ak sa automatizácia spúšťa príliš často

Zvýšte:

```text
input_number.export_optimizer_export_surplus_threshold_kwh
```

Automatizácia potom bude ignorovať menšie očakávané prebytky.

### Ak sa PV výkon obmedzuje pri plnej batérii

Zvýšte:

```text
input_number.export_optimizer_max_export_power_w
```

Automatizácia obsahuje logiku, ktorá pri plnej batérii a režime `Zero Export To CT` nastaví exportný limit na maximálnu hodnotu, pokiaľ spotová cena nie je záporná.

## 13. Odporúčaný dashboard

Jednoduchý debug dashboard by mal obsahovať:

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

Takto je oveľa jednoduchšie vidieť, prečo automatizácia je alebo nie je aktívna.

## 14. Účtovné senzory

Balík vytvára kumulatívne senzory na sledovanie výsledkov:

| Entita | Význam |
|---|---|
| `sensor.export_optimizer_exported_energy_during_negative_spot_price` | kWh exportované počas záporných spotových cien |
| `sensor.export_optimizer_exported_energy_by_automation` | kWh exportované počas aktívneho riadenia automatizáciou |
| `sensor.export_optimizer_automation_export_savings` | Odhad hodnoty zachránenej automatizáciou |
| `sensor.export_optimizer_negative_price_wasted_potential` | Odhad hodnoty stratenej exportom počas záporných cien |

Tieto senzory sú kumulatívne. Na denné hodnoty použite grafy alebo štatistiky, ktoré počítajú denný rozdiel.

## 15. Poznámky k výkonu Home Assistant

Balík používa trigger-based template senzory zámerne. Vyhnite sa tomu, aby ste tieto šablóny zmenili na bežné template senzory bez triggerov, ak obsahujú:

```text
now()
today_at()
state_attr(... prices ...)
state_attr(... detailedForecast ...)
```

Tieto funkcie a slučky môžu spôsobovať časté prepočítavanie šablón a vysoké CPU využitie na menších Home Assistant systémoch.

## 16. Bezpečnostný checklist

Predtým, než necháte automatizáciu bežať bez dozoru:

- Overte, že prepínanie režimu meniča funguje správne.
- Overte, že exportné limity sú primerané pre váš menič a pripojenie do siete.
- Overte, že záporné spotové ceny vracajú menič do `Zero Export To CT`.
- Overte, že `sensor.export_optimizer_okte_spotova_cena` zodpovedá reálnemu aktuálnemu OKTE obdobiu.
- Overte, že rezerva batérie je dostatočná pre vašu domácnosť.
- Začnite s nízkym maximálnym exportným výkonom a zvyšujte ho postupne.

## 17. Prispôsobenie iným krajinám alebo dodávateľom

Myšlienka nie je striktne slovenská, ale zdroj cien a pravidlá dodávateľa sú lokálne. Pri použití inde bude treba nahradiť entitu so spotovými cenami, parsovanie cien, výpočet hodnoty energie, názvy režimov meniča a prípadne solárne okno.

Základná myšlienka ostáva rovnaká: vytvoriť miesto v batérii pred záporným cenovým oknom, vyhnúť sa strategickému exportu počas záporných cien a sledovať, či je nastavenie dobre naladené.
