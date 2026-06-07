import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import AppShell from '../components/AppShell';
import api from '../lib/api';
import { toast } from 'sonner';
import {
  Flame, ArrowLeft, ArrowRight, Save, CheckCircle2, Circle, Lock, FileSignature,
  QrCode, Eye, Trash2, Plus, ShieldCheck, AlertCircle, Loader2, Stamp as StampIcon,
} from 'lucide-react';

// =========================  LIST  =========================
function GasProjectsList() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  useEffect(() => { (async () => {
    try { const { data } = await api.get('/gas-project'); setItems(data); }
    catch (e) { toast.error('Eroare încărcare proiecte'); }
    finally { setLoading(false); }
  })(); }, []);

  async function createNew() {
    try {
      const { data } = await api.post('/gas-project', { title: `Proiect gaz #${Date.now().toString().slice(-4)}` });
      toast.success('Proiect creat');
      navigate(`/gaze-naturale/${data.pid}`);
    } catch (e) { toast.error('Eroare creare proiect'); }
  }

  return (
    <AppShell title="Gaze Naturale — Studio" subtitle="Proiecte tehnice cu 11 faze legale (NTPEE 2018 + HG 907/2016)">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="label mb-2">// proiectele tale</div>
          <h3 className="text-xl font-semibold tracking-tight">Toate proiectele de gaze</h3>
        </div>
        <button onClick={createNew} className="amber-btn" data-testid="gas-create-btn">
          <Plus className="w-4 h-4" /> Proiect nou
        </button>
      </div>

      {loading ? (
        <div className="text-sm text-gray-500">Se încarcă…</div>
      ) : items.length === 0 ? (
        <div className="border border-dashed border-gray-300 p-12 text-center">
          <Flame className="w-10 h-10 mx-auto text-gray-400 mb-3" />
          <div className="text-sm text-gray-600 mb-4">Niciun proiect încă. Începe primul tău proiect tehnic.</div>
          <button onClick={createNew} className="amber-btn" data-testid="gas-create-empty">
            <Plus className="w-4 h-4" /> Creează primul proiect
          </button>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-px bg-gray-200 border border-gray-200">
          {items.map((p) => (
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
    </AppShell>
  );
}

// =========================  FIELD  =========================
function FieldInput({ field, value, onChange }) {
  const common = "w-full border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-black focus:ring-2 focus:ring-black/15 bg-white";
  if (field.type === 'textarea') {
    return (
      <textarea
        className={common}
        rows={3}
        placeholder={field.placeholder || ''}
        value={value || ''}
        onChange={(e) => onChange(field.key, e.target.value)}
        data-testid={`gas-field-${field.key}`}
      />
    );
  }
  if (field.type === 'select') {
    return (
      <select className={common} value={value || ''} onChange={(e) => onChange(field.key, e.target.value)} data-testid={`gas-field-${field.key}`}>
        <option value="">—</option>
        {(field.options || []).map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
    );
  }
  return (
    <input
      type={field.type || 'text'}
      className={common}
      placeholder={field.placeholder || ''}
      value={value || ''}
      onChange={(e) => onChange(field.key, e.target.value)}
      data-testid={`gas-field-${field.key}`}
    />
  );
}

// =========================  STUDIO  =========================
function GasProjectStudio() {
  const { pid } = useParams();
  const navigate = useNavigate();
  const [proj, setProj] = useState(null);
  const [phases, setPhases] = useState([]);
  const [activePhase, setActivePhase] = useState('tema');
  const [data, setData] = useState({});
  const [saving, setSaving] = useState(false);
  const [signing, setSigning] = useState(false);
  const [qrModal, setQrModal] = useState(null);
  const [previewMode, setPreviewMode] = useState(false);
  const [stamps, setStamps] = useState([]);
  const [selectedStamp, setSelectedStamp] = useState('');

  useEffect(() => { (async () => {
    try {
      const { data: p } = await api.get(`/gas-project/${pid}`);
      setProj(p); setPhases(p.phases_schema || []); setData(p.data || {});
      setActivePhase(p.phase || 'tema');
      try { const { data: st } = await api.get('/stamps'); setStamps(Array.isArray(st) ? st : (st?.stamps || [])); } catch (_) { /* stamps optional */ }
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
      try { await api.patch(`/gas-project/${pid}`, { phase: next }); } catch (_) { /* non-blocking */ }
    }
  }
  function prevPhase() {
    if (phaseIdx > 0) setActivePhase(phases[phaseIdx - 1].id);
  }

  async function signProject() {
    if (overall.percent < 70) {
      toast.error(`Proiect prea incomplet pentru semnătură (${overall.percent}% < 70%)`);
      return;
    }
    setSigning(true);
    try {
      await save();
      const { data: res } = await api.post(`/gas-project/${pid}/sign`, { stamp_id: selectedStamp || null });
      toast.success(`Proiect semnat digital · hash ${res.signature_hash.slice(0, 12)}…`);
      const { data: refreshed } = await api.get(`/gas-project/${pid}`);
      setProj(refreshed);
      showQr();
    } catch (e) { toast.error(e?.response?.data?.detail || 'Eroare semnătură'); }
    finally { setSigning(false); }
  }

  async function showQr() {
    try {
      const { data: qr } = await api.get(`/gas-project/${pid}/qr`);
      setQrModal(qr);
    } catch (e) { toast.error('Eroare QR'); }
  }

  // Bind Escape to close QR modal
  useEffect(() => {
    if (!qrModal) return undefined;
    const onKey = (e) => { if (e.key === 'Escape') setQrModal(null); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [qrModal]);

  async function removeProject() {
    if (!window.confirm('Ștergi acest proiect? (soft delete)')) return;
    try { await api.delete(`/gas-project/${pid}`); toast.success('Șters'); navigate('/gaze-naturale'); }
    catch (e) { toast.error('Eroare ștergere'); }
  }

  if (!proj) return <AppShell title="Studio" subtitle="…"><div className="text-sm text-gray-500">Se încarcă…</div></AppShell>;

  return (
    <AppShell title={proj.title} subtitle={`Gaze naturale · 11 faze legale · ${overall.percent}% completat`}>
      <Link to="/gaze-naturale" className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-black mb-4" data-testid="gas-back">
        <ArrowLeft className="w-3 h-3" /> Înapoi la proiecte
      </Link>

      {/* Header */}
      <div className="bg-black text-white p-6 mb-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4 flex-1">
            <div className="w-12 h-12 bg-[#FFB300] text-black flex items-center justify-center shrink-0"><Flame className="w-6 h-6" /></div>
            <div className="flex-1">
              <input
                type="text"
                value={proj.title}
                disabled={isSigned}
                onChange={(e) => setProj((p) => ({ ...p, title: e.target.value }))}
                onBlur={() => api.patch(`/gas-project/${pid}`, { title: proj.title }).catch(() => {})}
                className="bg-transparent text-2xl font-bold tracking-tight w-full focus:outline-none border-b border-transparent focus:border-[#FFB300]"
                data-testid="gas-title-input"
              />
              <div className="text-xs text-gray-400 mt-1">PID: <span className="mono">{proj.pid}</span></div>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {isSigned && <span className="text-[10px] uppercase tracking-wider bg-green-500/15 text-green-300 px-3 py-1.5 flex items-center gap-1" data-testid="gas-signed-badge"><ShieldCheck className="w-3 h-3" />Semnat digital</span>}
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
          <div className="label mb-3">// 11 faze legale</div>
          <div className="border border-gray-200 bg-white" data-testid="gas-phases-list">
            {phases.map((p) => {
              const isActive = p.id === activePhase;
              const filled = p.fields.filter((f) => String(data[f.key] || '').trim()).length;
              const pct = p.fields.length ? Math.round(100 * filled / p.fields.length) : 0;
              const done = pct === 100;
              return (
                <button
                  key={p.id}
                  onClick={() => setActivePhase(p.id)}
                  className={`w-full text-left p-3 border-b border-gray-200 last:border-b-0 hover:bg-gray-50 ${isActive ? 'bg-amber-50 border-l-4 border-l-[#FFB300]' : ''}`}
                  data-testid={`gas-phase-tab-${p.id}`}
                >
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

          {/* Digital signature panel */}
          <div className="mt-6 border border-gray-200 bg-white p-4">
            <div className="label mb-2">// semnătură digitală</div>
            <div className="text-xs text-gray-600 mb-3">Selectează o ștampilă/semnătură QES și semnează. Va genera hash SHA-256 + QR de verificare.</div>
            {stamps.length === 0 ? (
              <Link to="/stamps" className="text-xs text-black underline" data-testid="gas-upload-stamp-link">+ Încarcă ștampilă</Link>
            ) : (
              <select value={selectedStamp} onChange={(e) => setSelectedStamp(e.target.value)} className="w-full border border-gray-300 px-2 py-1.5 text-xs mb-3" data-testid="gas-stamp-select" disabled={isSigned}>
                <option value="">— alege ștampilă —</option>
                {stamps.map((s) => <option key={s.sid || s.stamp_id} value={s.sid || s.stamp_id}>{s.name || s.label || (s.sid || s.stamp_id)}</option>)}
              </select>
            )}
            <button
              onClick={signProject}
              disabled={signing || isSigned || overall.percent < 70}
              className="amber-btn w-full justify-center text-xs disabled:opacity-50"
              data-testid="gas-sign-btn"
            >
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

              {/* Deliverables */}
              <div className="bg-amber-50 border-l-4 border-[#FFB300] p-3 mb-5 text-xs">
                <div className="font-semibold mb-1">Livrabile faza:</div>
                <ul className="list-disc list-inside text-gray-700 space-y-0.5">
                  {phase.deliverables.map((d, i) => <li key={i}>{d}</li>)}
                </ul>
              </div>

              {/* Fields */}
              <div className="grid sm:grid-cols-2 gap-4 mb-6">
                {phase.fields.map((f) => (
                  <div key={f.key} className={f.type === 'textarea' ? 'sm:col-span-2' : ''}>
                    <label className="block text-xs font-semibold mb-1">
                      {f.label} {f.required && <span className="text-red-500">*</span>}
                    </label>
                    <FieldInput field={f} value={data[f.key]} onChange={onField} />
                  </div>
                ))}
              </div>

              {/* Phase progress */}
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
                  <button onClick={nextPhase} disabled={phaseIdx === phases.length - 1} className="amber-btn text-xs ml-auto" data-testid="gas-next-phase">
                    Faza următoare <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          ) : null}
        </main>
      </div>

      {/* QR modal */}
      {qrModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={() => setQrModal(null)}>
          <div className="bg-white max-w-md w-full p-6" onClick={(e) => e.stopPropagation()} data-testid="gas-qr-modal">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="label">// cod qr verificare</div>
                <h3 className="text-lg font-semibold">Verificare publică proiect</h3>
              </div>
              <button onClick={() => setQrModal(null)} className="text-gray-400 hover:text-black text-xl leading-none">×</button>
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
      )}
    </AppShell>
  );
}

// =========================  ROUTER WRAPPER  =========================
export default function GasNaturalProject() {
  const { pid } = useParams();
  if (pid) return <GasProjectStudio />;
  return <GasProjectsList />;
}
