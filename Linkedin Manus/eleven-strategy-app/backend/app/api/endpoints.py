from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.models.models import Article, ArticleUpdate, SummaryRequest, SummaryResponse, PublishRequest, PublishResponse
from app.services.storage import StorageService
from app.services.scraper import ScraperService
from app.services.summarizer import SummarizerService
from app.services.linkedin import LinkedInService

router = APIRouter()
storage_service = StorageService()
scraper_service = ScraperService()
summarizer_service = SummarizerService()
linkedin_service = LinkedInService()

@router.get("/articles", response_model=List[Article])
async def get_articles():
    """Récupère la liste de tous les articles."""
    return storage_service.get_articles()

@router.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: int):
    """Récupère un article spécifique par son ID."""
    article = storage_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return article

@router.post("/collect", response_model=List[Article])
async def collect_articles():
    """Collecte des articles depuis superhuman.ai."""
    articles = await scraper_service.collect_articles()
    return articles

@router.put("/articles/{article_id}", response_model=Article)
async def update_article(article_id: int, article_update: ArticleUpdate):
    """Met à jour un article existant."""
    updated_article = storage_service.update_article(article_id, article_update.dict(exclude_unset=True))
    if not updated_article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    return updated_article

@router.post("/summarize", response_model=SummaryResponse)
async def generate_summary(request: SummaryRequest):
    """Génère un résumé pour un article spécifique."""
    article = storage_service.get_article(request.article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    
    summary = await summarizer_service.generate_summary(request.article_id)
    if not summary:
        raise HTTPException(status_code=500, detail="Erreur lors de la génération du résumé")
    
    return SummaryResponse(article_id=request.article_id, summary=summary)

@router.post("/publish", response_model=PublishResponse)
async def publish_to_linkedin(request: PublishRequest):
    """Publie un résumé d'article sur LinkedIn."""
    article = storage_service.get_article(request.article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article non trouvé")
    
    result = await linkedin_service.publish_to_linkedin(request.article_id, request.summary)
    
    return PublishResponse(
        article_id=request.article_id,
        success=result["success"],
        message=result["message"],
        published_date=result["published_date"]
    )
