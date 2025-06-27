from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Article(BaseModel):
    """Modèle de données pour un article."""
    id: int
    title: str
    source: str
    url: str
    content: str
    date: str
    rating: int = 0
    summary: Optional[str] = None
    published: bool = False
    published_date: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "title": "L'IA révolutionne le marketing digital",
                "source": "superhuman.ai",
                "url": "https://superhuman.ai/article/1",
                "content": "Lorem ipsum dolor sit amet, consectetur adipiscing elit...",
                "date": "2025-04-20",
                "rating": 4,
                "summary": "L'IA transforme radicalement les stratégies marketing. Les entreprises adoptent des solutions automatisées. Les résultats montrent une efficacité accrue.",
                "published": False,
                "published_date": None
            }
        }

class ArticleCreate(BaseModel):
    """Modèle pour la création d'un article."""
    title: str
    source: str
    url: str
    content: str
    date: str

class ArticleUpdate(BaseModel):
    """Modèle pour la mise à jour d'un article."""
    rating: Optional[int] = None
    summary: Optional[str] = None
    published: Optional[bool] = None
    published_date: Optional[str] = None

class SummaryRequest(BaseModel):
    """Modèle pour la demande de génération de résumé."""
    article_id: int

class SummaryResponse(BaseModel):
    """Modèle pour la réponse de génération de résumé."""
    article_id: int
    summary: str

class PublishRequest(BaseModel):
    """Modèle pour la demande de publication sur LinkedIn."""
    article_id: int
    summary: str

class PublishResponse(BaseModel):
    """Modèle pour la réponse de publication sur LinkedIn."""
    article_id: int
    success: bool
    message: str
    published_date: Optional[str] = None
