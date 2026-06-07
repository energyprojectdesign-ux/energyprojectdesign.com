# Energy Project Design — PRD


## CHANGELOG — 2026-02-07 (V5.9) — Repo unification & public verification

### Backend (din repo dragosserban95/Energy-Project-Design clonat)
- **Clients CRM** (`clients_crm.py`, legacy per-user) — endpoints `/api/clients` cu CRUD complet, filtre status+industry.
- **Companies Directory** (`companies_directory.py`, public) — endpoints `/api/companies/{roles,stats,list,CRUD}` cu 8+ roluri (designer, executor, vgd, rte, etc.). Auto-verified pentru developers.
- Toate mountate prin `api2` router în server.py.

### Frontend
- **Clients.jsx** (per-user CRM proiectanți) și **Companies.jsx** (directory public) — copiate din repo.
- **VerifyGasProject.jsx** NOU — pagină publică `/verify/gas-project/:pid` (URL din QR-ul proiectului):
  - Card de verificare cu status semnat/draft, beneficiar, locație, faza, hash SHA-256
  - Pagină de eroare elegantă pentru PID inexistent
  - Fără auth — accesibilă oricui scanează QR-ul
- **Sidebar**: adăugat "Clienți (Proiectanți)" și "Companii (Directory)"
- **App.js routes**: `/clients`, `/companies`, `/verify/gas-project/:pid`

### Testing
- **iteration_4.json**: Backend 10/10 pytest, Frontend 100% pe toate selectoarele
- Test file: `/app/backend/tests/test_v59_features.py`
- 0 bug-uri. Code review note: server.py la 2390 linii — refactor recomandat în următoarea iterație.


## CHANGELOG — 2026-02-07 (V5.8) — Gas Project Studio + Subscribers + Rate Limiting

### Backend
- **Rate limiting AI Agents**: POST `/api/ai/agents/{agent}` cu cooldown per user (8/min, 60/zi pentru utilizatori; 30/min, 500/zi pentru admin/developer). Returnează 429 cu mesaj RO + obiect `rate_limit` în răspuns success.
- **Modul Gas Project Studio** (`gas_project_routes.py` + `gas_project_phases.py`):
  - 11 faze legale conform NTPEE 2018 + HG 907/2016: tema → SF → CU+Avize → DTAC → AC → PT → DE → Execuție → Probe → Recepție → PIF
  - 78 câmpuri variabile total per proiect (beneficiar, debit, presiune, materiale, atestate ANRE, etc.)
  - Endpoints: `GET /phases`, `POST /`, `GET /`, `GET /{pid}`, `PATCH /{pid}`, `DELETE /{pid}`, `POST /{pid}/sign`, `GET /{pid}/qr`, `GET /{pid}/public`
  - **Semnătură digitală**: SHA-256 hash + integrare cu ștampile încărcate (`/api/stamps`)
  - **QR code** generat dinamic (qrcode lib) cu URL public de verificare
  - Gate: semnătura blocată sub 70% completare proiect
- **Modul Subscribers B2B** (`subscribers_routes.py`):
  - 5 tipuri: primarie / asociatie_locatari / utilitate_publica / dezvoltator / societate
  - CRUD complet, filtrare după tip

### Frontend
- **GasNaturalProject.jsx** (Studio):
  - List view cu card-uri (progress bar, status semnat/draft)
  - Studio view cu sidebar 11 faze, formular dinamic, progress bar per fază + global, deliverables box
  - Preview mode (read-only tabular pentru toate fazele)
  - QR modal cu download PNG + Escape-to-close
  - Sign panel cu selector ștampilă din contul user
- **Subscribers.jsx**: 5 type cards, filter pills, create modal, list cards
- **Routing**: `/gaze-naturale`, `/gaze-naturale/:pid`, `/subscribers`
- **Sidebar**: adăugat "Gaze Naturale Studio" (nav-gaze-naturale) + "Subscriberi B2B" (nav-subscribers)

### Testing
- **iteration_3.json**: Backend 5/5 pytest passed, Frontend 100% pe toate selectoarele V5.8
- Test file: `/app/backend/tests/test_v58_features.py`
- 0 bug-uri critice. Fix aplicat: QR modal Escape-key close.


