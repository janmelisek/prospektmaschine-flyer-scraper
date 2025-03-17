# Prospektmaschine Flyer Scraper

Tento projekt je jednoduchý web scraper napísaný v Pythone, ktorý získava letáky zo stránky [prospektmaschine.de](https://www.prospektmaschine.de). Program načíta zoznam obchodov a pre každý obchod extrahuje letáky spolu s údajmi, ako je názov, obrázok, dátumy platnosti, názov obchodu a URL. Výsledné údaje sú uložené vo formáte JSON v súbore `flyers.json`.

## Funkcie
- **Načítanie obchodov:** Získa zoznam obchodov z podstránky `/hypermarkte/`.
- **Extrahovanie letákov:** Pre každý obchod skript extrahuje aktuálne letáky, pričom overuje ich platnosť a zahŕňa aj budúce letáky, ak je to povolené.
- **Logovanie:** Všetky dôležité akcie a chyby sú logované do súboru `scraper.log`.

## Konfiguračné premenné

Na začiatku skriptu nájdete niekoľko premenných, ktoré je možné upraviť podľa potrieb projektu:

- **BASE_URL**: Základná URL adresa, z ktorej sa načítavajú dáta.(default: [prospektmaschine.de](https://www.prospektmaschine.de))
- **SHOP_CATEGORY**: Nastavenie podstránky(default: /hypermarkte)
- **LOG_FILE**: Súbor, do ktorého sa ukladajú logovacie záznamy.(default: scraper.log)
- **TIMEOUT**: Timeout pre HTTP požiadavky (v sekundách).(default: 10)
- **INCLUDE_FUTURE**: Ak je nastavené na `True`, skript zobrazí aj letáky, ktoré zatiaľ neplatia, ale budú platné v budúcnosti.(default: True)

## Požiadavky
- Python 3.6+
- Knižnice:
  - `requests`
  - `beautifulsoup4`

## Inštalácia
1. Naklonujte repozitár:
    ```bash
    git clone https://github.com/janmelisek/prospektmaschine-flyer-scraper.git
    cd prospektmaschine-flyer-scraper
    ```
2. Vytvorte virtuálne prostredie (voliteľné):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Pre Unix systémy
    .\venv\Scripts\activate   # Pre Windows
    ```
3. Inštalujte potrebné knižnice:
    ```bash
    pip install requests beautifulsoup4
    ```
## Použitie
Spustite skript:
```bash
python parser.py
