import concurrent.futures
import logging
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import psutil
import requests
from bs4 import BeautifulSoup, Tag
from dotenv import load_dotenv
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

ALLOCINE_EMAIL: str = os.environ.get("ALLOCINE_EMAIL", "")
ALLOCINE_PASSWORD: str = os.environ.get("ALLOCINE_PASSWORD", "")

OUTPUT_DIR = Path("output")
DEBUG_PORT = 9222
BASE_URL = "https://www.allocine.fr"
LOAD_MORE_SELECTOR = (
    "button.button.button-default-full.button-md.load-more-button"
)
THUMBNAIL_SELECTOR = "figure.thumbnail"
MAX_WORKERS = 10
REQUEST_TIMEOUT = 15

KNOWN_PLATFORMS: dict[str, str] = {
    "netflix": "Netflix",
    "prime video": "Amazon Prime Video",
    "amazon prime": "Amazon Prime Video",
    "disney+": "Disney+",
    "disney +": "Disney+",
    "canal+": "Canal+",
    "canal +": "Canal+",
    "canal vod": "Canal VOD",
    "apple tv": "Apple TV+",
    "ocs": "OCS",
    "paramount+": "Paramount+",
    "paramount +": "Paramount+",
    "mycanal": "MyCanal",
}

logger = logging.getLogger(__name__)


