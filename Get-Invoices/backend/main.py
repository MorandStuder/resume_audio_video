"""
Point d'entrée principal de l'API FastAPI pour le téléchargement de factures Amazon.
"""
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from logging.handlers import RotatingFileHandler
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.models.schemas import (
    DownloadRequest,
    DownloadResponse,
    OTPRequest,
    OTPResponse,
    StatusResponse,
)
from backend.services.amazon_downloader import AmazonInvoiceDownloader


class Settings(BaseSettings):
    """Configuration de l'application."""
    amazon_email: str
    amazon_password: str
    download_path: str = "./factures"
    max_invoices: int = 100
    selenium_headless: bool = False
    selenium_timeout: int = 30
    selenium_manual_mode: bool = False  # Mode manuel : laisse le navigateur ouvert pour saisie manuelle
    selenium_browser: str = "chrome"  # "chrome" ou "firefox"
    firefox_profile_path: Optional[str] = None  # Chemin vers le profil Firefox existant (ex: C:\Users\USERNAME\AppData\Roaming\Mozilla\Firefox\Profiles\PROFILENAME)
    selenium_keep_browser_open: bool = False  # Connexion continue : ne pas fermer le navigateur à l'arrêt de l'app

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

    def validate_settings(self) -> None:
        """Valide les paramètres de configuration."""
        errors = []

        # Vérifier que l'email est fourni
        if not self.amazon_email or self.amazon_email == "votre_email@example.com":
            errors.append("AMAZON_EMAIL n'est pas configuré ou utilise la valeur par défaut")

        # Vérifier que le mot de passe est fourni
        if not self.amazon_password or self.amazon_password == "votre_mot_de_passe":
            errors.append("AMAZON_PASSWORD n'est pas configuré ou utilise la valeur par défaut")

        # Vérifier que le navigateur est valide
        if self.selenium_browser not in ["chrome", "firefox"]:
            errors.append(f"SELENIUM_BROWSER doit être 'chrome' ou 'firefox', pas '{self.selenium_browser}'")

        # Vérifier que le timeout est raisonnable
        if self.selenium_timeout < 10 or self.selenium_timeout > 300:
            errors.append(f"SELENIUM_TIMEOUT doit être entre 10 et 300 secondes, pas {self.selenium_timeout}")

        # Vérifier que max_invoices est positif
        if self.max_invoices <= 0:
            errors.append(f"MAX_INVOICES doit être positif, pas {self.max_invoices}")

        # Avertir si Firefox profile est défini mais browser n'est pas firefox
        if self.firefox_profile_path and self.selenium_browser != "firefox":
            errors.append(
                f"FIREFOX_PROFILE_PATH est défini mais SELENIUM_BROWSER='{self.selenium_browser}'. "
                "Le profil Firefox sera ignoré."
            )

        if errors:
            error_msg = "Erreurs de configuration détectées:\n" + "\n".join(f"  - {err}" for err in errors)
            raise ValueError(error_msg)


# Créer le dossier logs s'il n'existe pas
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configuration du logging avec fichier et console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        # Handler pour fichier avec rotation
        RotatingFileHandler(
            log_dir / "app.log",
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        ),
        # Handler pour console
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Chargement des paramètres
try:
    settings = Settings()
    settings.validate_settings()
    logger.info("Configuration chargée et validée avec succès")
except ValueError as e:
    logger.error(f"Erreur de configuration: {e}")
    logger.error("Veuillez vérifier votre fichier .env à la racine du projet")
    raise
except Exception as e:
    logger.error(f"Erreur lors du chargement de la configuration: {e}")
    logger.error("Assurez-vous que le fichier .env existe à la racine du projet")
    raise

# Instance globale du downloader
downloader: Optional[AmazonInvoiceDownloader] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Gestionnaire du cycle de vie de l'application.
    Remplace les event handlers startup/shutdown dépréciés.
    """
    global downloader
    # Startup
    try:
        logger.info("Initialisation du téléchargeur Amazon...")
        downloader = AmazonInvoiceDownloader(
            email=settings.amazon_email,
            password=settings.amazon_password,
            download_path=settings.download_path,
            headless=settings.selenium_headless,
            timeout=settings.selenium_timeout,
            manual_mode=settings.selenium_manual_mode,
            browser=settings.selenium_browser,
            firefox_profile_path=settings.firefox_profile_path,
            keep_browser_open=settings.selenium_keep_browser_open,
        )
        logger.info("Téléchargeur Amazon initialisé avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du téléchargeur: {str(e)}")
        import traceback
        logger.debug(traceback.format_exc())
        downloader = None

    yield

    # Shutdown
    if downloader:
        await downloader.close()
        logger.info("Téléchargeur Amazon fermé")


# Initialisation de l'application
app = FastAPI(
    title="Amazon Invoice Downloader API",
    description="API pour télécharger automatiquement les factures Amazon",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=StatusResponse)
async def root() -> StatusResponse:
    """Endpoint de statut de l'API."""
    return StatusResponse(
        status="ok",
        message="API Amazon Invoice Downloader opérationnelle"
    )


