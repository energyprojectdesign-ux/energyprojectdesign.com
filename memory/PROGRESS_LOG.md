# Energy Project Design — Progress & Vision Log

## 2026-02-06 — V5.4 Release: Admin Hub + Secondary Email + Tech Offer PDF + Deep Polish

### Implementat în această sesiune
1. **Email business secundar (CC automat)** — câmp `secondary_email` în `User`. La trimiterea oricărui email prin platformă, dacă admin-config-ul are `smtp_cc_secondary_default=True`, adresa companiei utilizatorului este adăugată automat în CC.
2. **Admin-Only Configuration UI** — pagină `/admin/config` (vizibilă doar pentru `is_developer || is_admin`):
   - Mod mentenanță (toggle + mesaj)
   - Banner anunțuri global (4 niveluri: info / succes / warning / danger)
   - SMTP global fallback (from name / Gmail / app password / CC default)
   - Feature flags pentru 6 module (forum, email, PDF, fotovoltaic, AI assistant, payments)
   - Gestionare utilizatori (search, promote/demote admin, ban/unban)
   - Stats globale (utilizatori, admini, proiecte, documente, email-uri, discuții forum)
3. **Generate Tech Offer FV PDF** — buton nou pe pagina Calcul Fotovoltaic care apelează `/api/photovoltaic/tech-offer-pdf` și descarcă o ofertă tehnică A4 premium (hero kWp, ANRE, configurație, producție estimată, conformitate normativă, termeni comerciali, semnături).
4. **Deep UI polish** pe trei pagini-cheie:
   - **FeaturesHub** — hero glass-morphism cu dot-pattern, 10 module cu badge-uri de status (active/parțial/skelet/planificat), search + filter, cards cu hover glow.
   - **IndustriesHub** — hero cu grid-pattern, stats glass cards, search + status filter, cards cu progress bar colorată per industrie.
   - **Forum** — hero gradient cu metrici live (discuții/răspunsuri/like-uri), thread cards cu hover shadow.
5. **Audit logs** — fiecare modificare admin (config update, user update) este persistată în `db.action_logs`.
6. **Public banner endpoint** — `/api/system/banner` returnează mentenanță + anunț + feature flags (oricine, fără auth).

### Backend endpoints noi
| Method | Path | Auth | Descriere |
| --- | --- | --- | --- |
| `GET` | `/api/admin/config` | admin | Get global config |
| `PUT` | `/api/admin/config` | admin | Update config (audit-logged) |
| `GET` | `/api/admin/stats` | admin | Stats platformă |
| `GET` | `/api/admin/users` | admin | List/search users |
| `PATCH` | `/api/admin/users/{id}` | admin | Update role/ban/plan |
| `GET` | `/api/system/banner` | public | Maintenance + announcement |
| `GET` | `/api/photovoltaic/tech-offer-pdf` | user | Download Tech Offer FV PDF |

### Modificări modele
- `User` — adăugate `secondary_email`, `is_admin`, `is_banned`
- Modele noi: `AdminConfig`, `AdminConfigUpdate`, `AdminUserRoleUpdate`
- Colecție nouă: `admin_config` (singleton `{config_id: "global"}`)
- Colecție audit: `action_logs` (persistă fiecare acțiune admin)

### Viziune păstrată / extinsă
- Continuă **structură schelet → polish progresiv** ghidat de listele `/app/memory/LIST_*`.
- Următoarele direcții identificate (nu blocante):
  - Banner global propagat în AppShell pe baza `/api/system/banner` (right now polled lazy by AdminConfig only)
  - Audit log viewer ca tab în AdminConfig
  - Bulk actions pe lista utilizatori (export CSV, mass-ban)
  - Tech Offer PDF — variantă tip pentru gaze naturale (re-folosește `build_tech_offer_fv_pdf` pattern)

### Notă deploy
- Push GitHub: foloseste butonul **"Save to Github"** din chat input (write actions nu sunt suportate direct de agent).
