# Podrobný návod na nastavenie

Tento návod vás prevedie inštaláciou a ladením balíka na ochranu exportu počas záporných spotových cien v Home Assistant.

Hlavný README obsahuje kratšiu verziu. Tento súbor je zámerne podrobnejší a je určený najmä na prvé nasadenie alebo na prispôsobenie balíka inému meniču.

## 1. Skontrolujte požadované integrácie

Pred kopírovaním balíka sa uistite, že potrebné integrácie už fungujú.

### OKTE ceny

Odporúčaná integrácia:

- [OKTE DAM](https://github.com/rgildein/okte-home-assistant)

Balík očakáva entitu s OKTE cenami, napríklad:

```yaml
sensor.okte_ceny_elektriny_prices
```

Táto entita musí mať atribút `prices`, ktorý obsahuje 15-minútové obdobia s časmi a cenami.

Balík sa nespolieha iba na stav OKTE senzora, pretože ten sa v niektorých inštaláciách môže aktualizovať neskôr ako reálna 15-minútová hranica ceny. Namiesto toho počíta aktuálnu cenu z atribútu `prices`.

### Solcast predpoveď výroby

Odporúčaná integrácia:

- [Solcast Solar](https://github.com/BJReplay/ha-solcast-solar)

Balík očakáva dennú predpoveď, napríklad:

```yaml
sensor.solcast_pv_forecast_predpoved_dnes
```

Entita by mala mať atribút `detailedForecast`. Balík ho používa na odhad výroby pred najbližším záporným cenovým oknom a počas neho.

### Integrácia meniča

Balík vznikol okolo entít typu Deye/Solarman.

Odporúčaná Solarman integrácia:

- [ha-solarman](https://github.com/davidrapan/ha-solarman)

Home Assistant musí vedieť minimálne:

- čítať SOC batérie,
- čítať aktuálny PV výkon,
- čítať aktuálnu spotrebu domu,
- čítať dennú PV výrobu,
- čítať dennú spotrebu domu,
- čítať celkový export do siete,
- meniť režim meniča,
- nastavovať limit exportu do siete.

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

Balík štandardne očakáva tohto pomocníka:

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

Ak používate inú entitu pomocníka, po inštalácii zmeňte `input_text.export_optimizer_entity_energy_value_helper`.

## 4. Namapujte svoje entity

Balík drží všetky externé entity v jednej konfiguračnej sekcii na začiatku súboru `negative_price_export_guard.yaml`.

Nájdite blok `input_text:` a upravte tieto hodnoty, ak sa vaše entity volajú inak:

| Mapovací pomocník | Predvolená hodnota |
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

Tieto hodnoty môžete zmeniť priamo v YAML pred prvou inštaláciou alebo neskôr v Home Assistant ako textových pomocníkov. Je to zvyčajne jednoduchšie než hľadať entity v celom package súbore.

## 5. Skontrolujte jednotky

Toto je dôležité.

Balík predpokladá:

| Mapovací pomocník | Očakávaná jednotka odkazovanej entity |
|---|---|
| `input_text.export_optimizer_entity_pv_power` | W |
| `input_text.export_optimizer_entity_load_power` | W |
| `input_text.export_optimizer_entity_export_surplus_power` | W |
| `input_text.export_optimizer_entity_today_load_consumption` | kWh |
| `input_text.export_optimizer_entity_today_production` | kWh |
| `input_text.export_optimizer_entity_total_energy_export` | kWh |
| `input_text.export_optimizer_entity_battery_soc` | % |
| `input_text.export_optimizer_entity_battery_capacity` | kWh |

Ak váš menič poskytuje výkon v kW namiesto W, musíte upraviť výpočty používajúce PV výkon, spotrebu domu a exportný výkon.

## 6. Skontrolujte názvy režimov meniča

Balík štandardne očakáva tieto možnosti:

```text
Export First
Zero Export To CT
```

Skontrolujte ich vo Vývojárskych nástrojoch Home Assistant. Ak váš menič používa iné názvy možností, zmeňte:

```text
input_text.export_optimizer_mode_export_first
input_text.export_optimizer_mode_zero_export
```

## 7. Spustite kontrolu konfigurácie

V Home Assistant:

```text
Nastavenia -> Vývojárske nástroje -> YAML -> Skontrolovať konfiguráciu
```

Nereštartujte Home Assistant, kým kontrola neprejde.

Najčastejšie príčiny chyby sú:

- entity, ktoré neexistujú,
- duplicitné YAML kľúče po manuálnej úprave,
- nesprávne odsadenie,
- názvy režimov meniča, ktoré nesedia s vašou integráciou.

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
```

## 9. Správanie počas prvého dňa

Prvý deň ešte 7-dňový priemer spotreby v solárnom okne nemá históriu. Balík používa náhradnú hodnotu, kým nazbiera reálne vzorky.

Denná logika učenia zaznamená spotrebu domu o 07:00 a o 18:00 vyhodnotí spotrebu za okno 07:00-18:00.

Odhad by sa mal zlepšiť po niekoľkých dňoch.

## 10. Odporúčané úvodné ladenie

Začnite konzervatívne:

| Pomocník | Odporúčaná hodnota |
|---|---:|
| `input_number.export_optimizer_min_reserve_soc` | `40` |
| `input_number.export_optimizer_consumption_margin_kwh` | `2` |
| `input_number.export_optimizer_export_surplus_threshold_kwh` | `1` |
| `input_number.export_optimizer_min_export_power_w` | `500` |
| `input_number.export_optimizer_max_export_power_w` | `3000` |
| `input_number.export_optimizer_price_floor` | `0` |

Potom sledujte aspoň niekoľko slnečných dní so zápornými alebo veľmi nízkymi cenami.

## 11. Ako ladiť nastavenia

### Ak sa energia stále exportuje počas záporných cien

Zvýšte jednu alebo viac hodnôt:

```text
input_number.export_optimizer_max_export_power_w
input_number.export_optimizer_consumption_margin_kwh
input_number.export_optimizer_export_surplus_threshold_kwh
```

Skontrolujte aj to, či Solcast nepodhodnocuje výrobu.

### Ak sa batéria vybíja príliš veľa

Zvýšte:

```text
input_number.export_optimizer_min_reserve_soc
```

alebo vypnite:

```text
input_boolean.export_optimizer_allow_battery_early_export
```

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

## 12. Odporúčaný dashboard

Jednoduchý debug dashboard by mal obsahovať:

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

Takto je oveľa jednoduchšie vidieť, prečo automatizácia je alebo nie je aktívna.

## 13. Účtovné senzory

Balík vytvára kumulatívne senzory na sledovanie výsledkov:

| Entita | Význam |
|---|---|
| `sensor.export_optimizer_exported_energy_during_negative_spot_price` | kWh exportované počas záporných spotových cien |
| `sensor.export_optimizer_exported_energy_by_automation` | kWh exportované počas aktívneho riadenia automatizáciou |
| `sensor.export_optimizer_automation_export_savings` | Odhad hodnoty zachránenej automatizáciou |
| `sensor.export_optimizer_negative_price_wasted_potential` | Odhad hodnoty stratenej exportom počas záporných cien |

Tieto senzory sú kumulatívne. Na denné hodnoty použite grafy alebo štatistiky, ktoré počítajú denný rozdiel.

## 14. Poznámky k výkonu Home Assistant

Balík používa trigger-based template senzory zámerne.

Vyhnite sa tomu, aby ste tieto šablóny zmenili na bežné template senzory bez triggerov, ak obsahujú:

```text
now()
today_at()
state_attr(... prices ...)
state_attr(... detailedForecast ...)
```

Tieto funkcie a slučky môžu spôsobovať časté prepočítavanie šablón a vysoké CPU využitie na menších Home Assistant systémoch.

## 15. Bezpečnostný checklist

Predtým, než necháte automatizáciu bežať bez dozoru:

- Overte, že prepínanie režimu meniča funguje správne.
- Overte, že exportné limity sú primerané pre váš menič a pripojenie do siete.
- Overte, že záporné spotové ceny vracajú menič do `Zero Export To CT`.
- Overte, že `sensor.export_optimizer_okte_spotova_cena` zodpovedá reálnemu aktuálnemu OKTE obdobiu.
- Overte, že rezerva batérie je dostatočná pre vašu domácnosť.
- Začnite s nízkym maximálnym exportným výkonom a zvyšujte ho postupne.

## 16. Prispôsobenie iným krajinám alebo dodávateľom

Myšlienka nie je striktne slovenská, ale zdroj cien a pravidlá dodávateľa sú lokálne.

Pri použití inde upravte:

- namapovanú entitu so spotovými cenami,
- parsovanie atribútov cien, ak je iné,
- pomocníka pre výpočet hodnoty výkupu alebo virtuálnej batérie,
- názvy režimov meniča,
- koniec solárneho okna, ak je lokálna výroba posunutá.

Základná myšlienka ostáva rovnaká: vytvoriť miesto v batérii pred záporným cenovým oknom, vyhnúť sa strategickému exportu počas záporných cien a sledovať, či je nastavenie dobre naladené.
