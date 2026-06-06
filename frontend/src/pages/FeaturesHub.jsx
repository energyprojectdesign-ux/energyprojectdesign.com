import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import AppShell from '../components/AppShell';
import {
  Bot, Building2, Briefcase, Users, Award, Mail, Scale, HeartHandshake,
  Wrench, ArrowRight, Sparkles, Search, Filter, Compass, CheckCircle2, Clock,
  Loader2, Layers,
} from 'lucide-react';

const FEATURE_HUB = [
  { id: 'seap', icon: Search, title: 'SEAP Alerts', desc: 'AI agent care monitorizează SEAP/SICAP și notifică zilnic firmele despre licitațiile relevante din 12 industrii.', status: 'planned', tag: 'AI · Procurement' },
  { id: 'ai-agents', icon: Bot, title: '4 AI Agents', desc: 'Producer / User / Client / Developer — 4 asistenți inteligenți specializați pe fluxuri B2B end-to-end.', status: 'skeleton', tag: 'Multi-Agent' },
  { id: 'subscribers', icon: Users, title: 'Abonați & Contracte', desc: 'Bază clienți cu tarife, chirii recurente, contracte și recomandări AI personalizate per industrie.', status: 'planned', tag: 'CRM' },
  { id: 'jobs', icon: Briefcase, title: 'Job Opportunities', desc: 'Marketplace pentru proiectanți autorizați + matching automat cu firme afiliate și autorități.', status: 'planned', tag: 'Marketplace' },
  { id: 'reports', icon: Mail, title: 'Rapoarte automate', desc: 'Rapoarte lunare de activitate + declarare automată venituri fiscale (ANAF e-Factura, eDeclarații).', status: 'planned', tag: 'Fiscal · ANAF' },
  { id: 'legal-automation', icon: Scale, title: 'Automatizare juridică', desc: 'Generare automată contracte tip + transmitere către unități legale autorizate (notariat, registru).', status: 'planned', tag: 'Legal' },
  { id: 'partners', icon: Award, title: 'Parteneriate brand', desc: 'Merchandise oficial + parteneri inspiraționali (formare spirituală, self-help, dezvoltare personală).', status: 'planned', tag: 'Brand' },
  { id: 'volunteering', icon: HeartHandshake, title: 'Voluntariat', desc: 'Cauze caritabile, proiecte comunitate, social impact tracking — vizibil în profilul firmei.', status: 'planned', tag: 'Social' },
  { id: 'developer-plan', icon: Wrench, title: 'Developer Plan', desc: 'Pachet pentru dezvoltatori cu template-uri/funcții personalizate, SDK și acces direct la API intern.', status: 'planned', tag: 'API · SDK' },
  { id: 'community', icon: Building2, title: 'Comunitate', desc: 'Pagini per industrie/infrastructură cu discuții, sondaje, anunțuri, evenimente locale și networking.', status: 'partial', tag: 'Community' },
];

const STATUS_META = {
  active: { color: 'text-emerald-700', bg: 'bg-emerald-50', border: 'border-emerald-200', label: 'Activă', icon: CheckCircle2 },
  partial: { color: 'text-amber-800', bg: 'bg-amber-50', border: 'border-amber-200', label: 'Parțial', icon: Loader2 },
  skeleton: { color: 'text-sky-700', bg: 'bg-sky-50', border: 'border-sky-200', label: 'Schelet', icon: Layers },
  planned: { color: 'text-gray-600', bg: 'bg-gray-50', border: 'border-gray-200', label: 'Planificat', icon: Clock },
};

const STATUS_FILTERS = ['all', 'active', 'partial', 'skeleton', 'planned'];

