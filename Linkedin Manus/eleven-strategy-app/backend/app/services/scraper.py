import requests
import feedparser
from bs4 import BeautifulSoup
from typing import List, Optional
from app.models.models import ArticleCreate
from app.services.storage import StorageService
from datetime import datetime

class ScraperService:
    """Service pour le scraping et la collecte d'articles depuis superhuman.ai."""
    
    def __init__(self):
        """Initialise le service de scraping."""
        self.storage_service = StorageService()
        self.superhuman_url = "https://superhuman.ai"
        self.superhuman_rss = "https://superhuman.ai/feed"  # URL fictive, à remplacer par l'URL réelle
    
    async def collect_articles(self) -> List[ArticleCreate]:
        """Collecte des articles depuis superhuman.ai via RSS ou scraping."""
        # Pour le MVP, nous allons d'abord essayer via RSS
        articles = self._collect_via_rss()
        
        # Si le RSS échoue ou ne retourne pas d'articles, essayer le scraping
        if not articles:
            articles = self._collect_via_scraping()
        
        # Sauvegarder les articles collectés
        saved_articles = []
        for article_data in articles:
            saved_article = self.storage_service.create_article(article_data)
            saved_articles.append(saved_article)
        
        return saved_articles
    
    def _collect_via_rss(self) -> List[ArticleCreate]:
        """Collecte des articles via le flux RSS."""
        try:
            feed = feedparser.parse(self.superhuman_rss)
            articles = []
            
            for entry in feed.entries:
                # Vérifier si l'article existe déjà
                existing_articles = self.storage_service.get_articles()
                if any(article.url == entry.link for article in existing_articles):
                    continue
                
                # Extraire le contenu complet de l'article
                content = entry.summary
                if hasattr(entry, 'content'):
                    content = entry.content[0].value
                
                # Créer l'article
                article = ArticleCreate(
                    title=entry.title,
                    source="superhuman.ai",
                    url=entry.link,
                    content=content,
                    date=datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z").strftime("%Y-%m-%d")
                )
                articles.append(article)
            
            return articles
        except Exception as e:
            print(f"Erreur lors de la collecte via RSS: {e}")
            return []
    
    def _collect_via_scraping(self) -> List[ArticleCreate]:
        """Collecte des articles via scraping."""
        try:
            # Pour le MVP, nous simulons la collecte d'articles
            # Dans une version réelle, nous ferions du scraping sur le site
            
            # Exemple d'articles simulés pour le MVP
            articles = [
                ArticleCreate(
                    title="L'IA révolutionne le marketing digital",
                    source="superhuman.ai",
                    url="https://superhuman.ai/article/1",
                    content="Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
                    date=datetime.now().strftime("%Y-%m-%d")
                ),
                ArticleCreate(
                    title="Nouvelles avancées en apprentissage automatique",
                    source="superhuman.ai",
                    url="https://superhuman.ai/article/2",
                    content="Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
                    date=datetime.now().strftime("%Y-%m-%d")
                ),
                ArticleCreate(
                    title="Comment l'IA transforme la prise de décision",
                    source="superhuman.ai",
                    url="https://superhuman.ai/article/3",
                    content="Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.",
                    date=datetime.now().strftime("%Y-%m-%d")
                )
            ]
            
            # Vérifier si les articles existent déjà
            existing_articles = self.storage_service.get_articles()
            new_articles = []
            
            for article in articles:
                if not any(existing.url == article.url for existing in existing_articles):
                    new_articles.append(article)
            
            return new_articles
        except Exception as e:
            print(f"Erreur lors de la collecte via scraping: {e}")
            return []
