from allocine_scraper import AllocineScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd
import os


class FilmsVusScraper(AllocineScraper):
    def get_watchlist(self, incremental=False):
        """Récupère la liste des films vus
        
        Args:
            incremental (bool): Si True, ne récupère que les nouveaux films
        """
        try:
            print("\nAccès à la liste des films vus...")
            watchlist_url = "https://mon.allocine.fr/mes-films/vus/"
            self.driver.get(watchlist_url)
            time.sleep(3)
            
            total_films = self._get_total_films_count(watchlist_url)
            if not total_films:
                return []
            
            # En mode incrémental, vérifier s'il y a de nouveaux films
            films_to_load = total_films
            existing_films_data = None
            if incremental:
                existing_films_data = self._get_existing_films_data()
                existing_films = len(existing_films_data) if existing_films_data is not None else 0
                if existing_films >= total_films:
                    print("\n✅ Pas de nouveaux films à récupérer")
                    return []
                new_films = total_films - existing_films
                print(f"\nNouveaux films à récupérer : {new_films}")
                # Charger un film de plus pour la vérification
                films_to_load = new_films + 1
            
            self._load_all_films(total_films, films_to_load)
            
            print("\nExtraction des informations des films...")
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            film_items = soup.select("figure.thumbnail")
            
            print(f"Nombre de films trouvés: {len(film_items)}")
            
            # En mode incrémental, vérifier la continuité avec le fichier existant
            if incremental and existing_films_data is not None:
                # Extraire le premier film existant pour comparaison
                first_existing_film = existing_films_data.iloc[0]
                verification_item = film_items[films_to_load - 1]
                verification_data = self._extract_film_info(verification_item)
                
                if verification_data and verification_data['titre'] != first_existing_film['Titre']:
                    print("\n⚠️ Attention : Incohérence détectée dans l'ordre des films")
                    print(f"Film en ligne : {verification_data['titre']}")
                    print(f"Film attendu : {first_existing_film['Titre']}")
                    return []
                
                # Ne garder que les nouveaux films
                film_items = film_items[:films_to_load - 1]
            
            films = []
            for i, item in enumerate(film_items, 1):
                film_data = self._extract_film_info(item)
                if film_data:
                    film_data = self._add_user_rating(film_data, item)
                    films.append(film_data)
                    print(
                        f"Film {i}/{len(film_items)} ajouté: "
                        f"{film_data['titre']}"
                    )
            
            return films
            
        except Exception as e:
            print(f"Erreur lors de la récupération des films: {str(e)}")
            return []

    def _get_existing_films_data(self, filename='films_vus_allocine.csv'):
        """Retourne les données des films du fichier CSV existant"""
        try:
            filepath = os.path.join('output', filename)
            if os.path.exists(filepath):
                return pd.read_csv(filepath, sep=';', encoding='utf-8-sig')
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier existant: {str(e)}")
        return None

    def _get_existing_films_count(self, filename='films_vus_allocine.csv'):
        """Retourne le nombre de films dans le fichier CSV existant"""
        df = self._get_existing_films_data(filename)
        return len(df) if df is not None else 0

    def _load_all_films(self, total_films, films_to_load=None):
        """Charge tous les films en cliquant sur 'Voir plus'
        
        Args:
            total_films (int): Nombre total de films disponibles
            films_to_load (int): Nombre de films à charger (None = tous)
        """
        while True:
            try:
                self.wait.until(
                    EC.presence_of_all_elements_located((
                        By.CSS_SELECTOR, 
                        "figure.thumbnail"
                    ))
                )
                time.sleep(2)
                
                current_films = len(self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "figure.thumbnail"
                ))
                print(f"\nFilms affichés: {current_films}/{total_films}")
                
                # Si on a assez de films, on arrête
                if films_to_load and current_films >= films_to_load:
                    print("Nombre suffisant de films chargés")
                    break
                
                if current_films >= total_films:
                    print("Tous les films sont affichés")
                    break
                    
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(2)
                
                try:
                    voir_plus = self.wait.until(
                        EC.element_to_be_clickable((
                            By.CSS_SELECTOR,
                            'button.button.button-default-full'
                            '.button-md.load-more-button'
                        ))
                    )
                    
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView(true);", 
                        voir_plus
                    )
                    time.sleep(1)
                    
                    self.driver.execute_script(
                        "arguments[0].click();", 
                        voir_plus
                    )
                    print("Clic sur 'Voir plus'")
                    time.sleep(3)
                    
                    self.wait.until(
                        lambda x: len(x.find_elements(
                            By.CSS_SELECTOR, 
                            "figure.thumbnail"
                        )) > current_films
                    )
                    
                except Exception as e:
                    print("Plus de bouton 'Voir plus' trouvé")
                    print(f"Erreur: {str(e)}")
                    break
                    
            except Exception as e:
                print(f"Erreur lors du comptage des films: {str(e)}")
                break

    def _add_user_rating(self, film_data, item):
        """Ajoute la note utilisateur aux données du film"""
        try:
            note_user = None
            
            rating_stars = item.select('.rating-star.active')
            if rating_stars:
                note_user = len(rating_stars) / 2
            
            if not note_user and film_data.get('url'):
                self.driver.get(film_data['url'])
                time.sleep(2)
                
                user_rating = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    '.rating-star.active'
                )
                if user_rating:
                    note_user = len(user_rating) / 2
            
            if note_user:
                film_data['note_user'] = str(note_user)
                print(f"Note utilisateur trouvée: {note_user}")
            else:
                film_data['note_user'] = 'Non noté'
            
        except Exception as e:
            print(
                f"Erreur lors de la recherche de la note utilisateur: "
                f"{str(e)}"
            )
            film_data['note_user'] = 'Erreur'
        
        return film_data

    def save_to_csv(self, films, filename='films_vus_allocine.csv', 
                   incremental=False):
        """Sauvegarde les films dans un fichier CSV
        
        Args:
            films (list): Liste des films à sauvegarder
            filename (str): Nom du fichier de sortie
            incremental (bool): Si True, ajoute les films au fichier existant
        """
        if not films:
            print("\n❌ Aucun nouveau film à sauvegarder")
            return

        # Formater les nouveaux films
        all_platforms = set()
        for film in films:
            if film['plateformes'] != 'Non disponible':
                platforms = film['plateformes'].split(', ')
                all_platforms.update(platforms)
        
        platform_columns = sorted(list(all_platforms))
        
        formatted_films = []
        for film in films:
            film_data = {
                'Titre': film['titre'],
                'Réalisateur': film['realisateur'],
                'Date de sortie': film['date_sortie'],
                'Synopsis': film['synopsis'],
                'Note Presse': film['note_presse'],
                'Note Spectateurs': film['note_spectateurs'],
                'Ma Note': film['note_user'],
                'Score Recommandation': film['score_recommandation']
            }
            
            available_platforms = []
            if film['plateformes'] != 'Non disponible':
                available_platforms = film['plateformes'].split(', ')
            for platform in platform_columns:
                film_data[platform] = (
                    'X' if platform in available_platforms else ''
                )
            
            film_data['URL'] = film['url']
            formatted_films.append(film_data)
        
        df_new = pd.DataFrame(formatted_films)
        
        # Créer le répertoire output s'il n'existe pas
        os.makedirs('output', exist_ok=True)
        output_file = os.path.join('output', filename)
        
        # En mode incrémental, fusionner avec le fichier existant
        if incremental and os.path.exists(output_file):
            try:
                df_existing = pd.read_csv(
                    output_file, 
                    sep=';', 
                    encoding='utf-8-sig'
                )
                
                # Récupérer toutes les plateformes
                excluded_cols = [
                    'Titre', 'Réalisateur', 'Date de sortie', 'Synopsis',
                    'Note Presse', 'Note Spectateurs', 'Ma Note',
                    'Score Recommandation', 'URL'
                ]
                all_platforms.update(
                    col for col in df_existing.columns
                    if col not in excluded_cols
                )
                platform_columns = sorted(list(all_platforms))
                
                # Ajouter les colonnes manquantes
                for df in [df_existing, df_new]:
                    for platform in platform_columns:
                        if platform not in df.columns:
                            df[platform] = ''
                
                # Mettre les nouveaux films au début
                df = pd.concat([df_new, df_existing], ignore_index=True)
            except Exception as e:
                print(f"Erreur lors de la fusion des fichiers: {str(e)}")
                df = df_new
        else:
            df = df_new
        
        # Réorganiser les colonnes
        columns_order = [
            'Titre', 'Réalisateur', 'Date de sortie', 'Synopsis',
            'Note Presse', 'Note Spectateurs', 'Ma Note',
            'Score Recommandation'
        ] + platform_columns + ['URL']
        
        df = df[columns_order]
        
        def _save_dataframe():
            df.to_csv(output_file, index=False, encoding='utf-8-sig', sep=';')
            print(
                f"\n✅ {len(films)} nouveaux films ajoutés "
                f"(total: {len(df)}) dans {output_file}"
            )
        
        try:
            _save_dataframe()
        except PermissionError:
            msg = "Le fichier est probablement ouvert dans un autre programme"
            print(f"\n❌ Impossible de sauvegarder le fichier {output_file}")
            print(msg)
            input("Veuillez fermer le fichier et appuyer sur Entrée...")
            
            try:
                _save_dataframe()
            except Exception as e:
                print(f"\n❌ Échec de la sauvegarde: {str(e)}") 