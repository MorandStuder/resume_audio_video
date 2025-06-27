import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from config import ALLOCINE_EMAIL, ALLOCINE_PASSWORD
#from credentials_manager import get_credentials, save_credentials
import psutil
import re


class AllocineScraper:
    def __init__(self):
        try:
            # Essayer de se connecter à une session Chrome existante
            options = webdriver.ChromeOptions()
            options.add_experimental_option(
                "debuggerAddress", 
                "127.0.0.1:9222"
            )
            self.driver = webdriver.Chrome(options=options)
            print("✅ Connexion à la session Chrome existante")
        except Exception:
            print("Démarrage d'une nouvelle session Chrome...")
            # Si pas de session existante, lancer Chrome avec le port de débogage
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')
            options.add_argument('--disable-notifications')
            options.add_argument('--remote-debugging-port=9222')
            # Remplacer detach par un autre moyen de garder le navigateur ouvert
            options.add_experimental_option("detach", True)
            self.driver = webdriver.Chrome(options=options)
        
        self.wait = WebDriverWait(self.driver, 10)

    def login(self, email, password):
        """Connexion à Allocine"""
        try:
            print("Connexion à Allocine...")
            # Aller d'abord sur la page principale pour gérer les cookies
            self.driver.get("https://mon.allocine.fr/connexion")
            time.sleep(3)
            
            # Accepter les cookies
            try:
                print("Recherche du bouton de cookies...")
                cookie_button = self.wait.until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR, 
                        "button.didomi-components-button--primary"
                    ))
                )
                time.sleep(1)
                self.driver.execute_script(
                    "arguments[0].click();", 
                    cookie_button
                )
                print("✅ Cookies acceptés")
                time.sleep(3)
            except Exception as e:
                print(f"⚠️ Erreur lors de l'acceptation des cookies: {str(e)}")
                print("Tentative de connexion sans accepter les cookies...")
            
            # Continuer avec la connexion
            print("Redirection vers la page de connexion...")
            self.driver.get("https://mon.allocine.fr/connexion/")
            time.sleep(3)
            
            # Vérifier si on est déjà connecté
            if "connexion" not in self.driver.current_url.lower():
                print("✅ Déjà connecté")
                return True
            
            # Remplir le formulaire de connexion
            print("Remplissage du formulaire...")
            try:
                email_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "email"))
                )
                print("Champ email trouvé")
            except Exception as e:
                print(f"❌ Impossible de trouver le champ email: {str(e)}")
                return False
            
            # Saisie lente de l'email
            for char in email:
                email_field.send_keys(char)
                time.sleep(0.1)
            
            time.sleep(1)
            
            try:
                password_field = self.driver.find_element(By.NAME, "password")
                print("Champ mot de passe trouvé")
            except Exception as e:
                print(f"❌ Impossible de trouver le champ mot de passe: {str(e)}")
                return False
            
            # Saisie lente du mot de passe
            for char in password:
                password_field.send_keys(char)
                time.sleep(0.1)
            
            time.sleep(2)
            
            try:
                submit_button = self.driver.find_element(
                    By.CSS_SELECTOR, 
                    "button[type='submit']"
                )
                print("Bouton de soumission trouvé")
            except Exception as e:
                print(f"❌ Impossible de trouver le bouton de soumission: {str(e)}")
                return False
            
            submit_button.click()
            print("Formulaire soumis")
            
            time.sleep(5)
            
            # Vérifier si la connexion a réussi
            if "connexion" not in self.driver.current_url.lower():
                print("✅ Connexion réussie!")
                return True
            else:
                print("❌ La connexion semble avoir échoué")
                return False
            
        except Exception as e:
            print(f"❌ Erreur lors de la connexion: {str(e)}")
            return False

    def _get_total_films_count(self, url):
        """Récupère le nombre total de films"""
        try:
            self.driver.get(url)
            time.sleep(3)
            
            total_count_elem = self.wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    'a.userspace-submenu-item[href*="vus"]'
                ))
            )
            count_text = total_count_elem.text
            match = re.search(r'\((\d+)\)', count_text)
            if match:
                total_films = int(match.group(1))
                print(f"\nNombre total de films à récupérer: {total_films}")
                return total_films
            else:
                print("Nombre de films non trouvé dans le texte")
                return 0
        except Exception as e:
            print(f"Erreur lors de la récupération du nombre total: {str(e)}")
            return 0

    def _load_all_films(self, total_films):
        """Charge tous les films en cliquant sur 'Voir plus'"""
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
                            'button.button.button-default-full.button-md.load-more-button'
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
                    print("Plus de bouton 'Voir plus' trouvé ou erreur lors du chargement")
                    print(f"Erreur: {str(e)}")
                    break
                    
            except Exception as e:
                print(f"Erreur lors du comptage des films: {str(e)}")
                break

    def _extract_film_info(self, item):
        """Extrait les informations détaillées d'un film"""
        try:
            # Obtenir l'URL du film
            link = item.select_one('a.thumbnail-link')
            if not link:
                return None
            
            url = link.get('href', '')
            if not url:
                return None

            print(f"\nExtraction des détails du film: {url}")
            
            # Visiter la page du film
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(url)
            time.sleep(2)
            
            # Parser la page du film
            film_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extraire les informations
            titre = None
            titre_selectors = [
                'h1.title-entity',
                'h1[data-testid="title-entity"]',
                '.titlebar-title',
                '.meta-title'
            ]
            for selector in titre_selectors:
                titre_elem = film_soup.select_one(selector)
                if titre_elem:
                    titre = titre_elem.text.strip()
                    break
            
            realisateur = None
            real_selectors = [
                '.meta-body-direction a',
                '.meta-body-item:contains("Réalisateur") a',
                '[data-testid="director"] a'
            ]
            for selector in real_selectors:
                real_elem = film_soup.select_one(selector)
                if real_elem:
                    realisateur = real_elem.text.strip()
                    break
            
            # Notes
            note_presse = None
            note_spec = None
            try:
                notes = film_soup.select('.stareval-note')
                
                if len(notes) >= 2:
                    note_presse = notes[0].get_text(strip=True).replace(',', '.')
                    print(f"Note presse trouvée: {note_presse}")
                    
                    note_spec = notes[1].get_text(strip=True).replace(',', '.')
                    print(f"Note spectateurs trouvée: {note_spec}")
                    
                elif len(notes) == 1:
                    note_spec = notes[0].get_text(strip=True).replace(',', '.')
                    print(f"Note spectateurs trouvée: {note_spec}")
                
            except Exception as e:
                print(f"Erreur lors de la recherche des notes: {str(e)}")
            
            # Synopsis
            synopsis = None
            synopsis_selectors = [
                '.content-txt',
                '.synopsis-txt',
                '[class*="synopsis"]',
                '.movie-synopsis',
                '.synopsis-section .content-txt'
            ]
            
            for selector in synopsis_selectors:
                synopsis_elem = film_soup.select_one(selector)
                if synopsis_elem:
                    synopsis = synopsis_elem.text.strip()
                    synopsis = ' '.join(synopsis.split())
                    print(f"Synopsis trouvé ({len(synopsis)} caractères)")
                    break
            
            # Plateformes
            plateformes = []
            try:
                vod_section = film_soup.select_one('#ovw-products')
                if vod_section:
                    known_platforms = {
                        'netflix': 'Netflix',
                        'prime video': 'Amazon Prime Video',
                        'amazon prime': 'Amazon Prime Video',
                        'disney+': 'Disney+',
                        'disney +': 'Disney+',
                        'canal+': 'Canal+',
                        'canal +': 'Canal+',
                        'canal vod': 'Canal VOD',
                        'apple tv': 'Apple TV+',
                        'ocs': 'OCS',
                        'paramount+': 'Paramount+',
                        'paramount +': 'Paramount+',
                        'mycanal': 'MyCanal'
                    }
                    
                    vod_text = vod_section.get_text(strip=True).lower()
                    print(f"Section VOD trouvée: {vod_text[:100]}...")
                    
                    for platform_key, platform_name in known_platforms.items():
                        if platform_key in vod_text and platform_name not in plateformes:
                            plateformes.append(platform_name)
                            print(f"Plateforme trouvée: {platform_name}")
                else:
                    print("Section VOD non trouvée (#ovw-products)")
            except Exception as e:
                print(f"Erreur lors de la recherche des plateformes: {str(e)}")
            
            # Score de recommandation
            score_reco = None
            try:
                score_elem = film_soup.select_one('.dZ6Qx4goXRfseGsQ2h8g')
                if score_elem:
                    score_reco = score_elem.text.strip()
                    print(f"Score de recommandation trouvé: {score_reco}%")
            except Exception as e:
                print(f"Erreur lors de la recherche du score de recommandation: {str(e)}")
            
            # Date de sortie
            date_sortie = None
            try:
                date_selectors = [
                    '.meta-body-info [class*="date"]',
                    '.meta-body-item:contains("Sortie") span',
                    '[class*="release-date"]',
                    '.date'
                ]
                
                for selector in date_selectors:
                    date_elem = film_soup.select_one(selector)
                    if date_elem:
                        date_sortie = date_elem.text.strip()
                        print(f"Date de sortie trouvée: {date_sortie}")
                        break
            except Exception as e:
                print(f"Erreur lors de la recherche de la date de sortie: {str(e)}")
            
            # Sauvegarder la page pour debug si aucune info trouvée
            if not any([titre, realisateur, note_presse, note_spec]):
                with open('debug_film.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                print("Page sauvegardée pour debug dans debug_film.html")
            
            # Fermer l'onglet et revenir à la liste
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return {
                'titre': titre or 'Non trouvé',
                'realisateur': realisateur or 'Non trouvé',
                'date_sortie': date_sortie or 'Non disponible',
                'synopsis': synopsis or 'Non disponible',
                'note_presse': note_presse or 'Non disponible',
                'note_spectateurs': note_spec or 'Non disponible',
                'score_recommandation': score_reco or 'Non disponible',
                'plateformes': ', '.join(plateformes) if plateformes else 'Non disponible',
                'url': url
            }
            
        except Exception as e:
            print(f"Erreur lors de l'extraction des données: {str(e)}")
            if len(self.driver.window_handles) > 1:
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            return None

    def save_to_csv(self, films, filename='films_allocine.csv'):
        """Sauvegarde les films dans un fichier CSV"""
        if films:
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
                    'Score Recommandation': film['score_recommandation']
                }
                
                available_platforms = (
                    film['plateformes'].split(', ') 
                    if film['plateformes'] != 'Non disponible' 
                    else []
                )
                for platform in platform_columns:
                    film_data[platform] = (
                        'X' if platform in available_platforms else ''
                    )
                
                film_data['URL'] = film['url']
                formatted_films.append(film_data)
            
            df = pd.DataFrame(formatted_films)
            
            columns_order = [
                'Titre', 'Réalisateur', 'Date de sortie', 
                'Synopsis', 'Note Presse', 'Note Spectateurs', 
                'Score Recommandation'
            ] + platform_columns + ['URL']
            
            df = df[columns_order]
            
            try:
                df.to_csv(filename, index=False, encoding='utf-8-sig', sep=';')
                print(f"\n✅ {len(films)} films sauvegardés dans {filename}")
            except PermissionError:
                print(f"\n❌ Impossible de sauvegarder le fichier {filename}")
                print("Le fichier est probablement ouvert dans un autre programme.")
                input("Veuillez fermer le fichier et appuyer sur Entrée pour réessayer...")
                
                try:
                    df.to_csv(filename, index=False, encoding='utf-8-sig', sep=';')
                    print(f"\n✅ {len(films)} films sauvegardés dans {filename}")
                except Exception as e:
                    print(f"\n❌ Échec de la sauvegarde: {str(e)}")
                    return
        else:
            print("\n❌ Aucun film à sauvegarder")

    def close(self):
        """Ferme le navigateur"""
        pass


def is_chrome_running_with_debug_port():
    """Vérifie si Chrome est déjà lancé avec le port de débogage"""
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] == 'chrome.exe':
                cmdline = proc.info['cmdline']
                if cmdline and '--remote-debugging-port=9222' in cmdline:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


def main():
    scraper = AllocineScraper()
    
    try:
        # Vérifier si déjà connecté en allant sur la watchlist
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