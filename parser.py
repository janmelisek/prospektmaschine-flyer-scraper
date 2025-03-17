import requests
from bs4 import BeautifulSoup
import json
import logging
import time
from datetime import datetime
import re
from typing import List, Dict

# Zakladne nastavenia
BASE_URL: str = "https://www.prospektmaschine.de"
SHOP_CATEGORY: str = "/hypermarkte"  # mozno zmenit na inu kategoriu
LOG_FILE: str = "scraper.log"
TIMEOUT: int = 10  # Timeout pre HTTP poziadavky v sekundach
INCLUDE_FUTURE: bool = True  # ak True povazujeme letaky ktore este nezacali za platne

# Nastavenie logovania
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def log_info(message: str) -> None:
    """
    Zapise informacnu spravu do logovacieho suboru.

    :param message: Text spravy, ktory sa ma zapisat.
    """
    logging.info(message)


def log_error(message: str) -> None:
    """
    Zapise chybovu spravu do logovacieho suboru.

    :param message: Text chybovej spravy, ktory sa ma zapisat.
    """
    logging.error(message)


class Flyer:
    """
    Trieda reprezentujuca letak.
    """

    def __init__(self, title: str, thumbnail: str, shop_name: str,
                 valid_from: str, valid_to: str, url: str) -> None:
        """
        Inicializacia instancie letaku.

        :param title: Nazov letaku.
        :param thumbnail: URL obrazka letaku.
        :param shop_name: Nazov obchodu, ku ktoremu letak patri.
        :param valid_from: Datum platnosti od vo formate YYYY-MM-DD.
        :param valid_to: Datum platnosti do vo formate YYYY-MM-DD.
        :param url: URL letaku.
        """
        self.title: str = title
        self.thumbnail: str = thumbnail
        self.shop_name: str = shop_name
        self.valid_from: str = valid_from
        self.valid_to: str = valid_to
        self.parsed_time: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.url: str = url

    def to_dict(self) -> Dict[str, str]:
        """
        Prevedie instanciu letaku do slovnika.

        :return: Slovnik s atributmi letaku.
        """
        return self.__dict__


