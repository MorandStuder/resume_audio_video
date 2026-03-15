import logging
import time

from bs4 import BeautifulSoup, Tag

from allocine_scraper import (
    ALLOCINE_EMAIL,
    ALLOCINE_PASSWORD,
    AllocineScraper,
    OUTPUT_DIR,
)

logger = logging.getLogger(__name__)

CSV_FILMS_A_VOIR = "films_a_voir_allocine.csv"


class FilmsAVoirScraper(AllocineScraper):
    def get_watchlist(self) -> list[dict[str, str]]:
        """Récupère la liste des films à voir.

        Returns:
            Liste des données films (peut être vide).
        """
        try:
            logger.info("Accès à la liste des films à voir...")
            watchlist_url = "https://mon.allocine.fr/mes-films/envie-de-voir/"
            self.driver.get(watchlist_url)
            time.sleep(3)

            if "connexion" in self.driver.current_url.lower():
                logger.warning(
                    "Session expirée, tentative de reconnexion..."
                )
                if not self.login(ALLOCINE_EMAIL, ALLOCINE_PASSWORD):
                    logger.error("Échec de la reconnexion automatique")
                    return []
                self.driver.get(watchlist_url)
                time.sleep(3)

            total_films = self._get_total_films_count(
                watchlist_url, href_pattern="envie-de-voir"
            )
            # total_films == 0 = sélecteur introuvable → mode "charger tout"
            self._load_all_films(total_films)

            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            film_items = soup.select("figure.thumbnail")

            if not film_items:
                logger.error("Aucun film trouvé sur la page")
                return []

            logger.info(
                "Films trouvés : %d — extraction en parallèle...",
                len(film_items),
            )

            # Collecter les URLs depuis les thumbnails
            urls: list[str] = []
            for item in film_items:
                if not isinstance(item, Tag):
                    continue
                url = self._extract_url_from_thumbnail(item)
                if url:
                    urls.append(url)

            if not urls:
                logger.error("Aucune URL de film extraite")
                return []

            # Extraction parallèle via requests
            session = self._get_requests_session()
            return self.extract_films(urls, session)

        except Exception as exc:
            logger.error("Erreur récupération films à voir : %s", exc)
            return []

    def save_to_csv(
        self,
        films: list[dict[str, str]],
        filename: str = CSV_FILMS_A_VOIR,
    ) -> None:
        """Sauvegarde les films dans output/<filename>.

        Args:
            films: Liste des données films.
            filename: Nom du fichier CSV de sortie.
        """
        OUTPUT_DIR.mkdir(exist_ok=True)
        output_file = str(OUTPUT_DIR / filename)
        super().save_to_csv(films, output_file)
