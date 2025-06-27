from allocine_scraper import AllocineScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from config import ALLOCINE_EMAIL, ALLOCINE_PASSWORD
import time
import pandas as pd
import re
import os


class FilmsAVoirScraper(AllocineScraper):
    def get_watchlist(self):
        """Récupère la liste des films à voir"""
        try:
            print("\nAccès à la liste des films à voir...")
            watchlist_url = "https://mon.allocine.fr/mes-films/envie-de-voir/"
            self.driver.get(watchlist_url)
            time.sleep(3)
            
            # Vérifier si on est toujours connecté
            if "connexion" in self.driver.current_url.lower():
                print("❌ Session expirée, tentative de reconnexion...")
                if not self.login(ALLOCINE_EMAIL, ALLOCINE_PASSWORD):
                    print("❌ Échec de la reconnexion automatique")
                    return []
                # Réessayer d'accéder à la page après reconnexion
                self.driver.get(watchlist_url)
                time.sleep(3)
            
            # Obtenir le nombre total de films
            total_films = self._get_total_films_count(watchlist_url)
            if not total_films:
                print("❌ Impossible de récupérer le nombre total de films")
                return []
            
            # Charger tous les films
            self._load_all_films(total_films)
            
            # Extraire les informations des films
            print("\nExtraction des informations des films...")
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            film_items = soup.select("figure.thumbnail")
            
            if not film_items:
                print("❌ Aucun film trouvé sur la page")
                return []
                
            print(f"Nombre de films trouvés: {len(film_items)}")
            
            films = []
            for i, item in enumerate(film_items, 1):
                try:
                    film_data = self._extract_film_info(item)
                    if film_data:
                        films.append(film_data)
                        print(f"Film {i}/{len(film_items)} ajouté: {film_data['titre']}")
                    else:
                        print(f"⚠️ Impossible d'extraire les informations du film {i}")
                except Exception as e:
                    print(f"⚠️ Erreur lors de l'extraction du film {i}: {str(e)}")
            
            return films
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des films: {str(e)}")
            return []

    def save_to_csv(self, films, filename='films_a_voir_allocine.csv'):
        """Sauvegarde les films dans un fichier CSV"""
        # Créer le répertoire output s'il n'existe pas
        os.makedirs('output', exist_ok=True)
        output_file = os.path.join('output', filename)
        super().save_to_csv(films, output_file)


def main():
    scraper = FilmsAVoirScraper()
    
    try:
        # Vérifier si déjà connecté
        print("Vérification de la connexion...")
        scraper.driver.get("https://mon.allocine.fr/mes-films/envie-de-voir/")
        time.sleep(3)
        
        # Si on est redirigé vers la page de connexion, se connecter
        if "connexion" in scraper.driver.current_url.lower():
            print("Session expirée, reconnexion nécessaire...")
            
            if not scraper.login(ALLOCINE_EMAIL, ALLOCINE_PASSWORD):
                print("\n❌ Échec de la connexion automatique")
                input("Veuillez vous connecter manuellement puis appuyez sur Entrée...")
        else:
            print("✅ Déjà connecté")
        
        # Récupération des films
        films = scraper.get_watchlist()
        # Sauvegarde
        scraper.save_to_csv(films)
        
    except Exception as e:
        print(f"Une erreur est survenue: {str(e)}")


if __name__ == "__main__":
    main() 