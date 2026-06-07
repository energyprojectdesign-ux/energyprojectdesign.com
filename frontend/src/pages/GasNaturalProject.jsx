import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import AppShell from '../components/AppShell';
import api from '../lib/api';
import { toast } from 'sonner';
import {
  Flame, ArrowLeft, ArrowRight, Save, CheckCircle2, Circle, Lock, FileSignature,
  QrCode, Eye, Trash2, Plus, ShieldCheck, AlertCircle, Loader2, Send, Globe,
  X, Mail, Building2, BookOpen, Calculator,
} from 'lucide-react';
import { PhaseCalcsPanel } from '../components/GasCalcWidgets';

// ====================================================================
// LIST / DASHBOARD — listing + create wizard
// ====================================================================
function GasProjectsList() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showWizard, setShowWizard] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => { void load(); }, []);
  async function load() {
    setLoading(true);
    try { const { data } = await api.get('/gas-project'); setItems(data); }
    catch (e) { toast.error('Eroare încărcare proiecte'); }
    finally { setLoading(false); }
  }

  const filtered = useMemo(() => {
    if (filter === 'all') return items;
    return items.filter((p) => p.subdomain === filter);
  }, [items, filter]);

  const subdomainCounts = useMemo(() => {
    const counts = {};
    items.forEach((p) => { counts[p.subdomain] = (counts[p.subdomain] || 0) + 1; });
    return counts;
  }, [items]);

  return (
    <AppShell title="Gaze Naturale — Studio" subtitle="Documentație tehnică reală conform NTPEE 2018 + HG 907/2016 + ANRE">
      {/* Industry overview card */}
      <IndustryOverview />

      <div className="flex items-center justify-between mt-8 mb-4">
        <div>
          <div className="label mb-2">// proiectele tale</div>
          <h3 className="text-xl font-semibold tracking-tight">Toate proiectele de gaze ({items.length})</h3>
        </div>
        <div className="flex items-center gap-2">
          <Link to="/gaze-naturale/recipients" className="ghost-btn text-xs" data-testid="gas-recipients-link">
            <Mail className="w-3 h-3" /> Destinatari autorități
          </Link>
          <button onClick={() => setShowWizard(true)} className="amber-btn" data-testid="gas-create-btn">
            <Plus className="w-4 h-4" /> Proiect nou
          </button>
        </div>
      </div>

      {/* Filter pills */}
      <div className="flex flex-wrap gap-2 mb-5" data-testid="gas-filter-pills">
        <button onClick={() => setFilter('all')}
          className={`px-3 py-1.5 text-xs border ${filter === 'all' ? 'bg-black text-white border-black' : 'bg-white border-gray-300'}`}>
          Toate ({items.length})
        </button>
        {Object.entries(subdomainCounts).map(([s, c]) => (
          <button key={s} onClick={() => setFilter(s)} data-testid={`gas-filter-${s}`}
            className={`px-3 py-1.5 text-xs border ${filter === s ? 'bg-black text-white border-black' : 'bg-white border-gray-300'}`}>
            {s} ({c})
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-sm text-gray-500">Se încarcă…</div>
      ) : filtered.length === 0 ? (
        <div className="border border-dashed border-gray-300 p-12 text-center">
          <Flame className="w-10 h-10 mx-auto text-gray-400 mb-3" />
          <div className="text-sm text-gray-600 mb-4">Niciun proiect încă. Începe primul tău proiect tehnic.</div>
          <button onClick={() => setShowWizard(true)} className="amber-btn" data-testid="gas-create-empty">
            <Plus className="w-4 h-4" /> Creează primul proiect
          </button>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-px bg-gray-200 border border-gray-200">
          {filtered.map((p) => (
            <Link key={p.pid} to={`/gaze-naturale/${p.pid}`} className="bg-white p-5 hover:bg-gray-50" data-testid={`gas-card-${p.pid}`}>
              <div className="flex items-start justify-between mb-3">
                <div className="w-10 h-10 bg-orange-50 text-orange-600 flex items-center justify-center"><Flame className="w-5 h-5" /></div>
                {p.status === 'signed' ? (
                  <span className="text-[10px] uppercase tracking-wider bg-green-50 text-green-700 px-2 py-1 flex items-center gap-1"><ShieldCheck className="w-3 h-3" />Semnat</span>
                ) : (
                  <span className="text-[10px] uppercase tracking-wider bg-gray-100 text-gray-600 px-2 py-1">{p.status || 'draft'}</span>
                )}
              </div>
              <div className="font-semibold mb-1 line-clamp-1">{p.title}</div>
              <div className="text-[10px] uppercase tracking-wider text-amber-700 mb-1">{p.subdomain || '—'}</div>
              <div className="text-xs text-gray-500 mb-3">{(p.data?.beneficiar_nume || '—')} · {p.data?.loc_consum_localitate || '—'}</div>
              <div className="flex items-center gap-2 text-xs">
                <div className="flex-1 h-1.5 bg-gray-100 overflow-hidden">
                  <div className="h-full bg-[#FFB300]" style={{ width: `${p.progress?.overall_percent || 0}%` }} />
                </div>
                <span className="mono text-[11px] text-gray-600">{p.progress?.overall_percent || 0}%</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {showWizard && <CreateWizard onClose={() => setShowWizard(false)} onCreated={() => { setShowWizard(false); load(); }} />}
    </AppShell>
  );
}

// ====================================================================
// INDUSTRY OVERVIEW — info banner
// ====================================================================
function IndustryOverview() {
  const [meta, setMeta] = useState(null);
  const [subdomains, setSubdomains] = useState([]);
  useEffect(() => { (async () => {
    try {
      const { data } = await api.get('/gas-project/catalog/RO/subdomains');
      setMeta(data.meta); setSubdomains(data.subdomains);
    } catch (_) { /* ignore */ }
  })(); }, []);
  if (!meta) return null;
  return (
    <div className="bg-gradient-to-br from-amber-50 to-white border border-amber-200 p-6" data-testid="gas-industry-overview">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-[#FFB300] text-black flex items-center justify-center shrink-0"><Flame className="w-6 h-6" /></div>
          <div>
            <div className="label mb-1">// industrie & cadru legal</div>
            <h2 className="text-2xl font-bold tracking-tight">{meta.industry_name} · Reglementator: {meta.regulator}</h2>
            <p className="text-xs text-gray-600 mt-1 max-w-2xl">Platformă pentru întocmirea reală a documentației tehnice electronice — multi-țară, multi-tipologie. {subdomains.length} ramuri active.</p>
          </div>
        </div>
        <div className="text-xs text-right shrink-0">
          <Globe className="w-3 h-3 inline mr-1" /> RO active · MD/BG/RS/UA roadmap
        </div>
      </div>
      <details className="mt-4">
        <summary className="text-xs font-semibold cursor-pointer hover:text-amber-700 flex items-center gap-1">
          <BookOpen className="w-3 h-3" /> {meta.primary_norms.length} norme legale aplicabile (click pentru detalii)
        </summary>
        <ul className="mt-2 text-xs space-y-1 list-disc list-inside text-gray-700">
          {meta.primary_norms.map((n, i) => <li key={i}>{n}</li>)}
        </ul>
      </details>
    </div>
  );
}

// ====================================================================
// CREATE WIZARD — pick subdomain
// ====================================================================
function CreateWizard({ onClose, onCreated }) {
  const [step, setStep] = useState(1);
  const [country, setCountry] = useState('RO');
  const [subdomain, setSubdomain] = useState(null);
  const [title, setTitle] = useState('');
  const [subdomains, setSubdomains] = useState([]);
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  useEffect(() => { (async () => {
    try { const { data } = await api.get(`/gas-project/catalog/${country}/subdomains`); setSubdomains(data.subdomains); }
    catch (e) { toast.error('Eroare încărcare subdomenii'); }
  })(); }, [country]);

  async function submit() {
    if (!subdomain) return;
    setCreating(true);
    try {
      const { data } = await api.post('/gas-project', {
        title: title.trim() || subdomain.name,
        country, subdomain: subdomain.id,
      });
      toast.success('Proiect creat');
      onCreated();
      navigate(`/gaze-naturale/${data.pid}`);
    } catch (e) { toast.error('Eroare creare'); }
    finally { setCreating(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={onClose} data-testid="gas-wizard">
      <div className="bg-white max-w-3xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="border-b border-gray-200 p-5 flex items-center justify-between">
          <div>
            <div className="label">// proiect nou — pas {step}/2</div>
            <h2 className="text-xl font-semibold">{step === 1 ? 'Alege ramura de gaze naturale' : 'Detalii proiect'}</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-black"><X className="w-5 h-5" /></button>
        </div>

        {step === 1 && (
          <div className="p-5">
            <div className="mb-4 flex items-center gap-2 text-xs">
              <Globe className="w-3 h-3" /> Țară: 
              <select value={country} onChange={(e) => setCountry(e.target.value)} className="border border-gray-300 px-2 py-1 text-xs" data-testid="wizard-country">
                <option value="RO">România</option>
              </select>
              <span className="text-gray-500">(alte țări — roadmap)</span>
            </div>
            <div className="grid sm:grid-cols-2 gap-3" data-testid="wizard-subdomains">
              {subdomains.map((s) => (
                <button key={s.id} onClick={() => { setSubdomain(s); setStep(2); }}
                  className="text-left border border-gray-200 hover:border-[#FFB300] hover:bg-amber-50 p-4 transition-all"
                  data-testid={`wizard-sub-${s.id}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] uppercase tracking-wider text-amber-700">{s.category}</span>
                    <span className="text-[10px] mono text-gray-500">{s.phases_count} faze</span>
                  </div>
                  <div className="font-semibold text-sm mb-1">{s.name}</div>
                  <div className="text-xs text-gray-600 mb-2">{s.description}</div>
                  <div className="text-[11px] text-gray-500"><strong>Regim:</strong> {s.regime}</div>
                  <div className="text-[11px] text-gray-500"><strong>Debit max:</strong> {s.max_debit_mc_h} m³/h</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {step === 2 && subdomain && (
          <div className="p-5 space-y-4">
            <div className="bg-amber-50 border-l-4 border-[#FFB300] p-3 text-xs">
              <strong>{subdomain.name}</strong> · {subdomain.regime}
              <div className="text-gray-600 mt-1">{subdomain.description}</div>
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1">Titlu proiect *</label>
              <input type="text" value={title} onChange={(e) => setTitle(e.target.value)}
                placeholder={`ex: ${subdomain.name} — beneficiar X`}
                className="w-full border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-black focus:ring-2 focus:ring-black/15"
                data-testid="wizard-title-input" autoFocus />
            </div>
            <div className="flex items-center justify-between pt-3 border-t border-gray-200">
              <button onClick={() => setStep(1)} className="ghost-btn text-xs" data-testid="wizard-back">
                <ArrowLeft className="w-3 h-3" /> Înapoi
              </button>
              <button onClick={submit} disabled={creating} className="amber-btn text-xs" data-testid="wizard-create">
                {creating ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                Creează proiect
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ====================================================================
// FIELD INPUT (with unit suffix)
// ====================================================================
function FieldInput({ field, value, onChange, disabled }) {
  const common = "w-full border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-black focus:ring-2 focus:ring-black/15 bg-white disabled:bg-gray-50";
  if (field.type === 'textarea') {
    return <textarea className={common} rows={3} placeholder={field.placeholder || ''} value={value || ''} disabled={disabled}
      onChange={(e) => onChange(field.key, e.target.value)} data-testid={`gas-field-${field.key}`} />;
  }
  if (field.type === 'select') {
    return (
      <select className={common} value={value || ''} disabled={disabled}
        onChange={(e) => onChange(field.key, e.target.value)} data-testid={`gas-field-${field.key}`}>
        <option value="">—</option>
        {(field.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    );
  }
  return (
    <div className="relative">
      <input
        type={field.type || 'text'} className={`${common} ${field.unit ? 'pr-14' : ''}`}
        placeholder={field.placeholder || ''} value={value || ''} disabled={disabled}
        onChange={(e) => onChange(field.key, e.target.value)}
        data-testid={`gas-field-${field.key}`}
      />
      {field.unit && <span className="absolute right-3 top-1/2 -translate-y-1/2 text-[11px] mono text-gray-500">{field.unit}</span>}
    </div>
  );
}

// ====================================================================
// DISPATCH MODAL — email a phase to authorities
// ====================================================================
function DispatchModal({ pid, phase, onClose }) {
  const [savedRecipients, setSavedRecipients] = useState({});
  const [emails, setEmails] = useState('');
  const [cc, setCc] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => { (async () => {
    try { const { data } = await api.get('/gas-project/recipients'); setSavedRecipients(data?.items || {}); }
    catch (_) { /* ignore */ }
  })(); }, []);

  function autoFill() {
    const roles = phase.recipients_default || [];
    const all = roles.flatMap((r) => savedRecipients[r] || []);
    setEmails(all.join(', '));
  }

  async function send() {
    const recipients = emails.split(/[,\s;]+/).map((e) => e.trim()).filter((e) => e.includes('@'));
    const ccList = cc.split(/[,\s;]+/).map((e) => e.trim()).filter((e) => e.includes('@'));
    if (recipients.length === 0) { toast.error('Adaugă cel puțin un destinatar'); return; }
    setSending(true);
    try {
      const { data } = await api.post(`/gas-project/${pid}/phase/${phase.id}/dispatch`,
        { recipients, cc: ccList, message });
      if (data.ok) toast.success(`Trimis către ${recipients.length} destinatari`);
      else toast.error(data.error || 'Eroare email');
      onClose();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Eroare dispatch');
    } finally { setSending(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={onClose} data-testid="gas-dispatch-modal">
      <div className="bg-white max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="border-b border-gray-200 p-5 flex items-center justify-between">
          <div>
            <div className="label">// trimite fază către autorități</div>
            <h2 className="text-lg font-semibold">{phase.name}</h2>
            <div className="text-[10px] mono text-gray-500">{phase.norm}</div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-black"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-5 space-y-4">
          <div className="bg-amber-50 border-l-4 border-[#FFB300] p-3 text-xs">
            <strong>Destinatari recomandați conform fazei:</strong>{' '}
            {phase.recipients_default?.join(', ') || '—'}
            <button onClick={autoFill} className="ml-2 underline text-amber-700" data-testid="dispatch-autofill">auto-completează din profilul tău</button>
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Destinatari principali (email, virgulă-separat) *</label>
            <input type="text" value={emails} onChange={(e) => setEmails(e.target.value)}
              placeholder="primaria@x.ro, distrigaz@y.ro"
              className="w-full border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-black focus:ring-2 focus:ring-black/15"
              data-testid="dispatch-emails" />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">CC (opțional)</label>
            <input type="text" value={cc} onChange={(e) => setCc(e.target.value)}
              className="w-full border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-black focus:ring-2 focus:ring-black/15"
              data-testid="dispatch-cc" />
          </div>
          <div>
            <label className="block text-xs font-semibold mb-1">Mesaj adițional (opțional)</label>
            <textarea value={message} onChange={(e) => setMessage(e.target.value)} rows={3}
              className="w-full border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-black focus:ring-2 focus:ring-black/15"
              data-testid="dispatch-message" />
          </div>
          <div className="text-[11px] text-gray-500">
            ℹ️ Va fi atașat un rezumat DOCX al fazei + datele introduse. Email-ul va fi trimis prin contul Gmail configurat în profilul tău (Setări → Email).
            Adresa secundară (business) va fi CC automat dacă e setată.
          </div>
        </div>
        <div className="border-t border-gray-200 p-4 flex items-center justify-end gap-2 bg-gray-50">
          <button onClick={onClose} className="ghost-btn text-xs">Anulează</button>
          <button onClick={send} disabled={sending} className="amber-btn text-xs" data-testid="dispatch-send">
            {sending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Send className="w-3 h-3" />} Trimite
          </button>
        </div>
      </div>
    </div>
  );
}

// ====================================================================
// STUDIO — main editor
// ====================================================================
function GasProjectStudio() {
  const { pid } = useParams();
  const navigate = useNavigate();
  const [proj, setProj] = useState(null);
  const [phases, setPhases] = useState([]);
  const [subdomainMeta, setSubdomainMeta] = useState(null);
  const [activePhase, setActivePhase] = useState('tema');
  const [data, setData] = useState({});
  const [saving, setSaving] = useState(false);
  const [signing, setSigning] = useState(false);
  const [qrModal, setQrModal] = useState(null);
  const [previewMode, setPreviewMode] = useState(false);
  const [showCalcs, setShowCalcs] = useState(false);
  const [stamps, setStamps] = useState([]);
  const [selectedStamp, setSelectedStamp] = useState('');
  const [dispatchPhase, setDispatchPhase] = useState(null);

  useEffect(() => { (async () => {
    try {
      const { data: p } = await api.get(`/gas-project/${pid}`);
      setProj(p); setPhases(p.phases_schema || []); setData(p.data || {});
      setSubdomainMeta(p.subdomain_meta || null);
      setActivePhase(p.phase || 'tema');
      try { const { data: st } = await api.get('/stamps'); setStamps(Array.isArray(st) ? st : (st?.stamps || [])); } catch (_) { /* ignore */ }
    } catch (e) {
      toast.error('Proiect inexistent');
      navigate('/gaze-naturale');
    }
  })(); }, [pid, navigate]);

  const phase = useMemo(() => phases.find((p) => p.id === activePhase), [phases, activePhase]);
  const phaseIdx = useMemo(() => phases.findIndex((p) => p.id === activePhase), [phases, activePhase]);

  const phaseProgress = useMemo(() => {
    if (!phase) return { filled: 0, total: 0, percent: 0 };
    const total = phase.fields.length;
    const filled = phase.fields.filter((f) => String(data[f.key] || '').trim()).length;
    return { filled, total, percent: total ? Math.round(100 * filled / total) : 0 };
  }, [phase, data]);

  const overall = useMemo(() => {
    const total = phases.reduce((acc, p) => acc + p.fields.length, 0);
    const filled = phases.reduce((acc, p) => acc + p.fields.filter((f) => String(data[f.key] || '').trim()).length, 0);
    return { filled, total, percent: total ? Math.round(100 * filled / total) : 0 };
  }, [phases, data]);

  const isSigned = proj?.status === 'signed';
  function onField(k, v) { if (!isSigned) setData((d) => ({ ...d, [k]: v })); }

  async function save() {
    setSaving(true);
    try {
      const { data: updated } = await api.patch(`/gas-project/${pid}`, { data, phase: activePhase });
      setProj(updated); setData(updated.data || {});
      toast.success('Salvat');
    } catch (e) { toast.error('Eroare la salvare'); }
    finally { setSaving(false); }
  }

  async function nextPhase() {
    if (phaseIdx < phases.length - 1) {
      const next = phases[phaseIdx + 1].id;
      await save();
      setActivePhase(next);
      try { await api.patch(`/gas-project/${pid}`, { phase: next }); } catch (_) { /* ignore */ }
    }
  }
  function prevPhase() { if (phaseIdx > 0) setActivePhase(phases[phaseIdx - 1].id); }

  async function signProject() {
    if (overall.percent < 70) { toast.error(`Proiect prea incomplet (${overall.percent}% < 70%)`); return; }
    setSigning(true);
    try {
      await save();
      const { data: res } = await api.post(`/gas-project/${pid}/sign`, { stamp_id: selectedStamp || null });
      toast.success(`Semnat digital · hash ${res.signature_hash.slice(0, 12)}…`);
      const { data: refreshed } = await api.get(`/gas-project/${pid}`);
      setProj(refreshed);
      showQr();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Eroare semnătură'); }
    finally { setSigning(false); }
  }

  async function showQr() {
    try { const { data: qr } = await api.get(`/gas-project/${pid}/qr`); setQrModal(qr); }
    catch (e) { toast.error('Eroare QR'); }
  }

  useEffect(() => {
    if (!qrModal && !dispatchPhase) return undefined;
    const onKey = (e) => { if (e.key === 'Escape') { setQrModal(null); setDispatchPhase(null); } };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [qrModal, dispatchPhase]);

  async function removeProject() {
    if (!window.confirm('Ștergi acest proiect? (soft delete)')) return;
    try { await api.delete(`/gas-project/${pid}`); toast.success('Șters'); navigate('/gaze-naturale'); }
    catch (e) { toast.error('Eroare ștergere'); }
  }

  if (!proj) return <AppShell title="Studio" subtitle="…"><div className="text-sm text-gray-500">Se încarcă…</div></AppShell>;

  return (
    <AppShell title={proj.title} subtitle={`${proj.subdomain} · ${overall.percent}% completat`}>
      <Link to="/gaze-naturale" className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-black mb-4" data-testid="gas-back">
        <ArrowLeft className="w-3 h-3" /> Înapoi la proiecte
      </Link>

      {/* Header */}
      <div className="bg-black text-white p-6 mb-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4 flex-1">
            <div className="w-12 h-12 bg-[#FFB300] text-black flex items-center justify-center shrink-0"><Flame className="w-6 h-6" /></div>
            <div className="flex-1">
              <input type="text" value={proj.title} disabled={isSigned}
                onChange={(e) => setProj((p) => ({ ...p, title: e.target.value }))}
                onBlur={() => api.patch(`/gas-project/${pid}`, { title: proj.title }).catch(() => {})}
                className="bg-transparent text-2xl font-bold tracking-tight w-full focus:outline-none border-b border-transparent focus:border-[#FFB300]"
                data-testid="gas-title-input" />
              <div className="text-xs text-gray-400 mt-1 flex flex-wrap gap-3">
                <span>PID: <span className="mono">{proj.pid}</span></span>
                <span>· Țară: {proj.country}</span>
                <span>· Subdomeniu: <strong className="text-amber-300">{proj.subdomain}</strong></span>
                {subdomainMeta?.regime && <span>· Regim: {subdomainMeta.regime}</span>}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {isSigned && <span className="text-[10px] uppercase tracking-wider bg-green-500/15 text-green-300 px-3 py-1.5 flex items-center gap-1" data-testid="gas-signed-badge"><ShieldCheck className="w-3 h-3" />Semnat</span>}
            <button onClick={() => setPreviewMode(!previewMode)} className="ghost-btn text-xs" data-testid="gas-preview-btn"><Eye className="w-3 h-3" /> Preview</button>
            <button onClick={showQr} className="ghost-btn text-xs" data-testid="gas-qr-btn"><QrCode className="w-3 h-3" /> QR</button>
          </div>
        </div>
        <div className="mt-5 flex items-center gap-2">
          <div className="flex-1 h-2 bg-white/10 overflow-hidden">
            <div className="h-full bg-[#FFB300] transition-all" style={{ width: `${overall.percent}%` }} data-testid="gas-overall-progress" />
          </div>
          <span className="mono text-xs text-gray-300">{overall.filled}/{overall.total} · {overall.percent}%</span>
        </div>
      </div>

      {/* Phases sidebar + form */}
      <div className="grid lg:grid-cols-12 gap-6">
        <aside className="lg:col-span-4">
          <div className="label mb-3">// {phases.length} faze legale</div>
          <div className="border border-gray-200 bg-white" data-testid="gas-phases-list">
            {phases.map((p) => {
              const isActive = p.id === activePhase;
              const filled = p.fields.filter((f) => String(data[f.key] || '').trim()).length;
              const pct = p.fields.length ? Math.round(100 * filled / p.fields.length) : 0;
              const done = pct === 100;
              return (
                <button key={p.id} onClick={() => setActivePhase(p.id)}
                  className={`w-full text-left p-3 border-b border-gray-200 last:border-b-0 hover:bg-gray-50 ${isActive ? 'bg-amber-50 border-l-4 border-l-[#FFB300]' : ''}`}
                  data-testid={`gas-phase-tab-${p.id}`}>
                  <div className="flex items-start gap-2.5">
                    <div className="mt-0.5">
                      {done ? <CheckCircle2 className="w-4 h-4 text-green-600" /> : <Circle className="w-4 h-4 text-gray-300" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-semibold leading-tight">{p.name}</div>
                      <div className="text-[10px] text-gray-500 mono mt-0.5">{p.norm}</div>
                      <div className="mt-1.5 flex items-center gap-1.5">
                        <div className="flex-1 h-1 bg-gray-200 overflow-hidden">
                          <div className="h-full bg-[#FFB300]" style={{ width: `${pct}%` }} />
                        </div>
                        <span className="mono text-[10px] text-gray-500">{filled}/{p.fields.length}</span>
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Signature panel */}
          <div className="mt-6 border border-gray-200 bg-white p-4">
            <div className="label mb-2">// semnătură digitală</div>
            <div className="text-xs text-gray-600 mb-3">Selectează o ștampilă/semnătură QES și semnează. Va genera hash SHA-256 + QR de verificare.</div>
            {stamps.length === 0 ? (
              <Link to="/stamps" className="text-xs text-black underline" data-testid="gas-upload-stamp-link">+ Încarcă ștampilă</Link>
            ) : (
              <select value={selectedStamp} onChange={(e) => setSelectedStamp(e.target.value)}
                className="w-full border border-gray-300 px-2 py-1.5 text-xs mb-3" data-testid="gas-stamp-select" disabled={isSigned}>
                <option value="">— alege ștampilă —</option>
                {stamps.map((s) => <option key={s.sid || s.stamp_id} value={s.sid || s.stamp_id}>{s.name || s.label || (s.sid || s.stamp_id)}</option>)}
              </select>
            )}
            <button onClick={signProject} disabled={signing || isSigned || overall.percent < 70}
              className="amber-btn w-full justify-center text-xs disabled:opacity-50" data-testid="gas-sign-btn">
              {signing ? <Loader2 className="w-3 h-3 animate-spin" /> : (isSigned ? <Lock className="w-3 h-3" /> : <FileSignature className="w-3 h-3" />)}
              {isSigned ? 'Deja semnat' : `Semnează digital (≥70% — acum ${overall.percent}%)`}
            </button>
            {proj?.signature_hash && (
              <div className="mt-3 text-[10px] mono break-all bg-gray-50 p-2 border-l-2 border-green-500" data-testid="gas-signature-hash">
                <div className="text-gray-500 mb-1">SHA-256</div>{proj.signature_hash}
              </div>
            )}
            <button onClick={removeProject} className="mt-3 text-[10px] text-red-600 hover:underline inline-flex items-center gap-1" data-testid="gas-delete-btn">
              <Trash2 className="w-3 h-3" /> Șterge proiect
            </button>
          </div>
        </aside>

        <main className="lg:col-span-8">
          {previewMode ? (
            <div className="bg-white border border-gray-200 p-6" data-testid="gas-preview">
              <div className="border-b border-gray-300 pb-4 mb-4">
                <div className="label">// preview proiect</div>
                <h2 className="text-2xl font-bold tracking-tight">{proj.title}</h2>
                <div className="text-xs text-gray-500 mt-1">PID: <span className="mono">{proj.pid}</span> · Beneficiar: {data.beneficiar_nume || '—'}</div>
              </div>
              {phases.map((p) => (
                <div key={p.id} className="mb-6">
                  <div className="font-semibold text-sm mb-2 border-l-4 border-[#FFB300] pl-3">{p.name}</div>
                  <div className="text-[11px] text-gray-500 mb-2 mono pl-3">{p.norm}</div>
                  <table className="w-full text-xs">
                    <tbody>
                      {p.fields.map((f) => (
                        <tr key={f.key} className="border-b border-gray-100">
                          <td className="py-1.5 pr-3 text-gray-600 align-top w-1/2">{f.label}</td>
                          <td className="py-1.5 text-gray-900 whitespace-pre-wrap">{data[f.key] || <span className="text-gray-300">—</span>}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>
          ) : phase ? (
            <div className="bg-white border border-gray-200 p-6" data-testid="gas-form-pane">
              <div className="flex items-baseline justify-between mb-1">
                <h2 className="text-xl font-semibold tracking-tight">{phase.name}</h2>
                <span className="text-xs text-gray-500 mono">{phaseIdx + 1}/{phases.length}</span>
              </div>
              <div className="text-[11px] mono text-gray-500 mb-3">{phase.norm}</div>
              <p className="text-xs text-gray-600 mb-5">{phase.description}</p>

              {/* Deliverables + recipients suggestion */}
              <div className="grid sm:grid-cols-2 gap-3 mb-5">
                <div className="bg-amber-50 border-l-4 border-[#FFB300] p-3 text-xs">
                  <div className="font-semibold mb-1">Livrabile faza:</div>
                  <ul className="list-disc list-inside text-gray-700 space-y-0.5">
                    {phase.deliverables.map((d, i) => <li key={i}>{d}</li>)}
                  </ul>
                </div>
                <div className="bg-blue-50 border-l-4 border-blue-500 p-3 text-xs">
                  <div className="font-semibold mb-1">Destinatari recomandați:</div>
                  <ul className="list-disc list-inside text-gray-700 space-y-0.5">
                    {(phase.recipients_default || []).map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              </div>

              {/* Fields */}
              <div className="grid sm:grid-cols-2 gap-4 mb-6">
                {phase.fields.map((f) => (
                  <div key={f.key} className={f.type === 'textarea' ? 'sm:col-span-2' : ''}>
                    <label className="block text-xs font-semibold mb-1">
                      {f.label} {f.required && <span className="text-red-500">*</span>}
                      {f.unit && <span className="text-[10px] mono text-gray-400 ml-1">({f.unit})</span>}
                    </label>
                    <FieldInput field={f} value={data[f.key]} onChange={onField} disabled={isSigned} />
                  </div>
                ))}
              </div>

              {/* Engineering calcs (collapsible) */}
              <div className="mb-6 border-t border-gray-200 pt-4">
                <button onClick={() => setShowCalcs(!showCalcs)} className="text-xs font-semibold flex items-center gap-2 hover:text-amber-700" data-testid="gas-toggle-calcs">
                  <Calculator className="w-3.5 h-3.5" />
                  {showCalcs ? 'Ascunde' : 'Arată'} calcule inginerești pentru această fază
                </button>
                {showCalcs && (
                  <div className="mt-3" data-testid="gas-calcs-panel">
                    <PhaseCalcsPanel phaseId={activePhase} />
                  </div>
                )}
              </div>

              {/* Phase progress + actions */}
              <div className="border-t border-gray-200 pt-4">
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex-1 h-1.5 bg-gray-100 overflow-hidden">
                    <div className="h-full bg-[#FFB300]" style={{ width: `${phaseProgress.percent}%` }} />
                  </div>
                  <span className="text-xs mono text-gray-600">{phaseProgress.filled}/{phaseProgress.total} · {phaseProgress.percent}%</span>
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  <button onClick={prevPhase} disabled={phaseIdx === 0} className="ghost-btn text-xs disabled:opacity-30" data-testid="gas-prev-phase">
                    <ArrowLeft className="w-3 h-3" /> Faza anterioară
                  </button>
                  <button onClick={save} disabled={saving || isSigned} className="outline-btn text-xs" data-testid="gas-save-btn">
                    {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />} Salvează
                  </button>
                  <button onClick={() => setDispatchPhase(phase)} disabled={phaseProgress.percent < 50}
                    title={phaseProgress.percent < 50 ? 'Faza trebuie completată ≥50% pentru dispatch' : ''}
                    className="ghost-btn text-xs disabled:opacity-40" data-testid="gas-dispatch-btn">
                    <Send className="w-3 h-3" /> Trimite faza către autorități
                  </button>
                  <button onClick={nextPhase} disabled={phaseIdx === phases.length - 1} className="amber-btn text-xs ml-auto" data-testid="gas-next-phase">
                    Faza următoare <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>

              {/* Dispatch log */}
              {proj.dispatches && proj.dispatches.filter((d) => d.phase_id === phase.id).length > 0 && (
                <div className="mt-6 border-t border-gray-200 pt-4" data-testid="gas-dispatch-log">
                  <div className="label mb-2">// istoric trimiteri pentru această fază</div>
                  <div className="space-y-2">
                    {proj.dispatches.filter((d) => d.phase_id === phase.id).map((d, i) => (
                      <div key={i} className="text-xs border-l-2 border-gray-300 pl-3">
                        <div className="flex items-center gap-2">
                          {d.ok ? <CheckCircle2 className="w-3 h-3 text-green-600" /> : <AlertCircle className="w-3 h-3 text-red-600" />}
                          <span className="mono text-[10px] text-gray-500">{d.sent_at?.slice(0, 19)}</span>
                          <span>către <strong>{d.recipients?.length || 0}</strong> destinatari</span>
                        </div>
                        {d.error && <div className="text-red-600 mt-1 text-[10px]">{d.error}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </main>
      </div>

      {/* Modals */}
      {qrModal && <QrModal qrModal={qrModal} pid={pid} onClose={() => setQrModal(null)} />}
      {dispatchPhase && <DispatchModal pid={pid} phase={dispatchPhase} onClose={() => setDispatchPhase(null)} />}
    </AppShell>
  );
}

function QrModal({ qrModal, pid, onClose }) {
  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white max-w-md w-full p-6" onClick={(e) => e.stopPropagation()} data-testid="gas-qr-modal">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="label">// cod qr verificare</div>
            <h3 className="text-lg font-semibold">Verificare publică proiect</h3>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-black text-xl leading-none">×</button>
        </div>
        <div className="bg-gray-50 p-4 flex items-center justify-center mb-3">
          <img src={qrModal.qr_png_b64} alt="QR" className="w-56 h-56" />
        </div>
        <div className="text-xs text-gray-700 break-all mono mb-2"><strong>URL:</strong> {qrModal.verify_url}</div>
        {qrModal.signature_hash && <div className="text-[10px] text-gray-500 break-all mono"><strong>SHA-256:</strong> {qrModal.signature_hash}</div>}
        <a href={qrModal.qr_png_b64} download={`${pid}_qr.png`} className="amber-btn w-full justify-center mt-4 text-xs" data-testid="gas-qr-download">
          <QrCode className="w-3 h-3" /> Descarcă PNG
        </a>
      </div>
    </div>
  );
}

// ====================================================================
// ROUTER WRAPPER
// ====================================================================
export default function GasNaturalProject() {
  const { pid } = useParams();
  if (pid) return <GasProjectStudio />;
  return <GasProjectsList />;
}