export default function FeaturesHub() {
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState('all');

  const filtered = useMemo(() => {
    return FEATURE_HUB.filter((f) => {
      if (filter !== 'all' && f.status !== filter) return false;
      if (query && !(f.title.toLowerCase().includes(query.toLowerCase()) || f.desc.toLowerCase().includes(query.toLowerCase()))) return false;
      return true;
    });
  }, [query, filter]);

  const counts = useMemo(() => {
    const c = { all: FEATURE_HUB.length, active: 0, partial: 0, skeleton: 0, planned: 0 };
    FEATURE_HUB.forEach((f) => { c[f.status] = (c[f.status] || 0) + 1; });
    return c;
  }, []);

  return (
    <AppShell title="Feat-uri viziune" subtitle="10 module-far din roadmap-ul platformei — implementate progresiv pe baza feedback-ului">
      {/* HERO premium */}
      <div className="relative overflow-hidden mb-10 bg-gradient-to-br from-[#0A0A0A] via-[#171717] to-[#0A0A0A] text-white" data-testid="features-hero">
        <div className="absolute -right-24 -top-24 w-96 h-96 bg-[#FFB300]/15 blur-[120px] rounded-full pointer-events-none" />
        <div className="absolute -left-16 -bottom-16 w-72 h-72 bg-[#FFB300]/10 blur-[100px] rounded-full pointer-events-none" />
        <div className="absolute inset-0 opacity-[0.04] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#FFB300 1px, transparent 1px)', backgroundSize: '16px 16px' }} />
        <div className="relative p-8 lg:p-12 grid lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-7">
            <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-[#FFB300] mb-4">
              <Sparkles className="w-3.5 h-3.5" /> // viziune extinsă platformă
            </div>
            <h1 className="text-4xl lg:text-5xl font-bold leading-[1.05] tracking-tight mb-4">
              10 module noi.<br />
              <span className="text-[#FFB300]">Construcție incrementală.</span>
            </h1>
            <p className="text-base text-gray-300 leading-relaxed max-w-2xl">
              Identificate în <span className="text-white font-semibold">Feat-uri.docx</span> — viziunea originală a platformei. Fiecare modul are rută definită, layout vizibil și status etichetat. Implementarea profundă merge progresiv, ghidată de listele <span className="font-mono text-[#FFB300]">/app/memory/LIST_*</span>.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link to="/developer/progres" className="inline-flex items-center gap-2 px-4 py-2.5 bg-[#FFB300] text-black text-sm font-semibold uppercase tracking-wider hover:bg-white transition-colors" data-testid="link-progres">
                Vezi build progres <ArrowRight className="w-3.5 h-3.5" />
              </Link>
              <Link to="/industrii" className="inline-flex items-center gap-2 px-4 py-2.5 border border-white/20 text-white text-sm font-semibold uppercase tracking-wider hover:bg-white/5 transition-colors">
                <Compass className="w-3.5 h-3.5" /> 12 industrii
              </Link>
            </div>
          </div>
          <div className="lg:col-span-5 grid grid-cols-2 gap-3">
            {[
              { v: counts.active, l: 'Active', c: 'text-emerald-400' },
              { v: counts.partial, l: 'Parțiale', c: 'text-amber-400' },
              { v: counts.skeleton, l: 'Schelete', c: 'text-sky-400' },
              { v: counts.planned, l: 'Planificate', c: 'text-gray-400' },
            ].map((s) => (
              <div key={s.l} className="bg-white/5 backdrop-blur-md border border-white/10 p-5">
                <div className={`text-4xl font-bold tracking-tight ${s.c}`}>{s.v}</div>
                <div className="text-[10px] uppercase tracking-[0.2em] text-gray-400 mt-2">{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Filter bar */}
      <div className="mb-8 flex flex-col lg:flex-row gap-4 items-stretch lg:items-center" data-testid="features-filters">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Caută modul după nume sau descriere…"
            className="w-full pl-11 pr-4 py-2.5 border border-gray-200 text-sm rounded-sm focus:outline-none focus:border-[#FFB300] focus:ring-2 focus:ring-[#FFB300]/30 bg-white"
            data-testid="features-search"
          />
        </div>
        <div className="flex items-center gap-1.5 overflow-x-auto">
          <Filter className="w-3.5 h-3.5 text-gray-400 shrink-0" />
          {STATUS_FILTERS.map((s) => {
            const isActive = filter === s;
            const meta = STATUS_META[s];
            const label = s === 'all' ? 'Toate' : meta.label;
            return (
              <button
                key={s}
                onClick={() => setFilter(s)}
                data-testid={`filter-${s}`}
                className={`text-[11px] uppercase tracking-wider font-semibold px-3 py-1.5 border transition-all whitespace-nowrap ${isActive ? 'bg-black text-[#FFB300] border-black' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'}`}
              >
                {label} <span className="ml-1 opacity-70">{counts[s]}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Cards grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="features-grid">
        {filtered.map((f, idx) => {
          const Icon = f.icon;
          const meta = STATUS_META[f.status];
          const StatusIcon = meta.icon;
          return (
            <Link
              key={f.id}
              to={`/feat-uri/${f.id}`}
              data-testid={`feature-card-${f.id}`}
              className="group relative bg-white border border-gray-200 hover:border-black hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all duration-300 p-6 overflow-hidden"
              style={{ animationDelay: `${idx * 40}ms` }}
            >
              {/* Hover glow */}
              <div className="absolute -right-8 -top-8 w-32 h-32 bg-[#FFB300]/0 group-hover:bg-[#FFB300]/20 blur-2xl rounded-full transition-all duration-500 pointer-events-none" />

              <div className="relative flex items-start justify-between mb-4">
                <div className="w-12 h-12 bg-gray-50 text-gray-700 group-hover:bg-black group-hover:text-[#FFB300] flex items-center justify-center transition-all duration-300">
                  <Icon className="w-5 h-5" strokeWidth={2} />
                </div>
                <span className={`inline-flex items-center gap-1 text-[9px] uppercase tracking-[0.18em] font-semibold px-2 py-1 border ${meta.color} ${meta.bg} ${meta.border}`}>
                  <StatusIcon className={`w-3 h-3 ${f.status === 'partial' ? 'animate-spin' : ''}`} style={{ animationDuration: '3s' }} />
                  {meta.label}
                </span>
              </div>
              <div className="text-[9px] uppercase tracking-[0.22em] text-[#FFB300] font-semibold mb-1.5">{f.tag}</div>
              <h3 className="font-bold text-lg leading-tight mb-2 group-hover:text-black">{f.title}</h3>
              <p className="text-sm text-gray-600 leading-relaxed mb-5 line-clamp-3">{f.desc}</p>
              <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <span className="text-[10px] uppercase tracking-[0.2em] text-gray-400 font-mono">#{f.id}</span>
                <span className="inline-flex items-center gap-1 text-xs text-gray-500 group-hover:text-black font-semibold">
                  Detalii <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                </span>
              </div>
            </Link>
          );
        })}
      </div>
      {filtered.length === 0 && (
        <div className="text-center py-16 text-sm text-gray-400" data-testid="features-empty">Niciun modul nu corespunde filtrelor curente.</div>
      )}

      {/* Bottom info strip */}
      <div className="mt-12 grid lg:grid-cols-2 gap-px bg-gray-200 border border-gray-200">
        <div className="bg-white p-6 lg:p-8">
          <Sparkles className="w-6 h-6 text-[#FFB300] mb-3" />
          <h3 className="font-bold text-lg tracking-tight mb-2">De ce structură schelet?</h3>
          <p className="text-sm text-gray-600 leading-relaxed">
            Iterăm rapid pe baza feedback-ului real. Model: <strong className="text-black">structură de bază → implementare progresivă</strong>. Fiecare modul are rută, layout, status etichetat și listă îmbunătățiri planificate.
          </p>
        </div>
        <div className="bg-white p-6 lg:p-8">
          <Search className="w-6 h-6 text-gray-700 mb-3" />
          <h3 className="font-bold text-lg tracking-tight mb-2">Surse de planificare</h3>
          <ul className="text-xs text-gray-600 space-y-1.5 mono">
            <li><span className="text-[#FFB300]">▸</span> LIST_1_TODO.md — execuție strictă</li>
            <li><span className="text-[#FFB300]">▸</span> LIST_2_SUGGESTED.md — îmbunătățiri</li>
            <li><span className="text-[#FFB300]">▸</span> LIST_3_FUTURISTIC.md — opt-in</li>
            <li><span className="text-[#FFB300]">▸</span> LIST_4_BIG_UPDATE — research</li>
          </ul>
        </div>
      </div>
    </AppShell>
  );
}
