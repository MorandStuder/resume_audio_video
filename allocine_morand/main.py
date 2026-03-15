import logging
import sys
import time

# Force UTF-8 sur la console Windows (évite les caractères corrompus)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from allocine_scraper import ALLOCINE_EMAIL, ALLOCINE_PASSWORD
from films_a_voir_scraper import FilmsAVoirScraper
from films_vus_scraper import FilmsVusScraper

logger = logging.getLogger(__name__)

URL_FILMS_VUS = "https://mon.allocine.fr/mes-films/vus/"
URL_FILMS_A_VOIR = "https://mon.allocine.fr/mes-films/envie-de-voir/"


def connect_to_allocine(scraper: FilmsVusScraper, url: str) -> None:
    """Vérifie et établit la connexion à Allociné.

    Args:
        scraper: Instance du scraper.
        url: URL à charger pour vérifier la session.
    """
    logger.info("Vérification de la connexion...")
    scraper.driver.get(url)
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


def get_films_vus(scraper: FilmsVusScraper) -> None:
    """Menu de choix du mode de récupération des films vus.

    Args:
        scraper: Instance de FilmsVusScraper.
    """
    while True:
        print("\nMode de sauvegarde pour les films vus :")
        print("1. Sauvegarde complète (tous les films)")
        print("2. Sauvegarde incrémentale (nouveaux films uniquement)")
        print("3. Retour au menu principal")

        choix = input("\nVotre choix (1-3) : ").strip()

        if choix == "1":
            films = scraper.get_watchlist(incremental=False)
            scraper.save_to_csv(films, incremental=False)
            break
        elif choix == "2":
            films = scraper.get_watchlist(incremental=True)
            scraper.save_to_csv(films, incremental=True)
            break
        elif choix == "3":
            return
        else:
            print("Choix invalide. Veuillez réessayer.")


def main() -> None:
    scraper = None
    try:
        while True:
            print("\nQue souhaitez-vous faire ?")
            print("1. Récupérer la liste des films vus")
            print("2. Récupérer la liste des films à voir")
            print("3. Quitter")

            choix = input("\nVotre choix (1-3) : ").strip()

            if choix == "1":
                if scraper:
                    scraper.close()
                scraper = FilmsVusScraper()
                try:
                    connect_to_allocine(scraper, URL_FILMS_VUS)
                    get_films_vus(scraper)
                except Exception as exc:
                    logger.error("Erreur films vus : %s", exc)

            elif choix == "2":
                if scraper:
                    scraper.close()
                scraper = FilmsAVoirScraper()
                try:
                    connect_to_allocine(scraper, URL_FILMS_A_VOIR)
                    films = scraper.get_watchlist()
                    scraper.save_to_csv(films)
                except Exception as exc:
                    logger.error("Erreur films à voir : %s", exc)

            elif choix == "3":
                print("\nAu revoir !")
                break
            else:
                print("Choix invalide. Veuillez réessayer.")

    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s : %(message)s",
    )
    main()