## CHANGELOG — 2026-02-07 (V5.7)
- **Branding global**: înlocuit "StampDoc.ro" cu "Energy Project Design" în Login, Register, LegalLayout, Gdpr, Settings, TemplateEditor.
- **Login hero text**: "Energy Project Design — international electronic technical documentation, certified and digitally stamped." (cerere directă utilizator)
- **SEO meta tags extinse** (`/app/frontend/public/index.html`): title nou, description bilingv multi-industrie, 50+ keywords (ANRE/ANRSC/ISCIR/NTPEE/VGD/RTE/QES/SEAP), 13 hashtag-uri ca `article:tag`, geo/locale RO+EN, theme-color #FFB300, OG + Twitter Cards aliniate la noul brand.
- **Sitemap.xml** extins: 13 industrii + 5 persona pages + 5 subdomenii gaze + pagini funcționale (jobs, marketplace, ai-agents, anaf, crm, energy-advisor).
- **Personas pages** noi (`/pentru/:role`) pentru Clienți, Utilizatori, Angajați, Developeri, Admin — fiecare cu beneficii, pagini utile, hashtag-uri. Component: `/app/frontend/src/pages/Personas.jsx`.
- **Landing hero refăcut** pentru poziționare internațională multi-industrie (13 industrii / 56+ subdomenii / QES) + secțiune "5 perspective" cu link-uri către persona pages.
- **Sidebar**: "Industrii (12)" → "Industrii (13)".
- Surse: `/app/esitmate.rar` extras în `/app/esitmate_extracted/` (58 fișiere: site.docx, Feat-uri.docx, prompt nou.docx, etc.).
- **Testing V5.7**: testing_agent_v3_fork iteration_2 — Backend 14/14 pytest passed, Frontend 100%. Suite: `/app/backend/tests/test_v57_features.py`.
- **AI Agents per persona confirmat funcțional**: 4 agenți (Producer/User/Client/Developer) deja implementați în `/app/backend/ai_agents.py` cu Claude Sonnet 4.6 via Emergent LLM Key + UI `/app/frontend/src/pages/AIAgents.jsx`. Răspunsuri live verificate prin curl + UI.


## Product Vision
B2B SaaS pentru proiectare în energie/infrastructură. Centralizează proiectarea ANRE, calcule tehnice (fotovoltaic, gaze, electric), generare automată documentație, semnătură digitală QES și marketplace de subdomenii (12 industrii + 158 subdomenii planificate).

Limba interfeței: **Română**.

## Tech Stack
- **Backend**: FastAPI 0.110+, Python 3.11, Motor (MongoDB async), Pydantic v2, ReportLab (PDF), python-docx (DOCX), Gmail SMTP.
- **Frontend**: React 18, React Router 6, Tailwind CSS, Shadcn UI, lucide-react icons, sonner toasts.
- **DB**: MongoDB (collections: users, projects, documents, templates, stamps, certificates, payment_transactions, forum_threads, action_logs, admin_config).
- **Integrări**: Stripe (payments), Gmail SMTP (email), Emergent LLM (AI assistant), ReportLab (PDF), ANRE catalog.

## User Personas
1. **Proiectant autorizat ANRE** — generează documentație tehnică pentru proiecte de gaze/electric/fotovoltaic.
2. **Firmă executantă** — primește documentația semnată QES și o transmite autorităților.
3. **Verificator VGD/RTE** — analizează și parafează documente; folosește forumul.
4. **Admin platformă** — configurare globală, gestionare utilizatori, monitorizare.

## Architecture
- All backend routes prefixed `/api`. Frontend uses `REACT_APP_BACKEND_URL` env var.
- Routing: protected routes wrap auth check. Sidebar in `AppShell` is role-aware (developers/admins see Admin Config + Developer Plan).
- DOCX generation pipeline: template (.docx) + data dict → docxtpl → response file.
- PDF generation: ReportLab `SimpleDocTemplate` with custom `_header`, themed palette (`#FFB300`/`#0A0A0A`/`#16A34A`).
- Email pipeline: per-user Gmail App Password → SMTP_SSL 465 with automatic CC to user's `secondary_email` based on global admin flag.

## Implemented Features (cumulative — see CHANGELOG via PROGRESS_LOG.md)