class AllocineScraper:
    @staticmethod
    def _make_silent_service() -> Service:
        """Crée un Service Chrome avec les logs supprimés."""
        return Service(log_output=subprocess.DEVNULL)

    @staticmethod
    def _make_silent_options() -> webdriver.ChromeOptions:
        """Crée des ChromeOptions silencieuses (sans logs internes Chrome)."""
        options = webdriver.ChromeOptions()
        options.page_load_strategy = "eager"
        options.add_argument("--log-level=3")
        options.add_argument("--silent")
        options.add_argument("--disable-logging")
        options.add_experimental_option(
            "excludeSwitches", ["enable-logging"]
        )
        return options

    def __init__(self) -> None:
        try:
            options = self._make_silent_options()
            options.add_experimental_option(
                "debuggerAddress",
                f"127.0.0.1:{DEBUG_PORT}",
            )
            self.driver = webdriver.Chrome(
                service=self._make_silent_service(), options=options
            )
            logger.info("Connexion à la session Chrome existante")
        except Exception:
            logger.info("Démarrage d'une nouvelle session Chrome...")
            options = self._make_silent_options()
            options.add_argument("--start-maximized")
            options.add_argument("--disable-notifications")
            options.add_argument(f"--remote-debugging-port={DEBUG_PORT}")
            options.add_experimental_option("detach", True)
            self.driver = webdriver.Chrome(
                service=self._make_silent_service(), options=options
            )

        self.wait = WebDriverWait(self.driver, 10)

    def login(self, email: str, password: str) -> bool:
        """Connexion à Allociné.

        Args:
            email: Adresse email du compte Allociné.
            password: Mot de passe du compte Allociné.

        Returns:
            True si la connexion a réussi, False sinon.
        """
        try:
            logger.info("Connexion à Allociné...")
            self.driver.get("https://mon.allocine.fr/connexion")
            time.sleep(3)

            # Accepter les cookies
            try:
                logger.debug("Recherche du bouton de cookies...")
                cookie_button = self.wait.until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR,
                        "button.didomi-components-button--primary",
                    ))
                )
                time.sleep(1)
                self.driver.execute_script(
                    "arguments[0].click();", cookie_button
                )
                logger.info("Cookies acceptés")
                time.sleep(3)
            except Exception as exc:
                logger.warning("Acceptation des cookies échouée : %s", exc)
                # Tenter de fermer l'overlay via JS si le bouton est bloqué
                try:
                    self.driver.execute_script(
                        "document.querySelector('.didomi-popup-container')"
                        "?.remove();"
                    )
                except Exception:
                    pass

            self.driver.get("https://mon.allocine.fr/connexion/")
            time.sleep(3)

            if "connexion" not in self.driver.current_url.lower():
                logger.info("Déjà connecté")
                return True

            logger.debug("Remplissage du formulaire de connexion...")
            try:
                email_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "email"))
                )
            except Exception as exc:
                logger.error("Champ email introuvable : %s", exc)
                return False

            for char in email:
                email_field.send_keys(char)
                time.sleep(0.1)

            time.sleep(1)

            try:
                password_field = self.driver.find_element(
                    By.NAME, "password"
                )
            except Exception as exc:
                logger.error("Champ mot de passe introuvable : %s", exc)
                return False

            for char in password:
                password_field.send_keys(char)
                time.sleep(0.1)

            time.sleep(2)

            try:
                submit_button = self.driver.find_element(
                    By.CSS_SELECTOR, "button[type='submit']"
                )
            except Exception as exc:
                logger.error("Bouton de soumission introuvable : %s", exc)
                return False

            self.driver.execute_script(
                "arguments[0].click();", submit_button
            )
            logger.debug("Formulaire soumis")

            # Attendre la redirection post-login (max 10s)
            try:
                self.wait.until(
                    lambda d: "connexion"
                    not in d.current_url.lower()
                )
                logger.info("Connexion réussie")
                return True
            except Exception:
                logger.error("La connexion semble avoir échoué")
                return False

        except Exception as exc:
            logger.error("Erreur lors de la connexion : %s", exc)
            return False

    def _get_total_films_count(
        self, url: str, href_pattern: str = "vus"
    ) -> int:
        """Récupère le nombre total de films depuis le menu de navigation.

        Args:
            url: URL de la page de liste.
            href_pattern: Motif de l'href à chercher dans le menu
                (ex: "vus", "envie-de-voir").

        Returns:
            Nombre total de films, ou 0 si non trouvé.
        """
        try:
            self.driver.get(url)
            time.sleep(3)

            # Plusieurs sélecteurs possibles selon la version d'Allociné
            selectors = [
                f'a.userspace-submenu-item[href*="{href_pattern}"]',
                f'a[href*="{href_pattern}"].submenu-item',
                f'nav a[href*="{href_pattern}"]',
                f'a[href*="{href_pattern}"]',
            ]

            count_text: Optional[str] = None
            for selector in selectors:
                try:
                    elem = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, selector)
                        )
                    )
                    count_text = elem.text
                    logger.debug(
                        "Compteur trouvé via '%s' : %s",
                        selector,
                        count_text,
                    )
                    break
                except Exception:
                    continue

            if count_text:
                match = re.search(r"\((\d+)\)", count_text)
                if match:
                    total_films = int(match.group(1))
                    logger.info(
                        "Nombre total de films : %d", total_films
                    )
                    return total_films

            # Compteur introuvable → renvoyer 0 = "charger tout jusqu'au bout"
            logger.warning(
                "Compteur de films introuvable via tous les sélecteurs. "
                "Mode 'charger tout' activé (clic jusqu'à disparition du "
                "bouton 'Voir plus')."
            )
            return 0
        except Exception as exc:
            logger.error(
                "Erreur lors de la récupération du nombre total : %s", exc
            )
            return 0

    def _load_all_films(self, total_films: int) -> None:
        """Charge tous les films en cliquant sur 'Voir plus'.

        Args:
            total_films: Nombre total de films à charger (0 = charger tout).
        """
        while True:
            try:
                self.wait.until(
                    EC.presence_of_all_elements_located((
                        By.CSS_SELECTOR, THUMBNAIL_SELECTOR
                    ))
                )
                time.sleep(2)

                current_films = len(
                    self.driver.find_elements(
                        By.CSS_SELECTOR, THUMBNAIL_SELECTOR
                    )
                )
                if total_films > 0:
                    logger.info(
                        "Films affichés : %d/%d", current_films, total_films
                    )
                else:
                    logger.info(
                        "Films affichés : %d (total inconnu)", current_films
                    )

                if total_films > 0 and current_films >= total_films:
                    logger.info("Tous les films sont affichés")
                    break

                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(2)

                try:
                    voir_plus = self.wait.until(
                        EC.element_to_be_clickable((
                            By.CSS_SELECTOR, LOAD_MORE_SELECTOR
                        ))
                    )
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", voir_plus
                    )
                    time.sleep(1)
                    self.driver.execute_script(
                        "arguments[0].click();", voir_plus
                    )
                    logger.debug("Clic sur 'Voir plus'")
                    self.wait.until(
                        lambda d: len(
                            d.find_elements(
                                By.CSS_SELECTOR, THUMBNAIL_SELECTOR
                            )
                        ) > current_films
                    )
                except Exception as exc:
                    logger.warning(
                        "Bouton 'Voir plus' introuvable : %s", exc
                    )
                    break

            except Exception as exc:
                logger.error(
                    "Erreur lors du chargement des films : %s", exc
                )
                break

    def _get_requests_session(self) -> requests.Session:
        """Crée une session requests à partir des cookies Selenium.

        Returns:
            Session requests authentifiée avec les cookies du navigateur.
        """
        session = requests.Session()
        for cookie in self.driver.get_cookies():
            session.cookies.set(
                name=cookie["name"],
                value=cookie["value"],
                domain=cookie.get("domain", ""),
                path=cookie.get("path", "/"),
            )
        user_agent: str = self.driver.execute_script(
            "return navigator.userAgent;"
        )
        session.headers.update({
            "User-Agent": user_agent,
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Referer": BASE_URL + "/",
        })
        return session

    def _extract_url_from_thumbnail(self, item: Tag) -> Optional[str]:
        """Extrait l'URL absolue d'un film depuis un thumbnail.

        Args:
            item: Élément BeautifulSoup <figure.thumbnail>.

        Returns:
            URL absolue du film, ou None si non trouvée.
        """
        link = item.select_one("a.thumbnail-link")
        if link:
            href = str(link.get("href", ""))
            if href:
                return urljoin(BASE_URL, href)
        return None

    def _extract_director(self, film_soup: BeautifulSoup) -> Optional[str]:
        """Extrait le réalisateur depuis le HTML de la page film.

        Args:
            film_soup: Objet BeautifulSoup de la page film.

        Returns:
            Nom du réalisateur ou None si non trouvé.
        """
        elem = film_soup.select_one(".meta-body-direction a")
        if elem:
            return elem.get_text(strip=True)

        for item in film_soup.find_all(class_="meta-body-item"):
            if isinstance(item, Tag) and "Réalisateur" in item.get_text():
                link = item.find("a")
                if isinstance(link, Tag):
                    return link.get_text(strip=True)

        elem = film_soup.select_one('[data-testid="director"] a')
        if elem:
            return elem.get_text(strip=True)

        return None

    def _extract_release_date(
        self, film_soup: BeautifulSoup
    ) -> Optional[str]:
        """Extrait la date de sortie depuis le HTML de la page film.

        Args:
            film_soup: Objet BeautifulSoup de la page film.

        Returns:
            Date de sortie ou None si non trouvée.
        """
        elem = film_soup.select_one('.meta-body-info [class*="date"]')
        if elem:
            return elem.get_text(strip=True)

        for item in film_soup.find_all(class_="meta-body-item"):
            if isinstance(item, Tag) and "Sortie" in item.get_text():
                span = item.find("span")
                if isinstance(span, Tag):
                    return span.get_text(strip=True)

        for selector in ('[class*="release-date"]', ".date"):
            elem = film_soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)

        return None

    def _parse_film_html(
        self, url: str, html: str
    ) -> Optional[dict[str, str]]:
        """Parse le HTML d'une page film et extrait les données.

        Args:
            url: URL du film (utilisée comme identifiant).
            html: Contenu HTML brut de la page.

        Returns:
            Dictionnaire avec les données du film, ou None si échec.
        """
        try:
            film_soup = BeautifulSoup(html, "lxml")

            # Titre
            titre: Optional[str] = None
            for selector in (
                "h1.title-entity",
                'h1[data-testid="title-entity"]',
                ".titlebar-title",
                ".meta-title",
                "h1",
            ):
                elem = film_soup.select_one(selector)
                if elem:
                    titre = elem.get_text(strip=True)
                    break

            realisateur = self._extract_director(film_soup)

            # Notes
            note_presse: Optional[str] = None
            note_spec: Optional[str] = None
            notes = film_soup.select(".stareval-note")
            if len(notes) >= 2:
                note_presse = notes[0].get_text(strip=True).replace(",", ".")
                note_spec = notes[1].get_text(strip=True).replace(",", ".")
            elif len(notes) == 1:
                note_spec = notes[0].get_text(strip=True).replace(",", ".")

            # Synopsis
            synopsis: Optional[str] = None
            for selector in (
                ".content-txt",
                ".synopsis-txt",
                '[class*="synopsis"]',
                ".movie-synopsis",
            ):
                elem = film_soup.select_one(selector)
                if elem:
                    synopsis = " ".join(elem.get_text(strip=True).split())
                    break

            # Plateformes VOD
            plateformes: list[str] = []
            vod_section = film_soup.select_one("#ovw-products")
            if vod_section:
                vod_text = vod_section.get_text(strip=True).lower()
                for key, name in KNOWN_PLATFORMS.items():
                    if key in vod_text and name not in plateformes:
                        plateformes.append(name)

            # Score de recommandation
            score_reco: Optional[str] = None
            score_elem = film_soup.select_one(".dZ6Qx4goXRfseGsQ2h8g")
            if score_elem:
                score_reco = score_elem.get_text(strip=True)

            date_sortie = self._extract_release_date(film_soup)

            return {
                "titre": titre or "Non trouvé",
                "realisateur": realisateur or "Non trouvé",
                "date_sortie": date_sortie or "Non disponible",
                "synopsis": synopsis or "Non disponible",
                "note_presse": note_presse or "Non disponible",
                "note_spectateurs": note_spec or "Non disponible",
                "score_recommandation": score_reco or "Non disponible",
                "plateformes": (
                    ", ".join(plateformes)
                    if plateformes
                    else "Non disponible"
                ),
                "url": url,
            }
        except Exception as exc:
            logger.error("Erreur parsing film %s : %s", url, exc)
            return None

    def _fetch_film(
        self, session: requests.Session, url: str
    ) -> Optional[dict[str, str]]:
        """Fetche et parse une page film via requests.

        Args:
            session: Session requests authentifiée.
            url: URL absolue du film.

        Returns:
            Données du film ou None si échec.
        """
        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return self._parse_film_html(url, response.text)
        except Exception as exc:
            logger.error("Erreur fetch %s : %s", url, exc)
            return None

    def extract_films(
        self,
        urls: list[str],
        session: requests.Session,
        max_workers: int = MAX_WORKERS,
    ) -> list[dict[str, str]]:
        """Extrait les infos de plusieurs films en parallèle via requests.

        L'ordre de la liste retournée correspond à l'ordre des URLs en entrée.

        Args:
            urls: URLs absolues des films à extraire.
            session: Session requests authentifiée.
            max_workers: Nombre de threads parallèles.

        Returns:
            Liste des données films (les échecs sont exclus).
        """
        total = len(urls)
        results: list[Optional[dict[str, str]]] = [None] * total
        completed = 0

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers
        ) as executor:
            future_to_index = {
                executor.submit(self._fetch_film, session, url): i
                for i, url in enumerate(urls)
            }
            for future in concurrent.futures.as_completed(future_to_index):
                i = future_to_index[future]
                result = future.result()
                results[i] = result
                completed += 1
                if result:
                    logger.info(
                        "Film %d/%d : %s",
                        completed,
                        total,
                        result["titre"],
                    )
                else:
                    logger.warning(
                        "Film %d/%d introuvable : %s",
                        completed,
                        total,
                        urls[i],
                    )

        return [r for r in results if r is not None]

    def save_to_csv(
        self,
        films: list[dict[str, str]],
        filename: str = "films_allocine.csv",
    ) -> None:
        """Sauvegarde les films dans un fichier CSV.

        Args:
            films: Liste des données films.
            filename: Chemin complet du fichier de sortie.
        """
        if not films:
            logger.warning("Aucun film à sauvegarder")
            return

        all_platforms: set[str] = set()
        for film in films:
            if film["plateformes"] != "Non disponible":
                all_platforms.update(film["plateformes"].split(", "))

        platform_columns = sorted(all_platforms)

        formatted_films = []
        for film in films:
            available = (
                film["plateformes"].split(", ")
                if film["plateformes"] != "Non disponible"
                else []
            )
            row: dict[str, str] = {
                "Titre": film["titre"],
                "Réalisateur": film["realisateur"],
                "Date de sortie": film["date_sortie"],
                "Synopsis": film["synopsis"],
                "Note Presse": film["note_presse"],
                "Note Spectateurs": film["note_spectateurs"],
                "Score Recommandation": film["score_recommandation"],
            }
            for platform in platform_columns:
                row[platform] = "X" if platform in available else ""
            row["URL"] = film["url"]
            formatted_films.append(row)

        df = pd.DataFrame(formatted_films)
        columns_order = (
            [
                "Titre",
                "Réalisateur",
                "Date de sortie",
                "Synopsis",
                "Note Presse",
                "Note Spectateurs",
                "Score Recommandation",
            ]
            + list(platform_columns)
            + ["URL"]
        )
        df = df[columns_order]

        self._write_csv(df, filename, len(films))

    def _write_csv(
        self, df: pd.DataFrame, filename: str, count: int
    ) -> None:
        """Écrit le DataFrame en CSV avec gestion du fichier ouvert.

        Args:
            df: DataFrame à écrire.
            filename: Chemin du fichier de sortie.
            count: Nombre de films (pour le message de confirmation).
        """
        try:
            df.to_csv(filename, index=False, encoding="utf-8-sig", sep=";")
            logger.info("%d films sauvegardés dans %s", count, filename)
        except PermissionError:
            logger.error(
                "Fichier %s ouvert ailleurs, fermer puis Entrée", filename
            )
            input(
                "Veuillez fermer le fichier et appuyer sur Entrée "
                "pour réessayer..."
            )
            try:
                df.to_csv(
                    filename, index=False, encoding="utf-8-sig", sep=";"
                )
                logger.info(
                    "%d films sauvegardés dans %s", count, filename
                )
            except Exception as exc:
                logger.error("Échec de la sauvegarde : %s", exc)

    def close(self) -> None:
        """Ferme le navigateur proprement."""
        try:
            self.driver.quit()
        except Exception as exc:
            logger.warning(
                "Erreur lors de la fermeture du navigateur : %s", exc
            )


