"""
Schémas Pydantic pour les requêtes et réponses de l'API.
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class DownloadRequest(BaseModel):
    """Requête pour télécharger des factures."""
    max_invoices: Optional[int] = Field(
        default=None,
        ge=1,
        le=1000,
        description="Nombre maximum de factures à télécharger"
    )
    year: Optional[int] = Field(
        default=None,
        ge=2020,
        le=2030,
        description="Année des factures à télécharger"
    )
    month: Optional[int] = Field(
        default=None,
        ge=1,
        le=12,
        description="Mois des factures à télécharger"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "max_invoices": 50,
                "year": 2024,
                "month": 1
            }
        }


class DownloadResponse(BaseModel):
    """Réponse après téléchargement de factures."""
    success: bool
    message: str
    count: int
    files: List[str] = Field(default_factory=list)


class StatusResponse(BaseModel):
    """Réponse de statut de l'API."""
    status: str
    message: str


class OTPRequest(BaseModel):
    """Requête pour soumettre un code OTP."""
    otp_code: str = Field(
        ...,
        min_length=4,
        max_length=10,
        description="Code OTP reçu (SMS, email ou application)"
    )


class OTPResponse(BaseModel):
    """Réponse après soumission d'un code OTP."""
    success: bool
    message: str
    requires_otp: bool = Field(
        default=False,
        description="Indique si un code OTP est toujours requis"
    )