### Core (V1-V5.3)
- Auth (email/password JWT + Google OAuth)
- Project management (CRUD, active project, technical data, photovoltaic data)
- Template/stamp/certificate library
- DOCX document generation
- PDF export (generic project report)
- Gmail SMTP email with attachment
- Stripe checkout flows
- Photovoltaic calculation engine (ANRE Ord. 34/2024 compliant)
- QES providers config (CertSign, DigiSign, Trans Sped)
- Forum (threads, replies, likes, industry filtering)
- AI Assistant (Emergent LLM-powered)
- 12 industries hub + per-industry pages

### V5.4 (2026-02-06) — Admin & Polish Release
- **Secondary Business Email**: `User.secondary_email` field; auto-CC on all outgoing email when `admin_config.smtp_cc_secondary_default=True`.
- **Admin-Only Configuration UI** at `/admin/config`:
  - Maintenance mode toggle + message
  - Announcement banner (info/success/warning/danger)
  - Global SMTP fallback (from name, Gmail, App Password — write-only)
  - 6 feature flags (forum, email, PDF, photovoltaic, AI, payments)
  - User management (search, promote/demote admin, ban/unban)
  - Live platform stats
- **Audit log**: every admin action persisted in `db.action_logs`.
- **Public banner endpoint**: `/api/system/banner` (no auth) — clients can poll for maintenance + announcement.
- **Generate Tech Offer FV PDF**: button on Photovoltaic Calc page → `/api/photovoltaic/tech-offer-pdf` returns a commercial-grade A4 PDF (hero kWp, ANRE category, full component config, energy estimation, normative compliance, commercial terms, signature blocks).
- **Deep UX polish** on FeaturesHub, IndustriesHub, Forum: glass-morphism heroes, dot/grid patterns, status badges, search + filters, progress bars, hover glow.

### V5.6 (2026-02-07) — Repository Unification + Marketplace Recovery
- **Comandă fondatoare**: "Acces fără excepție la toate fișierele, integrare a tuturor update-urilor de pe toate URL-urile" → consemnată în `/app/memory/VISION_MANIFEST.md`.
- **Restaurat din commit `933d02c`** (Marketplace pierdut):
  - `/api/dev/jobs` (admin CRUD) + `/api/jobs` (public, no auth) — Job Board ANRE
  - `/api/dev/contracts` (admin CRUD) — Contracte CRM cu legături la abonați
  - `/api/seap/status` — integration health
- **Refactor `server.py`**: mutat în `backend/admin_routes.py`:
  - `/admin/config` (GET/PUT), `/admin/users` (GET/PATCH), `/admin/stats`, `/admin/audit-logs`, `/admin/payment-accounts/*`
  - server.py redus de la 2406 la ~2150 linii
- **Nou modul**: `backend/marketplace_routes.py` cu APIRouter pentru jobs + contracts + seap status
- **Frontend nou**: `Jobs.jsx` + `Contracts.jsx` cu testid-uri și forma de creare admin
- **Sidebar updates**: 2 link-uri noi în secțiunea Business

### V5.5 (2026-02-07) — Repository Unification + Lost Features Recovery
- **Deep repository audit**: scanned all 244 commits across `main`, `gh/main`, `gh2/main` for ever-implemented files; confirmed local copy is strictly ahead.
- **EnergyAdvisor (Claude Sonnet 4.6) restored** from commit `81b3b77` (lost in a regression):
  - `/app/backend/ai_chatbot.py` — chat sessions persistence in `db.chatbot_sessions`, LLM via emergentintegrations.
  - `/app/frontend/src/pages/EnergyAdvisor.jsx` — full session UI (history sidebar, suggestions, delete).
  - 5 new endpoints: `POST /api/chatbot/message`, `GET/POST /api/chatbot/sessions`, `GET/DELETE /api/chatbot/sessions/{id}`.
  - Sidebar link "Consultant AI (Claude)" → route `/consultant-ai` (ProtectedRoute).
  - Models added: `ChatbotMessage`, `ChatbotSessionCreate`.

## Roadmap

### P0 (next iteration)
- Refactor `server.py` (2400+ lines) — extract `/admin/*` into `backend/routes/admin.py` (similar to existing forum.py pattern).
- Consolidate `is_developer` → `is_admin` mapping into `_user_from_doc` only.
- Push to GitHub via "Save to Github" (PAT in env returns 401; user action required).

