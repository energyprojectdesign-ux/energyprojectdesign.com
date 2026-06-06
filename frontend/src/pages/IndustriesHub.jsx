import { useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import AppShell from '../components/AppShell';
import api from '../lib/api';
import {
  Flame, Zap, Radio, TrainFront, Building2, Sun, Droplets,
  Trash2, Wind, Leaf, Construction, Lightbulb, ArrowRight,
  CheckCircle2, Clock, Sparkles, Search, Compass, BarChart3, Layers,
} from 'lucide-react';

const INDUSTRY_META = {
  gas_engineering: { icon: Flame, color: 'text-orange-600', bg: 'bg-orange-50', accent: '#EA580C', order: 1 },
  electrical_engineering: { icon: Zap, color: 'text-amber-600', bg: 'bg-amber-50', accent: '#D97706', order: 2 },
  telecom: { icon: Radio, color: 'text-sky-600', bg: 'bg-sky-50', accent: '#0284C7', order: 3 },
  railway_infra: { icon: TrainFront, color: 'text-slate-700', bg: 'bg-slate-100', accent: '#334155', order: 4 },
  civil_engineering: { icon: Building2, color: 'text-stone-700', bg: 'bg-stone-100', accent: '#44403C', order: 5 },
  photovoltaic: { icon: Sun, color: 'text-yellow-600', bg: 'bg-yellow-50', accent: '#CA8A04', order: 6 },
  water_sewage: { icon: Droplets, color: 'text-blue-600', bg: 'bg-blue-50', accent: '#2563EB', order: 7 },
  sanitation: { icon: Trash2, color: 'text-green-700', bg: 'bg-green-50', accent: '#15803D', order: 8 },
  hvac: { icon: Wind, color: 'text-cyan-600', bg: 'bg-cyan-50', accent: '#0891B2', order: 9 },
  environment: { icon: Leaf, color: 'text-emerald-600', bg: 'bg-emerald-50', accent: '#059669', order: 10 },
  roads_bridges: { icon: Construction, color: 'text-zinc-700', bg: 'bg-zinc-100', accent: '#3F3F46', order: 11 },
  public_lighting: { icon: Lightbulb, color: 'text-yellow-500', bg: 'bg-yellow-50', accent: '#EAB308', order: 12 },
  construction: { icon: Building2, color: 'text-stone-700', bg: 'bg-stone-100', accent: '#44403C', order: 13 },
};

export default function IndustriesHub() {
  const [industries, setIndustries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get('/industries');
        const sorted = (data || []).sort((a, b) => (INDUSTRY_META[a.id]?.order || 99) - (INDUSTRY_META[b.id]?.order || 99));
        setIndustries(sorted);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []);

  const totalSubdomains = industries.reduce((acc, i) => acc + (i.subdomains?.length || 0), 0);
  const activeSubdomains = industries.reduce((acc, i) => acc + (i.subdomains?.filter((s) => s.active).length || 0), 0);

  const filtered = useMemo(() => {
    return industries.filter((ind) => {
      const isActive = ind.subdomains?.filter((s) => s.active).length === ind.subdomains?.length && ind.subdomains?.length > 0;
      if (statusFilter === 'active' && !(ind.status === 'active' && isActive)) return false;
      if (statusFilter === 'partial' && !(ind.status === 'active' && !isActive)) return false;
      if (statusFilter === 'coming' && ind.status === 'active') return false;
      if (query && !(ind.name?.toLowerCase().includes(query.toLowerCase()) || ind.tagline?.toLowerCase().includes(query.toLowerCase()))) return false;
      return true;
    });
  }, [industries, query, statusFilter]);

  return (
    <AppShell title="Industrii" subtitle="12 industrii susținute + 1 extensie · roadmap de 158 subdomenii">
      {/* Hero */}
      <div className="relative overflow-hidden mb-10 bg-gradient-to-br from-[#0A0A0A] via-[#171717] to-[#0A0A0A] text-white" data-testid="industries-hero">
        <div className="absolute -right-32 -top-32 w-[480px] h-[480px] bg-[#FFB300]/15 blur-[140px] rounded-full pointer-events-none" />
        <div className="absolute inset-0 opacity-[0.05] pointer-events-none" style={{ backgroundImage: 'linear-gradient(#FFB300 1px, transparent 1px), linear-gradient(90deg, #FFB300 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
        <div className="relative p-8 lg:p-12 grid lg:grid-cols-12 gap-8 items-end">
          <div className="lg:col-span-7">
            <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-[#FFB300] mb-4">
              <Compass className="w-3.5 h-3.5" /> // industry coverage
            </div>
            <h1 className="text-4xl lg:text-5xl font-bold leading-[1.05] tracking-tight mb-4">
              12 industrii.<br />
              <span className="text-[#FFB300]">Un singur ecosistem.</span>
            </h1>
            <p className="text-base text-gray-300 leading-relaxed max-w-2xl">
              De la <span className="text-white font-semibold">gaze naturale</span> și <span className="text-white font-semibold">fotovoltaic</span> până la <span className="text-white font-semibold">drumuri și telecomunicații</span> — un singur stack pentru toate proiectele de infrastructură energetică din România.
            </p>
          </div>
          <div className="lg:col-span-5 grid grid-cols-3 gap-3">
            <Stat value={industries.length} label="Industrii" accent="text-[#FFB300]" />
            <Stat value={`${activeSubdomains}/${totalSubdomains}`} label="Subdomenii active" accent="text-emerald-400" />
            <Stat value={158} label="Plan roadmap" accent="text-sky-400" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-8 flex flex-col lg:flex-row gap-4 items-stretch lg:items-center">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Caută industrie sau subdomeniu…"
            className="w-full pl-11 pr-4 py-2.5 border border-gray-200 text-sm rounded-sm focus:outline-none focus:border-[#FFB300] focus:ring-2 focus:ring-[#FFB300]/30 bg-white"
            data-testid="industries-search"
          />
        </div>
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {[
            { v: 'all', l: 'Toate' },
            { v: 'active', l: 'Active' },
            { v: 'partial', l: 'Parțiale' },
            { v: 'coming', l: 'În curând' },
          ].map((f) => (
            <button
              key={f.v}
              onClick={() => setStatusFilter(f.v)}
              data-testid={`industry-filter-${f.v}`}
              className={`text-[11px] uppercase tracking-wider font-semibold px-3 py-1.5 border transition-all whitespace-nowrap ${statusFilter === f.v ? 'bg-black text-[#FFB300] border-black' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-400'}`}
            >{f.l}</button>
          ))}
        </div>
      </div>

      {loading && <div className="text-sm text-gray-500 py-12 text-center">Se încarcă industriile…</div>}

      {/* Grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="industries-grid">
        {filtered.map((ind, idx) => {
          const meta = INDUSTRY_META[ind.id] || { icon: Building2, color: 'text-gray-700', bg: 'bg-gray-50', accent: '#6B7280' };
          const Icon = meta.icon;
          const activeCount = ind.subdomains?.filter((s) => s.active).length || 0;
          const totalCount = ind.subdomains?.length || 0;
          const isFullyActive = ind.status === 'active' && activeCount === totalCount && totalCount > 0;
          const progressPct = totalCount > 0 ? Math.round((activeCount / totalCount) * 100) : 0;
          return (
            <Link
              key={ind.id}
              to={`/industrii/${ind.id}`}
              data-testid={`industry-card-${ind.id}`}
              className="group relative bg-white border border-gray-200 hover:border-black hover:shadow-[0_12px_36px_rgba(0,0,0,0.08)] transition-all duration-300 p-6 overflow-hidden"
              style={{ animationDelay: `${idx * 30}ms` }}
            >
              <div className="absolute -right-10 -top-10 w-32 h-32 rounded-full blur-2xl opacity-0 group-hover:opacity-40 transition-opacity duration-500 pointer-events-none" style={{ backgroundColor: meta.accent }} />
              <div className="relative flex items-start justify-between mb-4">
                <div className={`w-14 h-14 ${meta.bg} ${meta.color} flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                  <Icon className="w-7 h-7" strokeWidth={2} />
                </div>
                {isFullyActive ? (
                  <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-[0.15em] text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-1 font-semibold">
                    <CheckCircle2 className="w-3 h-3" /> Activă
                  </span>
                ) : ind.status === 'active' ? (
                  <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-[0.15em] text-amber-800 bg-amber-50 border border-amber-200 px-2 py-1 font-semibold">
                    <Sparkles className="w-3 h-3" /> Parțial
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-[0.15em] text-gray-500 bg-gray-50 border border-gray-200 px-2 py-1 font-semibold">
                    <Clock className="w-3 h-3" /> În curând
                  </span>
                )}
              </div>
              <h3 className="font-bold text-lg leading-tight mb-1 group-hover:text-black">{ind.name}</h3>
              <p className="text-sm text-gray-600 leading-relaxed mb-5 line-clamp-2">{ind.tagline}</p>

              {/* Progress bar */}
              <div className="mb-3">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold">Acoperire</span>
                  <span className="text-[11px] font-bold tracking-tight" style={{ color: meta.accent }}>{progressPct}%</span>
                </div>
                <div className="h-1 bg-gray-100 overflow-hidden">
                  <div className="h-full transition-all duration-500" style={{ width: `${progressPct}%`, backgroundColor: meta.accent }} />
                </div>
              </div>
              <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                <div className="text-xs text-gray-500">
                  <span className="font-mono font-bold text-black">{activeCount}</span>/{totalCount} subdomenii
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-black group-hover:translate-x-1 transition-all" />
              </div>
            </Link>
          );
        })}
      </div>

      {filtered.length === 0 && !loading && (
        <div className="text-center py-16 text-sm text-gray-400">Nicio industrie nu corespunde filtrelor.</div>
      )}

      {/* Roadmap */}
      <div className="mt-12 relative overflow-hidden bg-black text-white p-8 lg:p-10 border-l-4 border-[#FFB300]" data-testid="industries-roadmap">
        <div className="absolute -right-16 -bottom-16 w-64 h-64 bg-[#FFB300]/10 blur-3xl rounded-full pointer-events-none" />
        <div className="relative flex items-start gap-5">
          <div className="w-12 h-12 bg-[#FFB300] text-black flex items-center justify-center shrink-0">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <div className="text-[10px] uppercase tracking-[0.25em] text-[#FFB300] mb-2">// roadmap acoperire</div>
            <h3 className="text-2xl font-bold tracking-tight mb-3">158 subdomenii planificate</h3>
            <p className="text-sm text-gray-300 leading-relaxed max-w-3xl">
              Industrii prioritare în ordinea complexității: <strong className="text-white">Electrică</strong> (25 subdomenii), <strong className="text-white">Apă & canalizare</strong> (23), <strong className="text-white">Gaze</strong> (20), <strong className="text-white">Drumuri & poduri</strong> (18). Detalii complete în <span className="font-mono text-[#FFB300]">docs/INDUSTRIES_ROADMAP.md</span>.
            </p>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function Stat({ value, label, accent }) {
  return (
    <div className="bg-white/5 backdrop-blur-md border border-white/10 p-4">
      <div className={`text-3xl font-bold tracking-tight ${accent}`}>{value}</div>
      <div className="text-[10px] uppercase tracking-[0.2em] text-gray-400 mt-2">{label}</div>
    </div>
  );
}