class FlyerScraper:
    """
    Trieda implementujuca scraper pre letaky.
    """

    def __init__(self, base_url: str) -> None:
        """
        Inicializacia instancie scraperu.

        :param base_url: Zakladna URL adresa.
        """
        self.base_url: str = base_url
        self.shops: List[Dict[str, str]] = []
        self.flyers: List[Flyer] = []
        self.session: requests.Session = requests.Session()
        # Nastavenie vlastneho User-Agent
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; FlyerScraper/1.0)"
        })

    def get_shops(self) -> List[Dict[str, str]]:
        """
        Ziska zoznam obchodov z webovej stranky.

        :return: List slovnikov, kazdy obsahuje 'name' a 'url' obchodu.
        """
        url = self.base_url + SHOP_CATEGORY
        try:
            response = self.session.get(url, timeout=TIMEOUT)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            log_error(f"Chyba pri nacitani obchodov z {url}: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        shop_list: List[Dict[str, str]] = []

        # Najdenie kontajnera s obchodmi
        shop_container = soup.find("ul", class_="list-unstyled categories")
        if not shop_container:
            log_error("Chyba: Nenasiel sa kontajner s obchodmi!")
            return []

        # Prejdenie cez vsetky <li> elementy a ziskanie odkazu
        for shop in shop_container.find_all("li"):
            link = shop.find("a")
            if link and link.get("href"):
                shop_list.append({
                    "name": link.text.strip(),
                    "url": self.base_url + link["href"]
                })

        log_info(f"Najdenych {len(shop_list)} obchodov")
        return shop_list

    def clean_date(self, date_text: str) -> str:
        """
        Preformatuje datum z formatu dd.mm.yyyy na YYYY-MM-DD.

        :param date_text: Retazec obsahujuci datum vo formate dd.mm.yyyy.
        :return: Datum vo formate YYYY-MM-DD alebo prazdny retazec pri chybe.
        """
        match = re.search(r'(\d{2}\.\d{2}\.\d{4})', date_text)
        if match:
            try:
                # Prevod retazca na datetime objekt a formatovanie
                return datetime.strptime(match.group(1), "%d.%m.%Y").strftime("%Y-%m-%d")
            except ValueError as e:
                log_error(f"Chyba pri spracovani datumu '{date_text}': {e}")
                return ""
        return ""

    def parse_flyers(self, shop: Dict[str, str]) -> List[Flyer]:
        """
        Spracuje letaky pre dany obchod.

        :param shop: Slovnik obsahujuci 'name' a 'url' obchodu.
        :return: List instancii triedy Flyer.
        """
        log_info(f"Spracuvavam obchod: {shop['name']} - {shop['url']}")
        try:
            response = self.session.get(shop["url"], timeout=TIMEOUT)
            if response.status_code != 200:
                log_error(
                    f"Chyba pri nacitani {shop['url']}: {response.status_code}")
                return []

            soup = BeautifulSoup(response.text, "html.parser")
            flyers: List[Flyer] = []

            # Najdenie kontajnera s letakmi
            flyer_grid = soup.find("div", class_="letaky-grid")
            if not flyer_grid:
                log_info(f"Ziaden letak pre obchod {shop['name']}")
                return []

            today_date = datetime.today().date()
            seen_flyers = set()

            # Prejdenie vsetkych letakov
            for flyer in flyer_grid.find_all("div", class_="brochure-thumb"):
                # Preskocime stare letaky ("zatmavnutie")
                flyer_container = flyer.find("div", class_="grid-item")
                if flyer_container and "grid-item-old" in flyer_container.get("class", []):
                    continue

                title = flyer.find("strong").text.strip(
                ) if flyer.find("strong") else "Neznamy"
                date_text = flyer.find(
                    "small", class_="hidden-sm").text.strip() if flyer.find("small", class_="hidden-sm") else ""

                img_tag = flyer.find("img")
                img_url = img_tag.get("src") or img_tag.get(
                    "data-src") or img_tag.get("data-lazy") or ""

                link_tag = flyer.find("a")
                flyer_url = self.base_url + \
                    link_tag["href"] if link_tag and "href" in link_tag.attrs else ""

                try:
                    # Rozdelenie datumoveho textu na zaciatok a koniec platnosti
                    date_parts = date_text.split(" - ")
                    valid_from_str = self.clean_date(
                        date_parts[0]) if date_parts else ""
                    valid_to_str = self.clean_date(
                        date_parts[1]) if len(date_parts) > 1 else ""
                    if not valid_from_str:
                        log_error(
                            f"Neplatny datum pre letak '{title}' v obchode {shop['name']}")
                        continue

                    valid_from_date = datetime.strptime(
                        valid_from_str, "%Y-%m-%d").date()
                    if valid_to_str:
                        valid_to_date = datetime.strptime(
                            valid_to_str, "%Y-%m-%d").date()
                    else:
                        valid_to_date = None

                    flyer_id = f"{shop['name']}_{title}_{valid_from_str}_{valid_to_str}"
                    if valid_to_date:
                        if INCLUDE_FUTURE:
                            if today_date <= valid_to_date:
                                seen_flyers.add(flyer_id)
                                flyers.append(
                                    Flyer(title, img_url, shop["name"], valid_from_str, valid_to_str, flyer_url))
                            else:
                                log_info(
                                    f"Leták '{title}' v obchode {shop['name']} presiahol dátum platnosti ({valid_from_date} - {valid_to_date}).")
                        else:
                            if valid_from_date <= today_date <= valid_to_date:
                                seen_flyers.add(flyer_id)
                                flyers.append(
                                    Flyer(title, img_url, shop["name"], valid_from_str, valid_to_str, flyer_url))
                            else:
                                log_info(
                                    f"Leták '{title}' v obchode {shop['name']} nie je aktuálny! (platnosť {valid_from_date} - {valid_to_date})")
                    elif valid_from_date:
                        if INCLUDE_FUTURE or valid_from_date <= today_date:
                            seen_flyers.add(flyer_id)
                            flyers.append(
                                Flyer(title, img_url, shop["name"], valid_from_str, "", flyer_url))
                        else:
                            log_info(
                                f"Leták '{title}' v obchode {shop['name']} ešte nie je platný! (platnosť od {valid_from_date})")
                except Exception as e:
                    log_error(
                        f"Chyba pri spracovani datumu pre '{title}' v obchode {shop['name']}: {e}")
            log_info(
                f"Extrahovanych {len(flyers)} letakov pre obchod {shop['name']}")
            return flyers
        except Exception as e:
            log_error(f"Chyba pri spracovani obchodu {shop['name']}: {e}")
            return []

    def run(self) -> None:
        """
        Hlavna metoda, ktora spaja vsetky kroky scraperu.
        Ziska obchody, spracuje letaky a vysledok ulozi do suboru flyers.json.
        """
        start_time = time.time()
        self.shops = self.get_shops()

        for shop in self.shops:
            self.flyers.extend(self.parse_flyers(shop))

        # Ulozenie letakov do JSON suboru
        with open("flyers.json", "w", encoding="utf-8") as f:
            json.dump([flyer.to_dict() for flyer in self.flyers],
                      f, ensure_ascii=False, indent=4)

        duration = time.time() - start_time
        print(
            f"Spracovanych {len(self.flyers)} letakov v {len(self.shops)} obchodoch za {duration:.2f} sekund")
        log_info(
            f"Skript ukonceny: Spracovanych {len(self.flyers)} letakov v {len(self.shops)} obchodoch za {duration:.2f} sekund")


if __name__ == "__main__":
    # Vytvorenie instancie a spustenie scraperu
    scraper = FlyerScraper(BASE_URL)
    scraper.run()
