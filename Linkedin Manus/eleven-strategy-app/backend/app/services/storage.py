import json
import os
from typing import List, Optional
from app.core.config import settings
from app.models.models import Article, ArticleCreate

class StorageService:
    """Service pour la gestion du stockage des articles en JSON."""
    
    def __init__(self):
        """Initialise le service de stockage."""
        self.articles_file = settings.ARTICLES_FILE
        # Créer le fichier s'il n'existe pas
        if not os.path.exists(self.articles_file):
            with open(self.articles_file, 'w') as f:
                json.dump([], f)
    
    def get_articles(self) -> List[Article]:
        """Récupère tous les articles."""
        try:
            with open(self.articles_file, 'r') as f:
                articles_data = json.load(f)
                return [Article(**article) for article in articles_data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def get_article(self, article_id: int) -> Optional[Article]:
        """Récupère un article par son ID."""
        articles = self.get_articles()
        for article in articles:
            if article.id == article_id:
                return article
        return None
    
    def create_article(self, article_data: ArticleCreate) -> Article:
        """Crée un nouvel article."""
        articles = self.get_articles()
        
        # Générer un nouvel ID
        new_id = 1
        if articles:
            new_id = max(article.id for article in articles) + 1
        
        # Créer le nouvel article
        new_article = Article(
            id=new_id,
            **article_data.dict()
        )
        
        # Ajouter l'article à la liste et sauvegarder
        articles.append(new_article)
        self._save_articles(articles)
        
        return new_article
    
    def update_article(self, article_id: int, update_data: dict) -> Optional[Article]:
        """Met à jour un article existant."""
        articles = self.get_articles()
        updated_article = None
        
        for i, article in enumerate(articles):
            if article.id == article_id:
                # Mettre à jour les champs spécifiés
                article_dict = article.dict()
                article_dict.update({k: v for k, v in update_data.items() if v is not None})
                updated_article = Article(**article_dict)
                articles[i] = updated_article
                break
        
        if updated_article:
            self._save_articles(articles)
            return updated_article
        
        return None
    
    def _save_articles(self, articles: List[Article]) -> None:
        """Sauvegarde la liste des articles dans le fichier JSON."""
        articles_data = [article.dict() for article in articles]
        with open(self.articles_file, 'w') as f:
            json.dump(articles_data, f, indent=2)
