"""Main FastAPI server for the Romanian gas pipes engineering DOCX platform."""
import os
import io
import uuid
import base64
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Any, Dict

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from db import db
from models import (
    User, UserLogin, UserRegister, UserRegisterV2, AuthResponse,
    TemplateMeta, StampMeta, CertificateMeta,
    GenerateRequest, DocumentMeta, EmailSendRequest,
    CheckoutRequest, PaymentTransaction, new_id,
    ProjectIn, Project, TechnicalDataIn, PhotovoltaicDataIn,
    CertificationCreate, Certification, AIQuery,
)
from auth import (
    hash_password, verify_password, create_jwt,
    fetch_emergent_session, get_current_user,
)
from docx_processor import extract_placeholders, replace_placeholders, insert_stamp
from signing import parse_p12, sign_document
from email_sender import send_email_with_attachment
import qes_provider
import plans as plans_module
import calc_engine
import photovoltaic
import ai_assistant
import ai_developer
import industries as industries_module
import system_templates
import pdf_export
import github_push
import handoff as handoff_module
import verification as verification_module
import payment_accounts as pay_accounts
import forum as forum_module
import project_lifecycle as lifecycle
import company_profile as company_module
import hashlib

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="StampDoc Romania API")
api = APIRouter(prefix="/api")

# Developer accounts — lifetime access, AI Developer panel enabled
DEVELOPER_EMAILS = {"dragosserban95@gmail.com"}


def _is_developer_email(email: str) -> bool:
    return (email or "").lower() in DEVELOPER_EMAILS


def _user_from_doc(doc: dict) -> User:
    """Construct a User model, computing the gmail_configured boolean and stripping secrets."""
    d = {k: v for k, v in doc.items() if k not in ("_id", "password_hash", "gmail_app_password", "qes_credentials")}
    d["gmail_configured"] = bool(doc.get("gmail_user") and doc.get("gmail_app_password"))
    return User(**d)

# ----------- Pricing plans — see plans.py for catalog -----------
PLANS = {p["id"]: {"name": p["name"], "amount": float(p["price_eur"]), "currency": p["currency"], "documents_per_month": p["documents_per_month"]} for p in plans_module.PLANS.values() if not p.get("internal")}


def _set_session_cookie(response: Response, token: str):
    """Set the auth token as an httpOnly cookie. Secure + SameSite=None (cross-site OK)."""
    max_age = int(os.environ.get("JWT_EXPIRE_HOURS", "168")) * 3600
    response.set_cookie(
        key="session_token", value=token,
        httponly=True, secure=True, samesite="none", path="/",
        max_age=max_age,
    )