@app.get("/api/debug")
async def debug_info() -> dict:
    """Endpoint de debug pour diagnostiquer les problèmes."""
    debug_info = {
        "downloader_initialized": downloader is not None,
        "settings_loaded": settings is not None,
        "has_email": bool(settings.amazon_email) if settings else False,
        "has_password": bool(settings.amazon_password) if settings else False,
    }
    
    if downloader:
        try:
            debug_info["driver_initialized"] = downloader.driver is not None
            debug_info["2fa_required"] = downloader.is_2fa_required()
        except Exception as e:
            debug_info["driver_error"] = str(e)
    
    return debug_info


@app.post("/api/download", response_model=DownloadResponse)
async def download_invoices(
    request: DownloadRequest,
    otp_code: Optional[str] = None
) -> DownloadResponse:
    """
    Télécharge les factures Amazon.
    
    Args:
        request: Paramètres de téléchargement (nombre, période, etc.)
        otp_code: Code OTP pour la 2FA (optionnel)
    
    Returns:
        Réponse avec le nombre de factures téléchargées ou demande de code OTP
    """
    if not downloader:
        raise HTTPException(
            status_code=503,
            detail="Le téléchargeur n'est pas initialisé"
        )
    
    try:
        logger.info(f"Démarrage du téléchargement avec paramètres: max_invoices={request.max_invoices} year={request.year} month={request.month}, otp_code: {'fourni' if otp_code else 'non fourni'}")
        
        result = await downloader.download_invoices(
            max_invoices=request.max_invoices or settings.max_invoices,
            year=request.year,
            month=request.month,
            otp_code=otp_code
        )
        
        return DownloadResponse(
            success=True,
            message=f"{result['count']} facture(s) téléchargée(s)",
            count=result["count"],
            files=result.get("files", [])
        )
    
    except Exception as e:
        import traceback
        error_message = str(e)
        error_traceback = traceback.format_exc()
        logger.error("Erreur lors du téléchargement: %s", error_message)
        logger.debug("Traceback: %s", error_traceback)

        if "Code 2FA requis" in error_message or (downloader and downloader.is_2fa_required()):
            raise HTTPException(
                status_code=401,
                detail="Code 2FA requis - utilisez /api/submit-otp pour fournir le code"
            )

        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du téléchargement: {error_message}"
        )


@app.get("/api/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """Retourne le statut du téléchargeur."""
    if not downloader:
        return StatusResponse(
            status="error",
            message="Le téléchargeur n'est pas initialisé"
        )
    
    try:
        # Vérifier si un code 2FA est requis
        if downloader.is_2fa_required():
            return StatusResponse(
                status="otp_required",
                message="Code 2FA requis - veuillez fournir le code OTP"
            )
        
        return StatusResponse(
            status="ready",
            message="Le téléchargeur est prêt"
        )
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du statut: {str(e)}")
        return StatusResponse(
            status="error",
            message=f"Erreur lors de la vérification du statut: {str(e)}"
        )


@app.post("/api/submit-otp", response_model=OTPResponse)
async def submit_otp(request: OTPRequest) -> OTPResponse:
    """
    Soumet un code OTP pour l'authentification à deux facteurs.
    
    Args:
        request: Requête contenant le code OTP
    
    Returns:
        Réponse indiquant si le code est accepté
    """
    if not downloader:
        raise HTTPException(
            status_code=503,
            detail="Le téléchargeur n'est pas initialisé"
        )
    
    try:
        logger.info("Soumission du code OTP...")
        
        # Essayer de soumettre le code OTP
        success = await downloader.submit_otp(request.otp_code)
        
        if success:
            # Vérifier si la connexion est maintenant réussie
            still_requires = downloader.is_2fa_required()
            return OTPResponse(
                success=True,
                message="Code OTP accepté" if not still_requires else "Code OTP accepté, mais 2FA toujours requis",
                requires_otp=still_requires
            )
        else:
            return OTPResponse(
                success=False,
                message="Code OTP incorrect ou expiré",
                requires_otp=True
            )
    
    except Exception as e:
        logger.error(f"Erreur lors de la soumission du code OTP: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la soumission du code OTP: {str(e)}"
        )


@app.get("/api/check-2fa", response_model=OTPResponse)
async def check_2fa() -> OTPResponse:
    """
    Vérifie si un code 2FA est requis.
    
    Returns:
        Réponse indiquant si un code 2FA est requis
    """
    if not downloader:
        raise HTTPException(
            status_code=503,
            detail="Le téléchargeur n'est pas initialisé"
        )
    
    requires_otp = downloader.is_2fa_required()
    
    return OTPResponse(
        success=not requires_otp,
        message="Code 2FA requis" if requires_otp else "Aucun code 2FA requis",
        requires_otp=requires_otp
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

