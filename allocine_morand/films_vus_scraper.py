import logging
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup, Tag
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from allocine_scraper import (
    AllocineScraper,
    ALLOCINE_EMAIL,
    ALLOCINE_PASSWORD,
    LOAD_MORE_SELECTOR,
    OUTPUT_DIR,
    THUMBNAIL_SELECTOR,
)

logger = logging.getLogger(__name__)

CSV_FILMS_VUS = "films_vus_allocine.csv"

# Colonnes fixes du CSV (hors plateformes dynamiques)
FIXED_COLUMNS = [
    "Titre",
    "Réalisateur",
    "Date de sortie",
    "Synopsis",
    "Note Presse",
    "Note Spectateurs",
    "Ma Note",
    "Score Recommandation",
]


class FilmsVusScraper(AllocineScraper):
    def get_watchlist(self, incremental: bool = False) -> list[dict[str, str]]:
        """Récupère la liste des films vus.

        Args:
            incremental: Si True, ne récupère que les nouveaux films
                depuis le dernier export.

        Returns:
            Liste des données films (peut être vide).
        """
        try:
            logger.info("Accès à la liste des films vus...")
            watchlist_url = "https://mon.allocine.fr/mes-films/vus/"
            self.driver.get(watchlist_url)
            time.sleep(3)

            total_films = self._get_total_films_count(watchlist_url)
            # total_films == 0 = sélecteur introuvable → mode "charger tout"

            films_to_load: int = total_films
            existing_films_data: Optional[pd.DataFrame] = None

            if incremental:
                existing_films_data = self._get_existing_films_data()
                existing_count = (
                    len(existing_films_data)
                    if existing_films_data is not None
                    else 0
                )
                if total_films > 0 and existing_count >= total_films:
                    logger.info("Pas de nouveaux films à récupérer")
                    return []
                if total_films > 0:
                    new_films = total_films - existing_count  # noqa: E501
                    logger.info(
                        "Nouveaux films à récupérer : %d", new_films
                    )
                    # +1 pour le film de vérification de continuité
                    films_to_load = new_films + 1
                else:
                    logger.warning(
                        "Total inconnu — chargement complet"
                        " en mode incrémental"
                    )

            self._load_all_films(total_films, films_to_load)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            film_items = soup.select(THUMBNAIL_SELECTOR)
            logger.info("Films trouvés sur la page : %d", len(film_items))

            # Créer la session requests une seule fois
            session = self._get_requests_session()

            if incremental and existing_films_data is not None:
                film_items = self._verify_and_trim_incremental(
                    film_items, existing_films_data, films_to_load, session
                )
                if film_items is None:
                    return []

            # Collecter les URLs et les notes utilisateur depuis les thumbnails
            urls: list[str] = []
            url_to_rating: dict[str, str] = {}
            for item in film_items:
                if not isinstance(item, Tag):
                    continue
                url = self._extract_url_from_thumbnail(item)
                if url:
                    urls.append(url)
                    url_to_rating[url] = self._extract_user_rating(item)

            if not urls:
                logger.error("Aucune URL de film extraite")
                return []

            logger.info(
                "Films à extraire : %d — extraction en parallèle...",
                len(urls),
            )

            # Extraction parallèle via requests
            films = self.extract_films(urls, session)

            # Rattacher la note utilisateur à chaque film
            for film in films:
                film["note_user"] = url_to_rating.get(
                    film["url"], "Non noté"
                )

            return films

        except Exception as exc:
            logger.error("Erreur récupération films vus : %s", exc)
            return []

    def _extract_user_rating(self, item: Tag) -> str:
        """Extrait la note utilisateur depuis un thumbnail.

        Args:
            item: Élément BeautifulSoup <figure.thumbnail>.

        Returns:
            Note sous forme de chaîne (ex: "3.5") ou "Non noté".
        """
        rating_stars = item.select(".rating-star.active")
        if rating_stars:
            return str(len(rating_stars) / 2)
        return "Non noté"

    def _verify_and_trim_incremental(
        self,
        film_items: list[Tag],
        existing_data: pd.DataFrame,
        films_to_load: int,
        session: requests.Session,
    ) -> Optional[list[Tag]]:
        """Vérifie la continuité avec le CSV existant en mode incrémental.

        Compare le dernier film chargé avec le premier film du CSV existant.
        En cas d'incohérence, avertit l'utilisateur mais laisse le choix
        de continuer plutôt qu'abandonner silencieusement.

        Args:
            film_items: Éléments <figure> de la page.
            existing_data: DataFrame du CSV existant.
            films_to_load: Nombre de films chargés (nouveaux + 1 de vérif).
            session: Session requests authentifiée.

        Returns:
            Liste tronquée aux seuls nouveaux films, ou None si l'utilisateur
            choisit d'arrêter.
        """
        first_existing = existing_data.iloc[0]
        verification_item = film_items[films_to_load - 1]
        verification_url = self._extract_url_from_thumbnail(verification_item)

        if verification_url:
            verification_data = self._fetch_film(session, verification_url)
            if (
                verification_data
                and verification_data["titre"] != first_existing["Titre"]
            ):
                logger.warning(
                    "Incohérence : en ligne='%s', attendu='%s'",
                    verification_data["titre"],
                    first_existing["Titre"],
                )
                print(
                    "\n⚠️  Incohérence dans l'ordre des films.\n"
                    f"  En ligne : {verification_data['titre']}\n"
                    f"  Attendu  : {first_existing['Titre']}\n"
                    "Continuer quand même ? (o/N) : ",
                    end="",
                )
                if input().strip().lower() != "o":
                    logger.info(
                        "Mode incrémental annulé — relancez"
                        " en mode complet"
                    )
                    return None

        # Garder uniquement les nouveaux films (sans le film de vérification)
        return film_items[: films_to_load - 1]

    def _get_existing_films_data(
        self, filename: str = CSV_FILMS_VUS
    ) -> Optional[pd.DataFrame]:
        """Lit le CSV existant des films vus.

        Args:
            filename: Nom du fichier CSV dans le dossier output.

        Returns:
            DataFrame ou None si le fichier est absent/illisible.
        """
        filepath = OUTPUT_DIR / filename
        if filepath.exists():
            try:
                return pd.read_csv(
                    filepath, sep=";", encoding="utf-8-sig"
                )
            except Exception as exc:
                logger.error(
                    "Erreur lecture fichier existant : %s", exc
                )
        return None

    def _get_existing_films_count(
        self, filename: str = CSV_FILMS_VUS
    ) -> int:
        """Retourne le nombre de films dans le CSV existant.

        Args:
            filename: Nom du fichier CSV dans le dossier output.

        Returns:
            Nombre de lignes, ou 0 si absent.
        """
        df = self._get_existing_films_data(filename)
        return len(df) if df is not None else 0

    def _load_all_films(
        self, total_films: int, films_to_load: Optional[int] = None
    ) -> None:
        """Charge les films en cliquant sur 'Voir plus'.

        Args:
            total_films: Nombre total de films disponibles sur Allociné.
            films_to_load: Nombre de films à charger (None = tous).
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

                if films_to_load and current_films >= films_to_load:
                    logger.info("Nombre suffisant de films chargés")
                    break
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
                    "Erreur lors du comptage des films : %s", exc
                )
                break

    def save_to_csv(
        self,
        films: list[dict[str, str]],
        filename: str = CSV_FILMS_VUS,
        incremental: bool = False,
    ) -> None:
        """Sauvegarde les films dans un fichier CSV.

        Args:
            films: Liste des films à sauvegarder.
            filename: Nom du fichier de sortie (dans output/).
            incremental: Si True, fusionne avec le fichier existant.
        """
        if not films:
            logger.warning("Aucun nouveau film à sauvegarder")
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
                "Ma Note": film["note_user"],
                "Score Recommandation": film["score_recommandation"],
            }
            for platform in platform_columns:
                row[platform] = "X" if platform in available else ""
            row["URL"] = film["url"]
            formatted_films.append(row)

        df_new = pd.DataFrame(formatted_films)

        OUTPUT_DIR.mkdir(exist_ok=True)
        output_file = OUTPUT_DIR / filename

        if incremental and output_file.exists():
            try:
                df_existing = pd.read_csv(
                    output_file, sep=";", encoding="utf-8-sig"
                )
                # Fusionner les colonnes de plateformes
                excluded = set(FIXED_COLUMNS + ["URL"])
                all_platforms.update(
                    col
                    for col in df_existing.columns
                    if col not in excluded
                )
                platform_columns = sorted(all_platforms)

                for df in (df_existing, df_new):
                    for platform in platform_columns:
                        if platform not in df.columns:
                            df[platform] = ""

                df = pd.concat([df_new, df_existing], ignore_index=True)
            except Exception as exc:
                logger.error("Erreur fusion CSV : %s", exc)
                df = df_new
        else:
            df = df_new

        columns_order = (
            FIXED_COLUMNS + list(platform_columns) + ["URL"]
        )
        df = df[columns_order]

        self._write_csv(df, str(output_file), len(films))
