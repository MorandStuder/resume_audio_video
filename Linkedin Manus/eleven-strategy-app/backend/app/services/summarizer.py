import openai
from typing import Optional
from app.core.config import settings
from app.services.storage import StorageService

class SummarizerService:
    """Service pour la génération de résumés d'articles via l'API OpenAI."""
    
    def __init__(self):
        """Initialise le service de génération de résumés."""
        self.storage_service = StorageService()
        openai.api_key = settings.OPENAI_API_KEY
    
    async def generate_summary(self, article_id: int) -> Optional[str]:
        """Génère un résumé pour un article spécifique."""
        # Récupérer l'article
        article = self.storage_service.get_article(article_id)
        if not article:
            return None
        
        try:
            # Pour le MVP, nous générons un résumé de 3 phrases
            prompt = f"""
            Voici un article sur l'IA et les innovations technologiques:
            
            Titre: {article.title}
            
            Contenu: {article.content}
            
            Génère un résumé concis en exactement 3 phrases pour LinkedIn. 
            Le résumé doit être professionnel et captivant pour attirer l'attention des professionnels.
            """
            
            # Appel à l'API OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Tu es un expert en marketing digital spécialisé dans la création de résumés concis et percutants pour LinkedIn."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            # Extraire le résumé généré
            summary = response.choices[0].message.content.strip()
            
            # Mettre à jour l'article avec le résumé généré
            self.storage_service.update_article(article_id, {"summary": summary})
            
            return summary
        
        except Exception as e:
            print(f"Erreur lors de la génération du résumé: {e}")
            
            # Pour le MVP, en cas d'erreur, générer un résumé par défaut
            default_summary = f"Cet article traite de {article.title}. Il aborde des concepts importants dans le domaine de l'IA et des innovations technologiques. Il est recommandé pour les professionnels intéressés par ce sujet."
            
            # Mettre à jour l'article avec le résumé par défaut
            self.storage_service.update_article(article_id, {"summary": default_summary})
            
            return default_summary