# ====================== AUTH ======================
@api.post("/auth/register", response_model=AuthResponse)
async def register(payload: UserRegisterV2, response: Response):
    existing = await db.users.find_one({"email": payload.email.lower()}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email-ul este deja înregistrat")
    if not payload.gdpr_consent:
        raise HTTPException(status_code=400, detail="Trebuie să acceptați Politica de Confidențialitate și GDPR pentru a continua")
    user_id = new_id("usr_")
    is_dev = _is_developer_email(payload.email)
    user_doc = {
        "user_id": user_id,
        "email": payload.email.lower(),
        "name": payload.name,
        "company": payload.company,
        "picture": None,
        "auth_provider": "email",
        "plan": "developer" if is_dev else plans_module.DEFAULT_PLAN,
        "plan_renews_at": None,
        "gdpr_consent": True,
        "gdpr_consent_at": datetime.now(timezone.utc).isoformat(),
        "is_developer": is_dev,
        "password_hash": hash_password(payload.password),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(user_doc)
    await db.action_logs.insert_one({
        "log_id": new_id("log_"), "user_id": user_id, "action": "register",
        "meta": {"email": user_doc["email"]}, "created_at": user_doc["created_at"],
    })
    token = create_jwt(user_id)
    _set_session_cookie(response, token)
    return AuthResponse(token=token, user=_user_from_doc(user_doc))


@api.post("/auth/login", response_model=AuthResponse)
async def login(payload: UserLogin, response: Response):
    user_doc = await db.users.find_one({"email": payload.email.lower()})
    if not user_doc or not user_doc.get("password_hash"):
        raise HTTPException(status_code=401, detail="Credențiale invalide")
    if not verify_password(payload.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Credențiale invalide")
    # Auto-upgrade developer accounts
    if _is_developer_email(user_doc.get("email", "")) and not user_doc.get("is_developer"):
        await db.users.update_one({"user_id": user_doc["user_id"]}, {"$set": {"is_developer": True, "plan": "developer"}})
        user_doc["is_developer"] = True
        user_doc["plan"] = "developer"
    await db.action_logs.insert_one({
        "log_id": new_id("log_"), "user_id": user_doc["user_id"], "action": "login",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    token = create_jwt(user_doc["user_id"])
    _set_session_cookie(response, token)
    return AuthResponse(token=token, user=_user_from_doc(user_doc))


@api.post("/auth/google/session")
async def google_session(payload: dict, response: Response):
    """Exchange Emergent session_id for our session_token cookie + user."""
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    data = await fetch_emergent_session(session_id)
    email = data["email"].lower()
    user_doc = await db.users.find_one({"email": email}, {"_id": 0})
    if not user_doc:
        user_id = new_id("usr_")
        is_dev = _is_developer_email(email)
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": data.get("name", email.split("@")[0]),
            "company": None,
            "picture": data.get("picture"),
            "auth_provider": "google",
            "plan": "developer" if is_dev else plans_module.DEFAULT_PLAN,
            "plan_renews_at": None,
            "gdpr_consent": True,
            "gdpr_consent_at": datetime.now(timezone.utc).isoformat(),
            "is_developer": is_dev,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.users.insert_one(dict(user_doc))
    elif _is_developer_email(email) and not user_doc.get("is_developer"):
        # Auto-upgrade existing user if they're now a developer
        await db.users.update_one(
            {"email": email},
            {"$set": {"is_developer": True, "plan": "developer"}},
        )
        user_doc["is_developer"] = True
        user_doc["plan"] = "developer"
    session_token = data["session_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": user_doc["user_id"],
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    response.set_cookie(
        key="session_token", value=session_token,
        httponly=True, secure=True, samesite="none", path="/",
        max_age=7 * 24 * 3600,
    )
    return {"user": user_doc, "token": session_token}


@api.get("/auth/me", response_model=User)
async def me(user: User = Depends(get_current_user)):
    return user


@api.post("/auth/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_many({"session_token": token})
    response.delete_cookie("session_token", path="/")
    return {"ok": True}


# ====================== USER SETTINGS ======================
@api.patch("/users/me", response_model=User)
async def update_me(payload: dict, user: User = Depends(get_current_user)):
    """Update user profile / Gmail / QES settings."""
    allowed = {"name", "company", "gmail_user", "gmail_app_password", "qes_provider"}
    updates = {k: v for k, v in payload.items() if k in allowed}
    if not updates:
        raise HTTPException(status_code=400, detail="Nicio modificare validă")
    await db.users.update_one({"user_id": user.user_id}, {"$set": updates})
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
    return _user_from_doc(user_doc)


@api.get("/users/me/email-config")
async def email_config(user: User = Depends(get_current_user)):
    """Return whether Gmail is configured (never expose the password)."""
    doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "gmail_user": 1, "gmail_app_password": 1})
    configured = bool(doc and doc.get("gmail_user") and doc.get("gmail_app_password"))
    return {"configured": configured, "gmail_user": doc.get("gmail_user") if doc else None}


# ====================== QES PROVIDERS ======================
@api.get("/qes/providers")
async def list_qes_providers(user: User = Depends(get_current_user)):
    return qes_provider.list_providers()


# ====================== TEMPLATES ======================
@api.post("/templates/upload", response_model=TemplateMeta)
async def upload_template(file: UploadFile = File(...), name: Optional[str] = Form(None), user: User = Depends(get_current_user)):
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Se acceptă doar fișiere .docx")
    data = await file.read()
    placeholders = extract_placeholders(data)
    template_id = new_id("tpl_")
    doc = {
        "template_id": template_id,
        "user_id": user.user_id,
        "name": name or file.filename,
        "placeholders": placeholders,
        "size_bytes": len(data),
        "data_b64": base64.b64encode(data).decode("ascii"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.templates.insert_one(doc)
    return TemplateMeta(**{k: v for k, v in doc.items() if k != "data_b64"})


@api.get("/templates", response_model=List[TemplateMeta])
async def list_templates(user: User = Depends(get_current_user)):
    cursor = db.templates.find({"user_id": user.user_id}, {"_id": 0, "data_b64": 0}).sort("created_at", -1)
    docs = await cursor.to_list(500)
    return [TemplateMeta(**d) for d in docs]


@api.get("/templates/{template_id}", response_model=TemplateMeta)
async def get_template(template_id: str, user: User = Depends(get_current_user)):
    doc = await db.templates.find_one({"template_id": template_id, "user_id": user.user_id}, {"_id": 0, "data_b64": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Șablon negăsit")
    return TemplateMeta(**doc)


@api.delete("/templates/{template_id}")
async def delete_template(template_id: str, user: User = Depends(get_current_user)):
    res = await db.templates.delete_one({"template_id": template_id, "user_id": user.user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Șablon negăsit")
    return {"ok": True}


# ====================== STAMPS ======================
@api.post("/stamps/upload", response_model=StampMeta)
async def upload_stamp(file: UploadFile = File(...), name: Optional[str] = Form(None), user: User = Depends(get_current_user)):
    ct = (file.content_type or "").lower()
    if not (ct.startswith("image/") or file.filename.lower().endswith((".png", ".jpg", ".jpeg"))):
        raise HTTPException(status_code=400, detail="Se acceptă doar imagini PNG/JPG")
    data = await file.read()
    # Validate it's a real image
    try:
        from PIL import Image
        Image.open(io.BytesIO(data)).verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Imagine invalidă sau coruptă")
    stamp_id = new_id("stm_")
    doc = {
        "stamp_id": stamp_id,
        "user_id": user.user_id,
        "name": name or file.filename,
        "data_b64": base64.b64encode(data).decode("ascii"),
        "content_type": ct or "image/png",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.stamps.insert_one(doc)
    return StampMeta(**{k: v for k, v in doc.items() if k not in ("data_b64", "content_type")})


@api.get("/stamps", response_model=List[StampMeta])
async def list_stamps(user: User = Depends(get_current_user)):
    cursor = db.stamps.find({"user_id": user.user_id}, {"_id": 0, "data_b64": 0}).sort("created_at", -1)
    return [StampMeta(**d) for d in await cursor.to_list(500)]


@api.get("/stamps/{stamp_id}/image")
async def get_stamp_image(stamp_id: str, user: User = Depends(get_current_user)):
    doc = await db.stamps.find_one({"stamp_id": stamp_id, "user_id": user.user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Ștampilă negăsită")
    data = base64.b64decode(doc["data_b64"])
    return Response(content=data, media_type=doc.get("content_type", "image/png"))


@api.delete("/stamps/{stamp_id}")
async def delete_stamp(stamp_id: str, user: User = Depends(get_current_user)):
    res = await db.stamps.delete_one({"stamp_id": stamp_id, "user_id": user.user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ștampilă negăsită")
    return {"ok": True}


# ====================== CERTIFICATES ======================
@api.post("/certificates/upload", response_model=CertificateMeta)
async def upload_certificate(
    file: UploadFile = File(...),
    password: str = Form(""),
    name: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
):
    if not file.filename.lower().endswith((".p12", ".pfx")):
        raise HTTPException(status_code=400, detail="Se acceptă doar fișiere .p12 / .pfx")
    data = await file.read()
    try:
        info = parse_p12(data, password)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Certificat invalid sau parolă greșită: {e}")

    cert_id = new_id("crt_")
    doc = {
        "cert_id": cert_id,
        "user_id": user.user_id,
        "name": name or file.filename,
        "subject": info["subject"],
        "issuer": info["issuer"],
        "valid_from": info["valid_from"],
        "valid_to": info["valid_to"],
        "data_b64": base64.b64encode(data).decode("ascii"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.certificates.insert_one(doc)
    return CertificateMeta(**{k: v for k, v in doc.items() if k != "data_b64"})


@api.get("/certificates", response_model=List[CertificateMeta])
async def list_certificates(user: User = Depends(get_current_user)):
    cursor = db.certificates.find({"user_id": user.user_id}, {"_id": 0, "data_b64": 0}).sort("created_at", -1)
    return [CertificateMeta(**d) for d in await cursor.to_list(500)]


@api.delete("/certificates/{cert_id}")
async def delete_certificate(cert_id: str, user: User = Depends(get_current_user)):
    res = await db.certificates.delete_one({"cert_id": cert_id, "user_id": user.user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Certificat negăsit")
    return {"ok": True}


# ====================== DOCUMENT GENERATION ======================
async def _enforce_quota(user: User) -> None:
    """Free plan: 5 docs total. Pro/Enterprise: monthly cap."""
    if user.plan == "free":
        count = await db.documents.count_documents({"user_id": user.user_id})
        if count >= 5:
            raise HTTPException(status_code=402, detail="Limita planului Free atinsă. Vă rugăm să faceți upgrade.")
    else:
        plan_cfg = PLANS.get(user.plan)
        if plan_cfg:
            month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
            count = await db.documents.count_documents({"user_id": user.user_id, "created_at": {"$gte": month_start}})
            if count >= plan_cfg["documents_per_month"]:
                raise HTTPException(status_code=402, detail="Limita lunară atinsă pentru planul curent.")


@api.post("/documents/generate", response_model=DocumentMeta)
async def generate_document(req: GenerateRequest, user: User = Depends(get_current_user)):
    await _enforce_quota(user)

    tpl = await db.templates.find_one({"template_id": req.template_id, "user_id": user.user_id})
    if not tpl:
        raise HTTPException(status_code=404, detail="Șablon negăsit")
    docx_bytes = base64.b64decode(tpl["data_b64"])

    # Replace placeholders
    docx_bytes = replace_placeholders(docx_bytes, req.values)

    stamped = False
    if req.stamp_id:
        stamp = await db.stamps.find_one({"stamp_id": req.stamp_id, "user_id": user.user_id})
        if not stamp:
            raise HTTPException(status_code=404, detail="Ștampilă negăsită")
        stamp_bytes = base64.b64decode(stamp["data_b64"])
        docx_bytes = insert_stamp(docx_bytes, stamp_bytes, req.stamp_position, req.stamp_size_cm)
        stamped = True

    signed = False
    signature_b64: Optional[str] = None
    signature_info: Optional[dict] = None
    if req.cert_id:
        cert = await db.certificates.find_one({"cert_id": req.cert_id, "user_id": user.user_id})
        if not cert:
            raise HTTPException(status_code=404, detail="Certificat negăsit")
        try:
            sig_bytes, info = sign_document(docx_bytes, base64.b64decode(cert["data_b64"]), req.cert_password or "")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Eroare la semnare: {e}")
        signature_b64 = base64.b64encode(sig_bytes).decode("ascii")
        signature_info = info
        signed = True

    doc_id = new_id("doc_")
    base_name = (req.document_name or tpl["name"]).rsplit(".docx", 1)[0]
    final_name = f"{base_name}.docx"

    doc = {
        "document_id": doc_id,
        "user_id": user.user_id,
        "template_id": req.template_id,
        "name": final_name,
        "stamped": stamped,
        "signed": signed,
        "signature_hash": signature_info["sha256"] if signature_info else None,
        "signature_cert_subject": signature_info["subject"] if signature_info else None,
        "data_b64": base64.b64encode(docx_bytes).decode("ascii"),
        "signature_b64": signature_b64,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.documents.insert_one(doc)
    return DocumentMeta(**{k: v for k, v in doc.items() if k not in ("data_b64", "signature_b64")})


@api.get("/documents", response_model=List[DocumentMeta])
async def list_documents(user: User = Depends(get_current_user)):
    cursor = db.documents.find({"user_id": user.user_id}, {"_id": 0, "data_b64": 0, "signature_b64": 0}).sort("created_at", -1)
    return [DocumentMeta(**d) for d in await cursor.to_list(500)]


@api.get("/documents/{document_id}/download")
async def download_document(document_id: str, user: User = Depends(get_current_user)):
    doc = await db.documents.find_one({"document_id": document_id, "user_id": user.user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document negăsit")
    data = base64.b64decode(doc["data_b64"])
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{doc["name"]}"'},
    )


@api.get("/documents/{document_id}/signature")
async def download_signature(document_id: str, user: User = Depends(get_current_user)):
    doc = await db.documents.find_one({"document_id": document_id, "user_id": user.user_id})
    if not doc or not doc.get("signature_b64"):
        raise HTTPException(status_code=404, detail="Semnătură negăsită")
    data = base64.b64decode(doc["signature_b64"])
    name = doc["name"].rsplit(".docx", 1)[0] + ".p7s"
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/pkcs7-signature",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


@api.delete("/documents/{document_id}")
async def delete_document(document_id: str, user: User = Depends(get_current_user)):
    res = await db.documents.delete_one({"document_id": document_id, "user_id": user.user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document negăsit")
    return {"ok": True}


# ====================== EMAIL ======================
@api.post("/documents/email")
async def email_document(req: EmailSendRequest, user: User = Depends(get_current_user)):
    doc = await db.documents.find_one({"document_id": req.document_id, "user_id": user.user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document negăsit")
    data = base64.b64decode(doc["data_b64"])
    extras = []
    if doc.get("signature_b64"):
        sig_name = doc["name"].rsplit(".docx", 1)[0] + ".p7s"
        extras.append((sig_name, base64.b64decode(doc["signature_b64"]), "application/pkcs7-signature"))

    # Fetch user's Gmail credentials
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "gmail_user": 1, "gmail_app_password": 1})
    gmail_user = (user_doc or {}).get("gmail_user", "") or ""
    gmail_pass = (user_doc or {}).get("gmail_app_password", "") or ""

    result = send_email_with_attachment(
        gmail_user=gmail_user,
        gmail_password=gmail_pass,
        recipients=req.recipients,
        subject=req.subject,
        body=req.body,
        attachment_name=doc["name"],
        attachment_bytes=data,
        extra_attachments=extras,
    )
    await db.email_logs.insert_one({
        "log_id": new_id("log_"),
        "user_id": user.user_id,
        "document_id": req.document_id,
        "recipients": req.recipients,
        "subject": req.subject,
        "ok": result.get("ok", False),
        "error": result.get("error"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    if not result.get("ok"):
        raise HTTPException(status_code=500, detail=result.get("error", "Eroare la trimitere"))
    return {"ok": True}


# ====================== STRIPE PAYMENTS ======================
def _stripe_client(request: Request) -> StripeCheckout:
    api_key = os.environ.get("STRIPE_API_KEY", "")
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    return StripeCheckout(api_key=api_key, webhook_url=webhook_url)


@api.get("/plans")
async def list_plans_v2():
    return plans_module.public_plans()


@api.post("/payments/checkout")
async def create_checkout(req: CheckoutRequest, request: Request, user: User = Depends(get_current_user)):
    plan = PLANS.get(req.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Plan invalid")
    success_url = f"{req.origin_url.rstrip('/')}/dashboard?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{req.origin_url.rstrip('/')}/pricing"

    sc = _stripe_client(request)
    co_req = CheckoutSessionRequest(
        amount=float(plan["amount"]),
        currency=plan["currency"],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": user.user_id, "plan_id": req.plan_id, "source": "subscription"},
    )
    session = await sc.create_checkout_session(co_req)

    txn = {
        "transaction_id": new_id("txn_"),
        "user_id": user.user_id,
        "plan_id": req.plan_id,
        "session_id": session.session_id,
        "amount": float(plan["amount"]),
        "currency": plan["currency"],
        "payment_status": "initiated",
        "status": "open",
        "metadata": {"user_id": user.user_id, "plan_id": req.plan_id},
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.payment_transactions.insert_one(txn)
    return {"url": session.url, "session_id": session.session_id}


@api.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request, user: User = Depends(get_current_user)):
    sc = _stripe_client(request)
    status = await sc.get_checkout_status(session_id)
    txn = await db.payment_transactions.find_one({"session_id": session_id, "user_id": user.user_id}, {"_id": 0})
    if not txn:
        raise HTTPException(status_code=404, detail="Tranzacție negăsită")

    # Idempotent activation
    if status.payment_status == "paid" and txn["payment_status"] != "paid":
        plan_id = txn["plan_id"]
        renew_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": {"plan": plan_id, "plan_renews_at": renew_at}},
        )
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": "paid", "status": status.status, "completed_at": datetime.now(timezone.utc).isoformat()}},
        )
    else:
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": status.payment_status, "status": status.status}},
        )
    return {
        "payment_status": status.payment_status,
        "status": status.status,
        "amount_total": status.amount_total,
        "currency": status.currency,
    }


@api.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    sc = _stripe_client(request)
    body = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    try:
        event = await sc.handle_webhook(body, sig)
    except Exception as e:
        logger.warning(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook error")
    if event.payment_status == "paid":
        await db.payment_transactions.update_one(
            {"session_id": event.session_id},
            {"$set": {"payment_status": "paid"}},
        )
        meta = event.metadata or {}
        user_id = meta.get("user_id")
        plan_id = meta.get("plan_id")
        if user_id and plan_id:
            renew_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"plan": plan_id, "plan_renews_at": renew_at}},
            )
    return {"received": True}


# ====================== PROJECTS ======================
async def _get_active_project(user_id: str) -> dict:
    """Return active project for user, creating one if none exist."""
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0, "active_project_id": 1})
    active_id = (user_doc or {}).get("active_project_id")
    if active_id:
        proj = await db.projects.find_one({"project_id": active_id, "user_id": user_id})
        if proj:
            proj.pop("_id", None)
            return proj
    # fallback: first non-archived
    proj = await db.projects.find_one({"user_id": user_id, "archived": {"$ne": True}}, sort=[("created_at", 1)])
    if proj:
        proj.pop("_id", None)
        await db.users.update_one({"user_id": user_id}, {"$set": {"active_project_id": proj["project_id"]}})
        return proj
    # create default
    return await _create_project_doc(user_id, name="Proiect implicit")


async def _create_project_doc(user_id: str, name: str = "Proiect nou", description: str = "", industry: str = None, subdomain: str = None) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    proj_id = new_id("prj_")
    doc = {
        "project_id": proj_id, "user_id": user_id,
        "name": name, "description": description,
        "industry": industry or industries_module.DEFAULT_INDUSTRY,
        "subdomain": subdomain or industries_module.DEFAULT_SUBDOMAIN,
        "beneficiar": "", "adresa_lucrare": "", "localitate": "", "judet": "",
        "telefon": "", "email": "", "osd": "", "tip_lucrare": "",
        "numar_contract": "", "data_contract": "", "proiectant": "",
        "executant": "",
        "verificator_vgd": "", "atestat_vgd": "", "data_verificare_vgd": "", "status_vgd": "", "observatii_vgd": "",
        "responsabil_rte": "", "autorizatie_rte": "", "data_verificare_rte": "", "status_rte": "", "observatii_rte": "",
        "observatii": "",
        "completion": 0.0, "technical_data": {}, "calc_results": {},
        "archived": False,
        "created_at": now, "updated_at": now,
    }
    await db.projects.insert_one(doc)
    await db.users.update_one({"user_id": user_id}, {"$set": {"active_project_id": proj_id}})
    doc.pop("_id", None)
    return doc


# Backwards-compat name
_get_or_create_default_project = _get_active_project


REQUIRED_PROJECT_FIELDS = ["beneficiar", "adresa_lucrare", "localitate", "judet", "telefon", "email", "osd", "tip_lucrare", "numar_contract", "data_contract", "proiectant", "executant", "verificator_vgd", "responsabil_rte"]
EXTENDED_PROJECT_FIELDS = REQUIRED_PROJECT_FIELDS + ["atestat_vgd", "data_verificare_vgd", "status_vgd", "observatii_vgd", "autorizatie_rte", "data_verificare_rte", "status_rte", "observatii_rte", "observatii"]


def _completion(proj: dict) -> float:
    filled = sum(1 for f in REQUIRED_PROJECT_FIELDS if str(proj.get(f) or "").strip())
    return round(100.0 * filled / len(REQUIRED_PROJECT_FIELDS), 1)


def _clean_project(proj: dict) -> dict:
    return {k: v for k, v in proj.items() if k != "_id"}


@api.get("/project")
async def get_project(user: User = Depends(get_current_user)):
    proj = await _get_or_create_default_project(user.user_id)
    proj["completion"] = _completion(proj)
    return _clean_project(proj)


@api.put("/project")
async def update_project(payload: ProjectIn, user: User = Depends(get_current_user)):
    proj = await _get_or_create_default_project(user.user_id)
    updates = payload.model_dump(exclude_none=False)
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    merged = {**proj, **updates}
    updates["completion"] = _completion(merged)
    await db.projects.update_one({"project_id": proj["project_id"]}, {"$set": updates})
    await db.action_logs.insert_one({
        "log_id": new_id("log_"), "user_id": user.user_id, "action": "project.update",
        "created_at": updates["updated_at"],
    })
    proj = await db.projects.find_one({"project_id": proj["project_id"]})
    return _clean_project(proj)


@api.put("/project/technical")
async def update_technical(payload: TechnicalDataIn, user: User = Depends(get_current_user)):
    proj = await _get_or_create_default_project(user.user_id)
    td = payload.model_dump()
    overrides = td.pop("overrides", {}) or {}
    # Compute calculations
    results = calc_engine.calculate(td)
    # Apply overrides
    for k, v in overrides.items():
        if k in results and v not in (None, ""):
            results[k] = {**results[k], "value": v, "status": "override", "explanation": "Valoare suprascrisă manual de utilizator."}
    now = datetime.now(timezone.utc).isoformat()
    await db.projects.update_one(
        {"project_id": proj["project_id"]},
        {"$set": {"technical_data": td, "calc_results": results, "updated_at": now}},
    )
    return {"technical_data": td, "calc_results": results}


@api.post("/project/recalculate")
async def recalc(user: User = Depends(get_current_user)):
    proj = await _get_or_create_default_project(user.user_id)
    td = proj.get("technical_data") or {}
    results = calc_engine.calculate(td)
    await db.projects.update_one({"project_id": proj["project_id"]}, {"$set": {"calc_results": results}})
    return {"calc_results": results}


@api.get("/project/placeholders")
async def project_placeholders(user: User = Depends(get_current_user)):
    """Return all resolved placeholders <name>: value for inserting into documents."""
    proj = await _get_or_create_default_project(user.user_id)
    td = proj.get("technical_data") or {}
    calc = proj.get("calc_results") or {}
    placeholders = {}
    for k in EXTENDED_PROJECT_FIELDS:
        placeholders[k] = str(proj.get(k) or "")
    for k, v in td.items():
        if not isinstance(v, dict):
            placeholders[k] = str(v) if v is not None else ""
    for k, r in calc.items():
        placeholders[k] = str(r.get("value") or "")
    # Adaugă placeholderi fotovoltaici dacă au fost calculați
    pv_data = proj.get("photovoltaic_data") or {}
    pv_results = proj.get("photovoltaic_results") or {}
    if pv_results.get("status") == "ok":
        placeholders.update(photovoltaic.to_placeholders(pv_results))
    for k, v in pv_data.items():
        if not isinstance(v, (dict, list)):
            placeholders[f"fv_input_{k}"] = str(v) if v is not None else ""
    placeholders["data_document"] = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    return placeholders


# ---------------------------------------------------------------------
# PHOTOVOLTAIC (Fotovoltaice — implementare profundă conform ANRE)
# ---------------------------------------------------------------------
@api.post("/photovoltaic/calculate")
async def photovoltaic_calculate(payload: PhotovoltaicDataIn, user: User = Depends(get_current_user)):
    """Rulează lanțul complet de calcul fotovoltaic și salvează rezultatul pe proiect."""
    proj = await _get_or_create_default_project(user.user_id)
    data = payload.model_dump()
    result = photovoltaic.calculate(data)
    now = datetime.now(timezone.utc).isoformat()
    await db.projects.update_one(
        {"project_id": proj["project_id"]},
        {"$set": {"photovoltaic_data": data, "photovoltaic_results": result, "updated_at": now}},
    )
    return {"photovoltaic_data": data, "photovoltaic_results": result}


@api.get("/photovoltaic")
async def photovoltaic_get(user: User = Depends(get_current_user)):
    proj = await _get_or_create_default_project(user.user_id)
    return {
        "photovoltaic_data": proj.get("photovoltaic_data") or {},
        "photovoltaic_results": proj.get("photovoltaic_results") or {},
    }


@api.get("/photovoltaic/categories")
async def photovoltaic_categories():
    """Returnează categoriile ANRE — util pentru UI dropdown."""
    return {
        "categorii": [
            {"cat": "C1", "label": "Prosumator casnic ≤ 10.8 kWp", "p_max": 10.8},
            {"cat": "C2", "label": "Prosumator non-casnic 10.8-27 kWp", "p_max": 27},
            {"cat": "C3", "label": "Producător mic 27-200 kWp", "p_max": 200},
            {"cat": "C4", "label": "Parc FV > 200 kWp", "p_max": None},
        ],
        "zone": list(photovoltaic.IRADIATIE_KWH_M2_AN.keys()),
        "defaults": {
            "p_panou_wp": photovoltaic.PUTERE_PANOU_DEFAULT_WP,
            "voc_panou": photovoltaic.VOC_PANOU_DEFAULT,
            "isc_panou": photovoltaic.ISC_PANOU_DEFAULT,
            "pr": photovoltaic.PR_DEFAULT,
        },
    }


# Multi-project CRUD
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = ""
    industry: Optional[str] = industries_module.DEFAULT_INDUSTRY
    subdomain: Optional[str] = industries_module.DEFAULT_SUBDOMAIN


@api.get("/projects")
async def list_projects(include_archived: bool = False, user: User = Depends(get_current_user)):
    q = {"user_id": user.user_id}
    if not include_archived:
        q["archived"] = {"$ne": True}
    cursor = db.projects.find(q, {"_id": 0, "technical_data": 0, "calc_results": 0}).sort("created_at", -1)
    items = await cursor.to_list(500)
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "active_project_id": 1})
    active_id = (user_doc or {}).get("active_project_id")
    for p in items:
        p["completion"] = _completion(p)
        p["active"] = p["project_id"] == active_id
    return items


@api.post("/projects")
async def create_project(payload: ProjectCreate, user: User = Depends(get_current_user)):
    # Validate industry & subdomain exist and are active
    if payload.industry not in industries_module.INDUSTRIES:
        raise HTTPException(status_code=400, detail=f"Industrie necunoscută: {payload.industry}")
    ind = industries_module.INDUSTRIES[payload.industry]
    if ind.get("status") != "active":
        raise HTTPException(status_code=400, detail=f"Industria '{ind['name']}' nu este încă activă")
    sd_ids = {s["id"] for s in ind.get("subdomains", [])}
    if payload.subdomain not in sd_ids:
        raise HTTPException(status_code=400, detail=f"Subdomeniu necunoscut: {payload.subdomain}")
    doc = await _create_project_doc(user.user_id, name=payload.name, description=payload.description or "",
                                    industry=payload.industry, subdomain=payload.subdomain)
    return doc


@api.post("/projects/{project_id}/activate")
async def activate_project(project_id: str, user: User = Depends(get_current_user)):
    proj = await db.projects.find_one({"project_id": project_id, "user_id": user.user_id}, {"_id": 0})
    if not proj:
        raise HTTPException(status_code=404, detail="Proiect negăsit")
    await db.users.update_one({"user_id": user.user_id}, {"$set": {"active_project_id": project_id}})
    return {"active_project_id": project_id}


@api.post("/projects/{project_id}/archive")
async def archive_project(project_id: str, user: User = Depends(get_current_user)):
    res = await db.projects.update_one({"project_id": project_id, "user_id": user.user_id}, {"$set": {"archived": True}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Proiect negăsit")
    return {"archived": True}


@api.post("/projects/{project_id}/unarchive")
async def unarchive_project(project_id: str, user: User = Depends(get_current_user)):
    res = await db.projects.update_one({"project_id": project_id, "user_id": user.user_id}, {"$set": {"archived": False}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Proiect negăsit")
    return {"archived": False}


@api.delete("/projects/{project_id}")
async def delete_project(project_id: str, user: User = Depends(get_current_user)):
    res = await db.projects.delete_one({"project_id": project_id, "user_id": user.user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Proiect negăsit")
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "active_project_id": 1})
    if (user_doc or {}).get("active_project_id") == project_id:
        next_proj = await db.projects.find_one({"user_id": user.user_id, "archived": {"$ne": True}}, sort=[("created_at", 1)])
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": {"active_project_id": next_proj["project_id"] if next_proj else None}},
        )
    return {"deleted": True}


# ====================== CERTIFICATIONS ======================
@api.post("/certifications", response_model=Certification)
async def create_certification(payload: CertificationCreate, user: User = Depends(get_current_user)):
    if payload.role not in ["proiectant", "executant", "vgd", "rte", "societate"]:
        raise HTTPException(status_code=400, detail="Rol invalid")
    now = datetime.now(timezone.utc).isoformat()
    cid = new_id("cert_")
    payload_str = f"{user.user_id}|{payload.role}|{payload.signer_name}|{payload.document_title}|{now}"
    h = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    doc = {
        "cert_internal_id": cid,
        "user_id": user.user_id,
        "role": payload.role,
        "signer_name": payload.signer_name,
        "document_title": payload.document_title,
        "project_id": payload.project_id,
        "hash": h,
        "created_at": now,
    }
    await db.certifications_internal.insert_one(doc)
    return Certification(**doc)


@api.get("/certifications", response_model=List[Certification])
async def list_certifications(user: User = Depends(get_current_user)):
    cursor = db.certifications_internal.find({"user_id": user.user_id}, {"_id": 0}).sort("created_at", -1)
    docs = await cursor.to_list(500)
    return [Certification(**d) for d in docs]


# ====================== AI ASSISTANT ======================
@api.post("/ai/parse")
async def ai_parse(payload: AIQuery, user: User = Depends(get_current_user)):
    packet = ai_assistant.parse(payload.message)
    await db.action_logs.insert_one({
        "log_id": new_id("log_"), "user_id": user.user_id, "action": "ai.parse",
        "meta": {"message": payload.message[:200], "intent": packet.get("intent")},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return packet


# ====================== VERIFICATION ======================
@api.get("/verification")
async def verify_documentation(user: User = Depends(get_current_user)):
    proj = await _get_or_create_default_project(user.user_id)
    counts = {
        "templates": await db.templates.count_documents({"user_id": user.user_id}),
        "documents": await db.documents.count_documents({"user_id": user.user_id}),
        "stamps": await db.stamps.count_documents({"user_id": user.user_id}),
        "certifications": await db.certifications_internal.count_documents({"user_id": user.user_id}),
    }
    plan_cfg = plans_module.get_plan(user.plan)
    return verification_module.build_report(
        project=proj, counts=counts, plan_name=user.plan, plan_cfg=plan_cfg,
    )


# ====================== AUDIT ======================
APP_PAGES = [
    {"id": "panou", "label": "Panou principal", "route": "/dashboard", "fields": [], "required_handlers": ["fetch_stats"]},
    {"id": "proiect", "label": "Date proiect", "route": "/proiect", "fields": REQUIRED_PROJECT_FIELDS, "required_handlers": ["save", "validate"]},
    {"id": "tehnice", "label": "Date tehnice", "route": "/tehnice", "fields": ["debit_instalat", "presiune_regim", "diametru_conducta", "material_conducta", "lungime_bransament"], "required_handlers": ["save"]},
    {"id": "calcul", "label": "Calcul inteligent", "route": "/calcul", "fields": [], "required_handlers": ["recalculate", "copy_result"]},
    {"id": "templates", "label": "Șabloane", "route": "/templates", "fields": [], "required_handlers": ["upload", "delete"]},
    {"id": "documents", "label": "Documente", "route": "/documents", "fields": [], "required_handlers": ["download", "delete", "email"]},
    {"id": "stamps", "label": "Ștampile", "route": "/stamps", "fields": [], "required_handlers": ["upload", "delete"]},
    {"id": "certificari", "label": "Certificări interne", "route": "/certificari", "fields": ["role", "signer_name", "document_title"], "required_handlers": ["create"]},
    {"id": "email", "label": "Email-uri", "route": "/email", "fields": ["recipients", "subject", "body"], "required_handlers": ["send"]},
    {"id": "verifica", "label": "Verifică documentație", "route": "/verifica", "fields": [], "required_handlers": ["run", "export"]},
    {"id": "pricing", "label": "Planuri departamente", "route": "/pricing", "fields": [], "required_handlers": ["checkout"]},
    {"id": "settings", "label": "Setări", "route": "/settings", "fields": ["gmail_user", "gmail_app_password"], "required_handlers": ["save"]},
    {"id": "ai", "label": "AI Assistant", "route": "/ai", "fields": ["message"], "required_handlers": ["parse"]},
    {"id": "audit", "label": "Audit", "route": "/audit", "fields": [], "required_handlers": ["run"]},
]


@api.get("/audit")
async def run_audit(user: User = Depends(get_current_user)):
    plan_cfg = plans_module.get_plan(user.plan)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user": {"user_id": user.user_id, "plan": user.plan, "is_developer": user.is_developer},
        "pages": [
            {**p, "implemented": True, "plan_access": p["id"] not in ["developer"] or user.is_developer}
            for p in APP_PAGES
        ],
        "plan_features": plan_cfg.get("features", []),
    }


# ====================== GDPR ======================
@api.get("/gdpr/export")
async def gdpr_export(user: User = Depends(get_current_user)):
    """Export all user data — GDPR right to portability."""
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "password_hash": 0, "gmail_app_password": 0})
    projects = await db.projects.find({"user_id": user.user_id}, {"_id": 0}).to_list(100)
    documents = await db.documents.find({"user_id": user.user_id}, {"_id": 0, "data_b64": 0, "signature_b64": 0}).to_list(1000)
    templates = await db.templates.find({"user_id": user.user_id}, {"_id": 0, "data_b64": 0}).to_list(500)
    stamps = await db.stamps.find({"user_id": user.user_id}, {"_id": 0, "data_b64": 0}).to_list(500)
    certs_internal = await db.certifications_internal.find({"user_id": user.user_id}, {"_id": 0}).to_list(500)
    logs = await db.action_logs.find({"user_id": user.user_id}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "user": user_doc, "projects": projects, "documents": documents,
        "templates": templates, "stamps": stamps,
        "certifications_internal": certs_internal, "action_logs": logs,
    }


@api.delete("/gdpr/account")
async def gdpr_delete_account(user: User = Depends(get_current_user)):
    """Delete all user data permanently (GDPR right to be forgotten)."""
    uid = user.user_id
    for coll in ["projects", "documents", "templates", "stamps", "certificates",
                 "certifications_internal", "action_logs", "email_logs",
                 "user_sessions", "payment_transactions"]:
        await db[coll].delete_many({"user_id": uid})
    await db.users.delete_one({"user_id": uid})
    return {"deleted": True}


# ====================== INDUSTRIES & SUBDOMAINS ======================
@api.get("/industries")
async def get_industries():
    return industries_module.list_industries()


# ====================== SYSTEM TEMPLATES ======================
@api.get("/system-templates")
async def list_system_templates(industry: Optional[str] = None, subdomain: Optional[str] = None):
    q = {}
    if industry:
        q["industry"] = industry
    if subdomain:
        q["subdomain"] = subdomain
    cursor = db.system_templates.find(q, {"_id": 0, "data_b64": 0}).sort("name", 1)
    return await cursor.to_list(100)


@api.post("/system-templates/{key}/clone")
async def clone_system_template(key: str, user: User = Depends(get_current_user)):
    """Clone a system template into the user's library so they can use it."""
    sys_t = await db.system_templates.find_one({"key": key})
    if not sys_t:
        raise HTTPException(status_code=404, detail="Șablon de sistem negăsit")
    template_id = new_id("tpl_")
    doc = {
        "template_id": template_id,
        "user_id": user.user_id,
        "name": sys_t["name"],
        "placeholders": sys_t.get("placeholders", []),
        "size_bytes": sys_t.get("size_bytes", 0),
        "data_b64": sys_t["data_b64"],
        "source_system_key": key,
        "industry": sys_t.get("industry"),
        "subdomain": sys_t.get("subdomain"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.templates.insert_one(doc)
    return {k: v for k, v in doc.items() if k not in ("_id", "data_b64")}


# ====================== QES CREDENTIALS ======================
class QESCredsIn(BaseModel):
    provider: str
    credentials: Dict[str, Any]


@api.put("/qes/credentials")
async def save_qes_credentials(payload: QESCredsIn, user: User = Depends(get_current_user)):
    if payload.provider not in qes_provider.PROVIDERS:
        raise HTTPException(status_code=400, detail="Provider necunoscut")
    # Store under user.qes_credentials[provider]
    existing = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "qes_credentials": 1})
    creds_all = (existing or {}).get("qes_credentials") or {}
    creds_all[payload.provider] = payload.credentials
    await db.users.update_one({"user_id": user.user_id}, {"$set": {"qes_credentials": creds_all, "qes_provider": payload.provider}})
    return {"ok": True, "provider": payload.provider, "fields_saved": list(payload.credentials.keys())}


@api.get("/qes/credentials")
async def get_qes_credentials(user: User = Depends(get_current_user)):
    """Returns which providers have credentials saved (NOT the values)."""
    doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0, "qes_credentials": 1})
    creds_all = (doc or {}).get("qes_credentials") or {}
    return {pid: {"fields_count": len(c or {})} for pid, c in creds_all.items()}


# ====================== AI DEVELOPER (developer-only) ======================
class DevPlanRequest(BaseModel):
    prompt: str
    openai_api_key: Optional[str] = None


def _ensure_developer(user: User):
    if not user.is_developer:
        raise HTTPException(status_code=403, detail="Acces interzis. Doar contul Developer poate accesa această funcție.")


@api.post("/dev/plan")
async def dev_plan(payload: DevPlanRequest, user: User = Depends(get_current_user)):
    _ensure_developer(user)
    has_qes = bool((await db.users.find_one({"user_id": user.user_id}, {"qes_credentials": 1}) or {}).get("qes_credentials"))
    has_gmail = bool((await db.users.find_one({"user_id": user.user_id}, {"gmail_user": 1, "gmail_app_password": 1}) or {}).get("gmail_app_password"))
    has_system_tpl = (await db.system_templates.count_documents({})) > 0
    stripe_key = os.environ.get("STRIPE_API_KEY", "")
    repo_summary = {
        "has_stripe_live_key": stripe_key.startswith("sk_live_"),
        "has_qes_credentials": has_qes,
        "has_gmail_for_user": has_gmail,
        "has_system_templates": has_system_tpl,
    }
    result = await ai_developer.plan(
        payload.prompt, repo_summary,
        openai_api_key=payload.openai_api_key or os.environ.get("OPENAI_API_KEY"),
    )
    await db.action_logs.insert_one({
        "log_id": new_id("log_"), "user_id": user.user_id, "action": "dev.plan",
        "meta": {"prompt": payload.prompt[:300], "external": result.get("external_llm_used")},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return result


@api.get("/dev/safety-rules")
async def dev_safety_rules(user: User = Depends(get_current_user)):
    _ensure_developer(user)
    return {"rules": ai_developer.SAFETY_RULES}


# ====================== DEVELOPER → GITHUB AUTO-PUSH ======================
@api.get("/dev/github/status")
async def dev_github_status(user: User = Depends(get_current_user)):
    """Show last commit on configured branch — for the Developer panel."""
    _ensure_developer(user)
    try:
        return await github_push.repo_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GitHub status indisponibil: {e}")


@api.post("/dev/github/push")
async def dev_github_push(payload: github_push.GitHubPushRequest, user: User = Depends(get_current_user)):
    """Commit the supplied files into the connected repo (triggers Render auto-deploy)."""
    _ensure_developer(user)
    try:
        result = await github_push.push_files(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.action_logs.insert_one({
        "log_id": new_id("log_"),
        "user_id": user.user_id,
        "action": "dev.github.push",
        "meta": {
            "prompt": payload.prompt[:300],
            "commit_message": payload.commit_message,
            "files": [f["path"] for f in result.get("results", [])],
            "branch": result.get("branch"),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return result


@api.get("/dev/handoff/export")
async def dev_handoff_export(user: User = Depends(get_current_user)):
    """Generate a markdown 'save state' file for transferring this project to another Emergent user."""
    _ensure_developer(user)
    try:
        markdown = await handoff_module.build_handoff_markdown()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Handoff generation failed: {e}")
    return {
        "filename": "HANDOFF_FOR_NEXT_EMERGENT.md",
        "markdown": markdown,
        "size_chars": len(markdown),
    }


@api.post("/dev/handoff/push")
async def dev_handoff_push(user: User = Depends(get_current_user)):
    """Generate the handoff doc and commit it to the repo root so any future clone has it."""
    _ensure_developer(user)
    try:
        markdown = await handoff_module.build_handoff_markdown()
        req = github_push.GitHubPushRequest(
            prompt="Auto-generated handoff snapshot — paste this into a new Emergent chat to continue.",
            commit_message="docs: refresh HANDOFF_FOR_NEXT_EMERGENT.md",
            files=[github_push.GitHubPushFile(path="HANDOFF_FOR_NEXT_EMERGENT.md", content=markdown)],
            update_secret=os.environ.get("EPD_UPDATE_SECRET", "").strip() or None,
        )
        result = await github_push.push_files(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Handoff push failed: {e}")
    await db.action_logs.insert_one({
        "log_id": new_id("log_"),
        "user_id": user.user_id,
        "action": "dev.handoff.push",
        "meta": {"chars": len(markdown), "commit_sha": result["results"][0]["commit_sha"][:7]},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {
        "ok": True,
        "size_chars": len(markdown),
        "file_url": result["results"][0]["file_url"],
        "commit_url": result["results"][0]["commit_url"],
    }


# ====================== ACTIVITY LOG & VERSION STATUS ======================
@api.get("/activity")
async def get_activity(limit: int = 30, user: User = Depends(get_current_user)):
    """Return recent user actions for the dashboard activity log."""
    cursor = db.action_logs.find({"user_id": user.user_id}, {"_id": 0}).sort("created_at", -1)
    items = await cursor.to_list(limit)
    # Human-readable labels (Romanian) — keeps the log professional looking
    label_map = {
        "register": "Înregistrare cont nou",
        "login": "Autentificare",
        "project.update": "Actualizare date proiect",
        "ai.parse": "Comandă AI Assistant",
        "dev.plan": "Plan AI Developer generat",
        "logout": "Deconectare",
    }
    for it in items:
        it["label"] = label_map.get(it.get("action", ""), it.get("action", "Acțiune"))
    return items


@api.get("/version/status")
async def version_status(user: User = Depends(get_current_user)):
    """Aggregate completion status of the platform. Returns final-version message
    when all critical capabilities are configured.
    """
    # Count user-scoped configured items
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0}) or {}
    proj_count = await db.projects.count_documents({"user_id": user.user_id, "archived": {"$ne": True}})
    doc_count = await db.documents.count_documents({"user_id": user.user_id})
    sys_t_count = await db.system_templates.count_documents({})
    capabilities = {
        "gmail_configured": bool(user_doc.get("gmail_user") and user_doc.get("gmail_app_password")),
        "qes_configured": bool(user_doc.get("qes_credentials")),
        "has_projects": proj_count > 0,
        "has_documents": doc_count > 0,
        "system_templates_loaded": sys_t_count > 0,
        "gdpr_consent": bool(user_doc.get("gdpr_consent")),
        "stripe_live": os.environ.get("STRIPE_API_KEY", "").startswith("sk_live_"),
    }
    done = sum(1 for v in capabilities.values() if v)
    total = len(capabilities)
    percent = round(100.0 * done / total, 1)
    is_final = percent == 100.0
    return {
        "version": "4.7",
        "capabilities": capabilities,
        "completion_percent": percent,
        "is_final_version": is_final,
        "message": "Program versiune finală încheiat cu succes." if is_final else
                   f"Versiune în dezvoltare — {done}/{total} capabilități configurate.",
    }


# ====================== PDF EXPORT ======================
@api.get("/project/pdf")
async def project_pdf(user: User = Depends(get_current_user)):
    """Generate a styled A4 PDF report for the active project."""
    proj = await _get_or_create_default_project(user.user_id)
    # Build verification dict inline for the report (lightweight)
    verification = await verify_documentation(user)
    pdf_bytes = pdf_export.build_project_pdf(proj, calc_results=proj.get("calc_results"), verification=verification)
    safe_name = (proj.get("name") or "proiect")
    # Strip non-ASCII for HTTP Content-Disposition (latin-1 only)
    safe_name = safe_name.encode("ascii", "ignore").decode("ascii").replace(" ", "_").replace("/", "_") or "proiect"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="raport_{safe_name}.pdf"'},
    )


# ====================== AI DEVELOPER CHAT (persistent, developer-only) ======================
class DevChatMessage(BaseModel):
    role: str  # 'user' | 'assistant'
    content: str
    created_at: Optional[str] = None


class DevChatSend(BaseModel):
    message: str
    openai_api_key: Optional[str] = None
    session_id: Optional[str] = None


@api.get("/dev/chat/sessions")
async def list_dev_chat_sessions(user: User = Depends(get_current_user)):
    _ensure_developer(user)
    cursor = db.dev_chat_sessions.find({"user_id": user.user_id}, {"_id": 0}).sort("updated_at", -1)
    return await cursor.to_list(50)


@api.get("/dev/chat/{session_id}")
async def get_dev_chat(session_id: str, user: User = Depends(get_current_user)):
    _ensure_developer(user)
    sess = await db.dev_chat_sessions.find_one({"session_id": session_id, "user_id": user.user_id}, {"_id": 0})
    if not sess:
        raise HTTPException(status_code=404, detail="Sesiune negăsită")
    return sess


@api.post("/dev/chat/send")
async def send_dev_chat(payload: DevChatSend, user: User = Depends(get_current_user)):
    _ensure_developer(user)
    now = datetime.now(timezone.utc).isoformat()

    session_id = payload.session_id
    if not session_id:
        session_id = new_id("dch_")
        await db.dev_chat_sessions.insert_one({
            "session_id": session_id, "user_id": user.user_id,
            "title": payload.message[:80],
            "messages": [],
            "created_at": now, "updated_at": now,
        })

    # Diagnostic context
    user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0}) or {}
    repo_summary = {
        "has_stripe_live_key": os.environ.get("STRIPE_API_KEY", "").startswith("sk_live_"),
        "has_qes_credentials": bool(user_doc.get("qes_credentials")),
        "has_gmail_for_user": bool(user_doc.get("gmail_app_password")),
        "has_system_templates": (await db.system_templates.count_documents({})) > 0,
    }
    plan_result = await ai_developer.plan(
        payload.message, repo_summary,
        openai_api_key=payload.openai_api_key or os.environ.get("OPENAI_API_KEY"),
    )
    # Build a chat-style assistant reply (markdown-ish)
    parts = [f"**Plan generat** (mode: `{plan_result.get('mode')}`)\n"]
    diag = plan_result.get("diagnostic", {})
    if diag.get("missing_capabilities"):
        parts.append("**Capabilități lipsă:**")
        for m in diag["missing_capabilities"]:
            parts.append(f"- {m}")
    else:
        parts.append("✅ Nicio capabilitate critică lipsă.")
    parts.append("\n**Pași propuși:**")
    for i, s in enumerate(plan_result.get("proposed_steps", []), 1):
        parts.append(f"{i}. {s}")
    if plan_result.get("external_llm_advice"):
        parts.append("\n**Sfat OpenAI:**")
        parts.append(plan_result["external_llm_advice"])
    parts.append("\n**Validare după aplicare:**")
    for v in plan_result.get("validation_checklist", []):
        parts.append(f"- [ ] {v}")
    parts.append("\n_Plan Mode — confirmați aplicarea manuală cu agentul principal (Emergent / Claude / ChatGPT / Codex)._")

    assistant_reply = "\n".join(parts)
    messages_to_add = [
        {"role": "user", "content": payload.message, "created_at": now},
        {"role": "assistant", "content": assistant_reply, "created_at": datetime.now(timezone.utc).isoformat(),
         "metadata": {"intent": plan_result.get("mode"), "external": plan_result.get("external_llm_used")}},
    ]
    await db.dev_chat_sessions.update_one(
        {"session_id": session_id},
        {"$push": {"messages": {"$each": messages_to_add}}, "$set": {"updated_at": now}},
    )

    sess = await db.dev_chat_sessions.find_one({"session_id": session_id}, {"_id": 0})
    return sess


@api.delete("/dev/chat/{session_id}")
async def delete_dev_chat(session_id: str, user: User = Depends(get_current_user)):
    _ensure_developer(user)
    await db.dev_chat_sessions.delete_one({"session_id": session_id, "user_id": user.user_id})
    return {"deleted": True}


# ====================== VISION / MEMORY ======================
@api.get("/vision")
async def get_vision(user: User = Depends(get_current_user)):
    """Return the PRD / vision document so any AI can pick up context."""
    vision_path = Path("/app/memory/PRD.md")
    if not vision_path.exists():
        return {"vision": "", "exists": False}
    try:
        content = vision_path.read_text(encoding="utf-8")
        return {"vision": content, "exists": True, "size_bytes": len(content)}
    except Exception as e:
        return {"vision": "", "exists": False, "error": str(e)}


# ====================== PROGRESS TRACKER & LISTS (developer-only) ======================
import json as _json_mod

_LIST_FILES_MAP = {
    "todo": "/app/memory/LIST_1_TODO.md",
    "suggested": "/app/memory/LIST_2_SUGGESTED.md",
    "futuristic": "/app/memory/LIST_3_FUTURISTIC.md",
    "big_update": "/app/memory/LIST_4_BIG_UPDATE_WEB_RESEARCH.md",
}


@api.get("/dev/progress")
async def dev_progress(user: User = Depends(get_current_user)):
    """Return the STEP_TRACKER.json content so developer page can render phases + steps."""
    _ensure_developer(user)
    tracker_path = Path("/app/memory/STEP_TRACKER.json")
    if not tracker_path.exists():
        return {"meta": {}, "phases": [], "checkpoints": [], "last_emergent_account_command": None}
    try:
        return _json_mod.loads(tracker_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tracker read error: {e}")


@api.get("/dev/list/{list_id}")
async def dev_list(list_id: str, user: User = Depends(get_current_user)):
    """Return the markdown content of one of the 4 planning lists."""
    _ensure_developer(user)
    file_path = _LIST_FILES_MAP.get(list_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="List inexistentă (folosește: todo|suggested|futuristic|big_update)")
    p = Path(file_path)
    if not p.exists():
        return {"id": list_id, "content": "", "exists": False}
    try:
        return {"id": list_id, "content": p.read_text(encoding="utf-8"), "exists": True, "size": p.stat().st_size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List read error: {e}")


@api.post("/dev/list/{list_id}/append")
async def dev_list_append(list_id: str, payload: dict, user: User = Depends(get_current_user)):
    """Append a markdown block at the end of a list (append-only, never overwrite)."""
    _ensure_developer(user)
    file_path = _LIST_FILES_MAP.get(list_id)
    if not file_path:
        raise HTTPException(status_code=404, detail="List inexistentă")
    block = (payload or {}).get("block", "").strip()
    if not block:
        raise HTTPException(status_code=400, detail="Lipsește 'block' (text markdown).")
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    appended_block = f"\n\n---\n### Append [{timestamp}]\n{block}\n"
    with p.open("a", encoding="utf-8") as fh:
        fh.write(appended_block)
    return {"ok": True, "id": list_id, "appended_chars": len(appended_block), "timestamp": timestamp}


# ====================== FEAT-URI STATUS (public-ish, sumar) ======================
FEAT_HUB_STATUS = {
    "seap": "planned",
    "ai-agents": "skeleton",
    "subscribers": "planned",
    "jobs": "planned",
    "reports": "planned",
    "legal-automation": "planned",
    "partners": "planned",
    "volunteering": "planned",
    "developer-plan": "partial",
    "community": "partial",
}


@api.get("/feat/status")
async def feat_status():
    """Returns the status of the vision sub-modules (active/partial/skeleton/planned)."""
    return {
        "features": [
            {"id": fid, "status": st} for fid, st in FEAT_HUB_STATUS.items()
        ],
        "summary": {
            "total": len(FEAT_HUB_STATUS),
            "active": sum(1 for s in FEAT_HUB_STATUS.values() if s == "active"),
            "partial": sum(1 for s in FEAT_HUB_STATUS.values() if s == "partial"),
            "skeleton": sum(1 for s in FEAT_HUB_STATUS.values() if s == "skeleton"),
            "planned": sum(1 for s in FEAT_HUB_STATUS.values() if s == "planned"),
        },
    }


# ====================== AI AGENTS REGISTRY (skeleton — 4 specialized agents) ======================
AI_AGENTS_REGISTRY = [
    {
        "id": "producer",
        "name": "Producer AI Agent",
        "tagline": "Analizează documentația veche și sugerează actualizări conform normelor noi.",
        "model_recommendation": "gpt-4o",
        "context_scope": "documente firmei + norme ANRE/ANRP/ISCIR/AFER curente",
        "status": "planned",
    },
    {
        "id": "user",
        "name": "User AI Agent",
        "tagline": "Ghidează utilizatorul pe formular cu validare în timp real și sugestii contextuale.",
        "model_recommendation": "gpt-4o-mini",
        "context_scope": "proiectul activ + tipul de utilizator (proiectant/executant/RTE/VGD)",
        "status": "skeleton",
    },
    {
        "id": "client",
        "name": "Client AI Agent",
        "tagline": "Chat clienți finali cu recomandări tarife/servicii pe baza istoricului.",
        "model_recommendation": "gpt-4o-mini",
        "context_scope": "istoric servicii client + cataloagele firmei + reduceri active",
        "status": "planned",
    },
    {
        "id": "developer",
        "name": "Developer AI Agent",
        "tagline": "Modificări cod custom + dezvoltare funcții (Plan Mode + Apply Mode în viitor).",
        "model_recommendation": "gpt-4o + tools",
        "context_scope": "repo /app/* + safety rules + diff preview",
        "status": "partial",
    },
]


@api.get("/ai/agents")
async def list_ai_agents():
    """Public read-only registry of the 4 specialized AI agents from the vision."""
    return {"agents": AI_AGENTS_REGISTRY, "count": len(AI_AGENTS_REGISTRY)}


# ====================== ROOT ======================
@api.get("/")
async def root():
    return {"app": "Energy Project Design Services", "version": "5.2", "status": "ok", "build": "emergent-rebuild-2026-06"}


# ====================== PAYMENT ACCOUNTS (admin / public) ======================
@api.get("/payment-accounts/active")
async def get_active_payment_account():
    """Public — returns the currently active receiving account for SEPA bank transfers."""
    acc = await pay_accounts.get_active_account()
    if not acc:
        return {"available": False, "message": "Niciun cont activ configurat pentru transfer bancar."}
    return {
        "available": True,
        "account_holder": acc["account_holder"],
        "iban": acc["iban"],
        "swift_bic": acc.get("swift_bic"),
        "bank_name": acc["bank_name"],
        "currency": acc["currency"],
        "status": acc["status"],
        "notes": acc.get("notes"),
    }


@api.get("/admin/payment-accounts")
async def admin_list_payment_accounts(include_disabled: bool = False, user: User = Depends(get_current_user)):
    _ensure_developer(user)
    return await pay_accounts.list_accounts(include_disabled=include_disabled)


@api.post("/admin/payment-accounts")
async def admin_create_payment_account(payload: pay_accounts.PaymentAccountIn, user: User = Depends(get_current_user)):
    _ensure_developer(user)
    account_id = new_id("acc_")
    doc = await pay_accounts.create_account(payload, account_id)
    await db.action_logs.insert_one({
        "log_id": new_id("log_"), "user_id": user.user_id, "action": "admin.payment_accounts.create",
        "meta": {"account_id": account_id, "iban_last4": doc["iban"][-4:], "status": doc["status"]},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return doc


@api.patch("/admin/payment-accounts/{account_id}")
async def admin_update_payment_account(account_id: str, payload: dict, user: User = Depends(get_current_user)):
    _ensure_developer(user)
    res = await pay_accounts.update_account(account_id, payload)
    if not res:
        raise HTTPException(status_code=404, detail="Cont inexistent")
    await db.action_logs.insert_one({
        "log_id": new_id("log_"), "user_id": user.user_id, "action": "admin.payment_accounts.update",
        "meta": {"account_id": account_id, "fields": list(payload.keys())},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return res


@api.delete("/admin/payment-accounts/{account_id}")
async def admin_delete_payment_account(account_id: str, user: User = Depends(get_current_user)):
    _ensure_developer(user)
    ok = await pay_accounts.delete_account(account_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Cont inexistent")
    await db.action_logs.insert_one({
        "log_id": new_id("log_"), "user_id": user.user_id, "action": "admin.payment_accounts.delete",
        "meta": {"account_id": account_id},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"deleted": True}


# Forum routes appended below — include_router moved to end of file.


# ====================== FORUM (registered above include_router) ======================
# Note: forum routes are defined here and then re-included below.
@api.get("/forum/industry-stats")
async def forum_industry_stats():
    return await forum_module.industry_stats()


@api.get("/forum/threads")
async def forum_list_threads(industry: Optional[str] = None, sort: str = "recent", limit: int = 50):
    return await forum_module.list_threads(industry=industry, sort=sort, limit=min(limit, 100))


@api.get("/forum/threads/{thread_id}")
async def forum_get_thread(thread_id: str):
    thread = await forum_module.get_thread(thread_id, increment_view=True)
    if not thread:
        raise HTTPException(status_code=404, detail="Discuție inexistentă")
    replies = await forum_module.list_replies(thread_id)
    return {"thread": thread, "replies": replies}


@api.post("/forum/threads")
async def forum_create_thread(payload: forum_module.ThreadCreate, user: User = Depends(get_current_user)):
    try:
        thread_id = new_id("thr_")
        doc = await forum_module.create_thread(user, payload, thread_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await db.action_logs.insert_one({
        "log_id": new_id("log_"), "user_id": user.user_id, "action": "forum.thread.create",
        "meta": {"thread_id": thread_id, "industry": payload.industry, "title": payload.title[:80]},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return doc


@api.post("/forum/threads/{thread_id}/replies")
async def forum_create_reply(thread_id: str, payload: forum_module.ReplyCreate, user: User = Depends(get_current_user)):
    reply_id = new_id("rep_")
    doc = await forum_module.create_reply(user, thread_id, payload, reply_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Discuție inexistentă")
    await db.action_logs.insert_one({
        "log_id": new_id("log_"), "user_id": user.user_id, "action": "forum.reply.create",
        "meta": {"thread_id": thread_id, "reply_id": reply_id},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return doc


@api.post("/forum/threads/{thread_id}/like")
async def forum_like_thread(thread_id: str, user: User = Depends(get_current_user)):
    likes = await forum_module.like_thread(thread_id, user.user_id)
    if likes is None:
        raise HTTPException(status_code=404, detail="Discuție inexistentă")
    return {"likes": likes}


@api.delete("/forum/threads/{thread_id}")
async def forum_delete_thread(thread_id: str, user: User = Depends(get_current_user)):
    _ensure_developer(user)
    ok = await forum_module.delete_thread(thread_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Discuție inexistentă")
    return {"deleted": True}


# ====================== PROJECT LIFECYCLE ======================
@api.get("/lifecycle/statuses")
async def lifecycle_statuses():
    """Public — return the catalog of project lifecycle statuses."""
    return {"statuses": lifecycle.STATUSES}


@api.get("/lifecycle/current")
async def lifecycle_current(user: User = Depends(get_current_user)):
    """Returns current detected status + smart audit score + next best action for the active project."""
    proj = await _get_or_create_default_project(user.user_id)
    counts = {
        "templates": await db.templates.count_documents({"user_id": user.user_id}),
        "documents": await db.documents.count_documents({"user_id": user.user_id}),
        "stamps": await db.stamps.count_documents({"user_id": user.user_id}),
        "certifications": await db.certifications_internal.count_documents({"user_id": user.user_id}),
    }
    plan_cfg = plans_module.get_plan(user.plan)
    detected = lifecycle.detect_status(proj, counts)
    score = lifecycle.smart_audit_score(proj, counts)
    action = lifecycle.next_best_action(proj, counts, plan_cfg)
    return {
        "current_status": detected,
        "status_meta": lifecycle.status_meta(detected),
        "score": score,
        "next_best_action": action,
        "counts": counts,
    }


@api.post("/lifecycle/set-status")
async def lifecycle_set_status(payload: dict, user: User = Depends(get_current_user)):
    """Manual override — sets the status on the active project."""
    new_status = (payload or {}).get("status", "").strip()
    if new_status not in lifecycle.STATUS_BY_ID:
        raise HTTPException(status_code=400, detail=f"Status invalid. Valid: {list(lifecycle.STATUS_BY_ID.keys())}")
    proj = await _get_or_create_default_project(user.user_id)
    await db.projects.update_one(
        {"project_id": proj["project_id"], "user_id": user.user_id},
        {"$set": {"status": new_status, "status_changed_at": datetime.now(timezone.utc).isoformat()}},
    )
    await db.action_logs.insert_one({
        "log_id": new_id("log_"), "user_id": user.user_id, "action": "lifecycle.set_status",
        "meta": {"project_id": proj["project_id"], "from": proj.get("status"), "to": new_status},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"status": new_status, "meta": lifecycle.status_meta(new_status)}


# ====================== AUDIT LOGS ======================
@api.get("/logs")
async def list_audit_logs(
    action: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 100,
    user: User = Depends(get_current_user),
):
    """User sees their own logs. Developer sees ALL logs."""
    q = {} if user.is_developer else {"user_id": user.user_id}
    if action:
        q["action"] = {"$regex": action, "$options": "i"}
    if from_date:
        q.setdefault("created_at", {})["$gte"] = from_date
    if to_date:
        q.setdefault("created_at", {})["$lte"] = to_date
    docs = await db.action_logs.find(q, {"_id": 0}).sort("created_at", -1).limit(min(limit, 500)).to_list(500)
    return docs


@api.get("/logs/actions")
async def list_log_actions(user: User = Depends(get_current_user)):
    """Return distinct action names — for the filter dropdown."""
    q = {} if user.is_developer else {"user_id": user.user_id}
    actions = await db.action_logs.distinct("action", q)
    return sorted([a for a in actions if a])


# ====================== DOCUMENT VERSIONING ======================
@api.get("/documents/groups")
async def list_document_groups(user: User = Depends(get_current_user)):
    """Group documents by base name — returns groups with version count + latest version."""
    docs = await db.documents.find(
        {"user_id": user.user_id},
        {"_id": 0, "data_b64": 0, "signature_b64": 0},
    ).sort("created_at", -1).to_list(2000)
    groups: Dict[str, Dict[str, Any]] = {}
    for d in docs:
        base = (d.get("name") or "Untitled").rsplit("_v", 1)[0]
        if base not in groups:
            groups[base] = {
                "base_name": base,
                "latest_id": d["document_id"],
                "latest_name": d["name"],
                "latest_created_at": d["created_at"],
                "versions_count": 1,
                "versions": [{"document_id": d["document_id"], "name": d["name"], "created_at": d["created_at"], "signed": d.get("signed"), "stamped": d.get("stamped")}],
            }
        else:
            groups[base]["versions_count"] += 1
            groups[base]["versions"].append({"document_id": d["document_id"], "name": d["name"], "created_at": d["created_at"], "signed": d.get("signed"), "stamped": d.get("stamped")})
    return list(groups.values())


@api.get("/documents/{document_id}/versions")
async def get_document_versions(document_id: str, user: User = Depends(get_current_user)):
    """List versions of the same base-name as the given document."""
    doc = await db.documents.find_one({"document_id": document_id, "user_id": user.user_id}, {"_id": 0, "data_b64": 0, "signature_b64": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Document negăsit")
    base = (doc.get("name") or "").rsplit("_v", 1)[0]
    if not base:
        return [doc]
    cursor = db.documents.find(
        {"user_id": user.user_id, "name": {"$regex": f"^{base}"}},
        {"_id": 0, "data_b64": 0, "signature_b64": 0},
    ).sort("created_at", 1)
    return await cursor.to_list(100)


@api.get("/company-profile")
async def get_company_profile(user: User = Depends(get_current_user)):
    return await company_module.get_profile(user.user_id)


@api.put("/company-profile")
async def upsert_company_profile(payload: company_module.CompanyProfile, user: User = Depends(get_current_user)):
    doc = await company_module.upsert_profile(user.user_id, payload)
    await db.action_logs.insert_one({
        "log_id": new_id("log_"), "user_id": user.user_id, "action": "company.profile.update",
        "meta": {"fields": [k for k, v in payload.model_dump().items() if v is not None]},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return doc


@api.get("/company-profile/placeholders")
async def get_company_placeholders(user: User = Depends(get_current_user)):
    """Returns the placeholder map derived from the company profile."""
    profile = await company_module.get_profile(user.user_id)
    return company_module.placeholders_from_profile(profile)


app.include_router(api)


# CORS: when credentials are required, browsers reject "*" origin. Use a regex
# that matches the Emergent preview URL pattern + Render production URL. Override
# via CORS_ORIGINS env (comma-separated explicit origins) if needed.
_cors_env = os.environ.get("CORS_ORIGINS", "").strip()
if _cors_env and _cors_env != "*":
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=[o.strip() for o in _cors_env.split(",") if o.strip()],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origin_regex=r"https://([a-z0-9-]+\.)*(emergentagent\.com|onrender\.com|emergent\.host)|http://localhost:3000",
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )


@app.on_event("startup")
async def on_startup():
    try:
        await system_templates.seed_system_templates(db)
        logger.info("System templates seeded.")
        await pay_accounts.seed_default_account()
        logger.info("Default payment account seeded.")
        # Upgrade developer accounts on every startup
        await db.users.update_many(
            {"email": {"$in": list(DEVELOPER_EMAILS)}},
            {"$set": {"is_developer": True, "plan": "developer"}},
        )
    except Exception as e:
        logger.warning(f"Startup seed failed: {e}")


@app.on_event("shutdown")
async def shutdown_db_client():
    from db import client
    client.close()
