3# -*- coding: utf-8 -*-
from films_vus_scraper import FilmsVusScraper
from films_a_voir_scraper import FilmsAVoirScraper
from config import ALLOCINE_EMAIL, ALLOCINE_PASSWORD
import time


def connect_to_allocine(scraper, url):
    """Gère la connexion à Allociné
    
    Args:
        scraper: Instance du scraper
        url (str): URL à vérifier pour la connexion
    """
    print("Vérification de la connexion...")
    scraper.driver.get(url)
    time.sleep(3)
    
    if "connexion" in scraper.driver.current_url.lower():
        print("Session expirée, reconnexion nécessaire...")
        
        if not scraper.login(ALLOCINE_EMAIL, ALLOCINE_PASSWORD):
            print("\n❌ Échec de la connexion automatique")
            input("Veuillez vous connecter manuellement puis appuyez...")
    else:
        print("✅ Déjà connecté")


def get_films_vus(scraper):
    """Récupère les films vus avec le mode choisi par l'utilisateur"""
    while True:
        print("\nMode de sauvegarde pour les films vus :")
        print("1. Sauvegarde complète (tous les films)")
        print("2. Sauvegarde incrémentale (nouveaux films uniquement)")
        print("3. Retour au menu principal")
        
        choix = input("\nVotre choix (1-3) : ")
        
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
            print("\nChoix invalide. Veuillez réessayer.")


def main():
    scraper = None
    try:
        while True:
            print("\nQue souhaitez-vous faire ?")
            print("1. Récupérer la liste des films vus")
            print("2. Récupérer la liste des films à voir")
            print("3. Quitter")
            
            choix = input("\nVotre choix (1-3) : ")
            
            if choix == "1":
                if scraper:
                    scraper.driver.quit()
                scraper = FilmsVusScraper()
                try:
                    connect_to_allocine(
                        scraper, 
                        "https://mon.allocine.fr/mes-films/vus/"
                    )
                    get_films_vus(scraper)
                except Exception as e:
                    print(f"Une erreur est survenue: {str(e)}")
                
            elif choix == "2":
                if scraper:
                    scraper.driver.quit()
                scraper = FilmsAVoirScraper()
                try:
                    connect_to_allocine(
                        scraper, 
                        "https://mon.allocine.fr/mes-films/a-voir/"
                    )
                    films = scraper.get_watchlist()
                    scraper.save_to_csv(films)
                except Exception as e:
                    print(f"Une erreur est survenue: {str(e)}")
            elif choix == "3":
                print("\nAu revoir !")
                break
            else:
                print("\nChoix invalide. Veuillez réessayer.")
    finally:
        if scraper:
            scraper.driver.quit()


if __name__ == "__main__":
    main() 