def is_chrome_running_with_debug_port() -> bool:
    """Vérifie si Chrome tourne déjà avec le port de débogage activé.

    Returns:
        True si Chrome est lancé avec --remote-debugging-port=9222.
    """
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            if proc.info["name"] == "chrome.exe":
                cmdline = proc.info["cmdline"]
                debug_flag = f"--remote-debugging-port={DEBUG_PORT}"
                if cmdline and debug_flag in cmdline:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


def main() -> None:
    scraper = AllocineScraper()
    try:
        logger.info("Vérification de la connexion...")
        scraper.driver.get("https://mon.allocine.fr/mes-films/envie-de-voir/")
        time.sleep(3)

        if "connexion" in scraper.driver.current_url.lower():
            logger.info("Session expirée, reconnexion nécessaire...")
            if not scraper.login(ALLOCINE_EMAIL, ALLOCINE_PASSWORD):
                logger.error("Échec de la connexion automatique")
                input(
                    "Veuillez vous connecter manuellement "
                    "puis appuyez sur Entrée..."
                )
        else:
            logger.info("Déjà connecté")

        films = scraper.get_watchlist()  # type: ignore[attr-defined]
        scraper.save_to_csv(films)
    except Exception as exc:
        logger.error("Erreur inattendue : %s", exc)
    finally:
        scraper.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s : %(message)s",
    )
    main()