### P1 (planned)
- SEAP/SICAP alerts AI agent.
- 4 specialized AI agents (Producer/User/Client/Developer).
- Subscribers/contracts CRM with recurring fees.
- Job marketplace for autorizati ANRE.
- Automated reports + ANAF e-Factura integration.
- Legal document automation (contracts, notary submissions).
- Brand merchandise + partner network.
- Voluntariat (CSR tracking).
- Developer SDK + API access tier.

### P2 (futurist — opt-in)
- Mobile apps (iOS + Android).
- Real-time collaborative design canvas.
- BIM integration (Revit/AutoCAD).

## Key DB Schema (current)
```
users           : { user_id, email, name, password_hash?, auth_provider, plan, gmail_user?, gmail_app_password?, secondary_email?, is_developer, is_admin, is_banned, qes_provider?, qes_credentials?, active_project_id?, gdpr_consent, created_at }
projects        : { project_id, user_id, name, beneficiar, ..., photovoltaic_data?, photovoltaic_results?, technical_data?, created_at }
admin_config    : { config_id:"global", smtp_from_name, smtp_global_user?, smtp_global_password?, smtp_cc_secondary_default, feature_*_enabled (6 flags), maintenance_mode, maintenance_message, announcement_banner, announcement_level, updated_at, updated_by }
action_logs     : { log_id, user_id, action, details, created_at }
forum_threads   : { thread_id, author_id, author_name, industry, title, body, tags, pinned, is_developer_post, reply_count, likes, views, last_activity_at }
documents       : { doc_id, user_id, project_id, name, content_bytes, created_at }
payment_transactions : { tx_id, user_id, stripe_session_id, plan, amount, status, created_at }
```

## Key API Endpoints (V5.4 admin)
| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| `GET` | `/api/admin/config` | admin | Read global config |
| `PUT` | `/api/admin/config` | admin | Update + audit-log |
| `GET` | `/api/admin/stats` | admin | Counters |
| `GET` | `/api/admin/users` | admin | List/search (limit, search) |
| `PATCH` | `/api/admin/users/{id}` | admin | Updates + returns updated user |
| `GET` | `/api/system/banner` | public | Maintenance + announcement |
| `GET` | `/api/photovoltaic/tech-offer-pdf` | user | Premium PDF download |
| `PATCH` | `/api/users/me` | user | Now accepts `secondary_email` |
| `GET` | `/api/users/me/email-config` | user | Now returns `secondary_email` |
| `POST` | `/api/chatbot/message` | user | Energy Consultant AI (Claude Sonnet 4.6) reply |
| `GET` | `/api/chatbot/sessions` | user | List user chat sessions |
| `POST` | `/api/chatbot/sessions` | user | Create empty session |
| `GET` | `/api/chatbot/sessions/{id}` | user | Get session with messages |
| `DELETE` | `/api/chatbot/sessions/{id}` | user | Delete session |
| `GET/POST` | `/api/dev/jobs` | admin | Job Board ANRE CRUD |
| `DELETE` | `/api/dev/jobs/{job_id}` | admin | Delete job posting |
| `GET` | `/api/jobs` | public | Public jobs feed (no auth) |
| `GET/POST` | `/api/dev/contracts` | admin | Contracts CRM CRUD |
| `DELETE` | `/api/dev/contracts/{ctr_id}` | admin | Delete contract |
| `GET` | `/api/seap/status` | admin | SEAP integration health |
| `GET/PUT` | `/api/admin/config` | admin | **Moved to admin_routes.py** |
| `GET/PATCH` | `/api/admin/users` | admin | **Moved to admin_routes.py** |
| `GET` | `/api/admin/stats` | admin | **Moved to admin_routes.py** |
| `*` | `/api/admin/payment-accounts/*` | admin | **Moved to admin_routes.py** |

## Test Credentials
See `/app/memory/test_credentials.md` — admin (`dragosserban95@gmail.com` / `Test12345`).

## Known Gaps / Mocked
- Forum is functional but lightly populated.
- AI Assistant uses Emergent LLM key — budget should be monitored via Profile → Universal Key.
- Mobile responsive review for AdminConfig table not yet pixel-tuned (works, but could be denser at <640px).
