"""Pydantic models for the application."""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict
import uuid


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:16]}"


# ---- Auth ----
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=120)
    company: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: EmailStr
    name: str
    company: Optional[str] = None
    picture: Optional[str] = None
    auth_provider: str = "email"  # 'email' | 'google'
    plan: str = "basic"
    plan_renews_at: Optional[str] = None
    gmail_user: Optional[str] = None
    gmail_configured: bool = False
    qes_provider: Optional[str] = None
    qes_credentials: Optional[Dict[str, Any]] = None  # stored per provider
    active_project_id: Optional[str] = None
    gdpr_consent: bool = False
    gdpr_consent_at: Optional[str] = None
    is_developer: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserRegisterV2(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=120)
    company: Optional[str] = None
    gdpr_consent: bool = False


# ---- Project ----
class ProjectIn(BaseModel):
    beneficiar: Optional[str] = ""
    adresa_lucrare: Optional[str] = ""
    localitate: Optional[str] = ""
    judet: Optional[str] = ""
    telefon: Optional[str] = ""
    email: Optional[str] = ""
    osd: Optional[str] = ""
    tip_lucrare: Optional[str] = ""
    numar_contract: Optional[str] = ""
    data_contract: Optional[str] = ""
    proiectant: Optional[str] = ""
    executant: Optional[str] = ""
    verificator_vgd: Optional[str] = ""
    atestat_vgd: Optional[str] = ""
    data_verificare_vgd: Optional[str] = ""
    status_vgd: Optional[str] = ""
    observatii_vgd: Optional[str] = ""
    responsabil_rte: Optional[str] = ""
    autorizatie_rte: Optional[str] = ""
    data_verificare_rte: Optional[str] = ""
    status_rte: Optional[str] = ""
    observatii_rte: Optional[str] = ""
    observatii: Optional[str] = ""


class Project(ProjectIn):
    model_config = ConfigDict(extra="ignore")
    project_id: str
    user_id: str
    completion: float = 0.0
    technical_data: Dict[str, Any] = Field(default_factory=dict)
    calc_results: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class TechnicalDataIn(BaseModel):
    debit_instalat: Optional[float] = None
    presiune_regim: Optional[str] = ""
    diametru_conducta: Optional[str] = ""
    diametru_bransament: Optional[str] = ""
    material_conducta: Optional[str] = ""
    lungime_bransament: Optional[float] = None
    punct_racordare: Optional[str] = ""
    post_reglare: Optional[str] = ""
    contor: Optional[str] = ""
    categorie_consumator: Optional[str] = ""
    traseu: Optional[str] = ""
    observatii_tehnice: Optional[str] = ""
    # overrides (manual) keyed by calc result name
    overrides: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PhotovoltaicDataIn(BaseModel):
    """Date intrare pentru calcul fotovoltaic deep."""
    p_kwp: float = Field(gt=0, description="Putere instalată dorită (kWp)")
    p_panou_wp: Optional[float] = 450
    lungime_dc_m: Optional[float] = 30
    lungime_ac_m: Optional[float] = 15
    monofazat: Optional[bool] = False
    zona_geografica: Optional[str] = "implicit"  # sud / sud_est / centru / nord_est / nord_vest / implicit


# ---- Certifications ----
class CertificationCreate(BaseModel):
    role: str  # 'proiectant' | 'executant' | 'vgd' | 'rte'
    signer_name: str
    document_title: str
    project_id: Optional[str] = None


class Certification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    cert_internal_id: str
    user_id: str
    role: str
    signer_name: str
    document_title: str
    project_id: Optional[str] = None
    hash: str
    created_at: str


# ---- AI assistant ----
class AIQuery(BaseModel):
    message: str


class AuthResponse(BaseModel):
    token: str
    user: User


# ---- Templates ----
class TemplateMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")
    template_id: str
    user_id: str
    name: str
    placeholders: List[str]
    size_bytes: int
    created_at: str


class TemplateCreate(BaseModel):
    name: str


# ---- Stamps ----
class StampMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")
    stamp_id: str
    user_id: str
    name: str
    created_at: str


# ---- Certificates ----
class CertificateMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")
    cert_id: str
    user_id: str
    name: str
    subject: str
    issuer: str
    valid_from: str
    valid_to: str
    created_at: str


# ---- Documents ----
class GenerateRequest(BaseModel):
    template_id: str
    values: Dict[str, str]  # placeholder => value
    stamp_id: Optional[str] = None
    stamp_position: str = "bottom-right"  # top-left, top-right, bottom-left, bottom-right
    stamp_size_cm: float = 4.0
    cert_id: Optional[str] = None
    cert_password: Optional[str] = None
    document_name: Optional[str] = None


class DocumentMeta(BaseModel):
    model_config = ConfigDict(extra="ignore")
    document_id: str
    user_id: str
    template_id: str
    name: str
    stamped: bool = False
    signed: bool = False
    signature_hash: Optional[str] = None
    signature_cert_subject: Optional[str] = None
    created_at: str


class EmailSendRequest(BaseModel):
    document_id: str
    recipients: List[EmailStr]
    subject: str
    body: str


# ---- Subscription / Stripe ----
class CheckoutRequest(BaseModel):
    plan_id: str  # 'pro' or 'enterprise'
    origin_url: str


class PaymentTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    transaction_id: str
    user_id: str
    plan_id: str
    session_id: str
    amount: float
    currency: str
    payment_status: str = "initiated"
    status: str = "open"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
