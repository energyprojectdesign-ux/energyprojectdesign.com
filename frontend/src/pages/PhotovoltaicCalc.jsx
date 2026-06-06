import { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import api from '../lib/api';
import { toast } from 'sonner';
import { Sun, RefreshCw, Save, Zap, Cable, Shield, TrendingUp, Building2, FileJson, FileDown } from 'lucide-react';

const ZONE_OPTIONS = [
  { value: 'sud', label: 'Sud (Dobrogea, Bărăgan) — 1450 kWh/m²' },
  { value: 'sud_est', label: 'Sud-Est (Constanța, Tulcea) — 1430 kWh/m²' },
  { value: 'sud_vest', label: 'Sud-Vest (Mehedinți, Dolj) — 1380 kWh/m²' },
  { value: 'centru', label: 'Centru (Transilvania) — 1320 kWh/m²' },
  { value: 'nord_est', label: 'Nord-Est (Moldova) — 1280 kWh/m²' },
  { value: 'nord_vest', label: 'Nord-Vest (Maramureș, Bihor) — 1300 kWh/m²' },
  { value: 'implicit', label: 'Implicit (medie țară) — 1350 kWh/m²' },
];

const CATEGORY_TONE = {
  C1: 'bg-emerald-50 text-emerald-800 border-emerald-200',
  C2: 'bg-sky-50 text-sky-800 border-sky-200',
  C3: 'bg-amber-50 text-amber-800 border-amber-200',
  C4: 'bg-rose-50 text-rose-800 border-rose-200',
};

const DEFAULTS = {
  p_kwp: 8,
  p_panou_wp: 450,
  lungime_dc_m: 30,
  lungime_ac_m: 15,
  monofazat: false,
  zona_geografica: 'implicit',
};

export default function PhotovoltaicCalc() {
  const [form, setForm] = useState(DEFAULTS);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [savedAt, setSavedAt] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await api.get('/photovoltaic');
        if (data?.photovoltaic_data && Object.keys(data.photovoltaic_data).length) {
          setForm({ ...DEFAULTS, ...data.photovoltaic_data });
        }
        if (data?.photovoltaic_results && data.photovoltaic_results.status === 'ok') {
          setResults(data.photovoltaic_results);
        }
      } catch (e) { /* no project yet */ }
    })();
  }, []);

  const update = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const runCalc = async () => {
    setLoading(true);
    try {
      const payload = {
        ...form,
        p_kwp: Number(form.p_kwp),
        p_panou_wp: Number(form.p_panou_wp),
        lungime_dc_m: Number(form.lungime_dc_m),
        lungime_ac_m: Number(form.lungime_ac_m),
      };
      const { data } = await api.post('/photovoltaic/calculate', payload);
      if (data.photovoltaic_results?.status === 'ok') {
        setResults(data.photovoltaic_results);
        setSavedAt(new Date().toLocaleTimeString('ro-RO'));
        toast.success('Calcul fotovoltaic finalizat și salvat pe proiect');
      } else {
        toast.error(data.photovoltaic_results?.explanation || 'Date insuficiente');
      }
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Eroare la calcul');
    } finally {
      setLoading(false);
    }
  };

  const exportJson = () => {
    if (!results) return;
    const blob = new Blob([JSON.stringify({ input: form, results }, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `calcul-fv-${form.p_kwp}kWp.json`;
    a.click();
  };

  const downloadTechOfferPdf = async () => {
    if (!results) return;
    try {
      const res = await api.get('/photovoltaic/tech-offer-pdf', { responseType: 'blob' });
      const blob = new Blob([res.data], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `oferta-tehnica-FV-${form.p_kwp}kWp.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Oferta tehnică PDF generată');
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Eroare generare PDF');
    }
  };

  return (
    <AppShell title="Calcul fotovoltaic (FV)" subtitle="Dimensionare ANRE-compliantă: panouri, invertor, cabluri DC/AC, protecții și producție anuală.">
      <div className="grid lg:grid-cols-12 gap-6">
        {/* ───────────── INPUT FORM ───────────── */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white border border-gray-200 p-6" data-testid="fv-input-card">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 bg-[#FFB300] text-black flex items-center justify-center">
                <Sun className="w-5 h-5" strokeWidth={2.4} />
              </div>
              <div>
                <div className="font-semibold tracking-tight">Date sistem FV</div>
                <div className="text-[11px] text-gray-500 uppercase tracking-[0.18em]">ANRE Ord. 34/2024 · PVGIS</div>
              </div>
            </div>

            <div className="space-y-4">
              <Field label="Putere instalată (kWp)" hint="Suma puterilor panourilor la STC">
                <input
                  data-testid="fv-input-pkwp"
                  type="number" step="0.1" min="0.1"
                  value={form.p_kwp}
                  onChange={(e) => update('p_kwp', e.target.value)}
                  className="fv-input"
                />
              </Field>

              <Field label="Putere unitară panou (Wp)" hint="Modul mono TOPCon / HJT 2025 ≈ 450 Wp">
                <input
                  data-testid="fv-input-ppanou"
                  type="number" step="10" min="50"
                  value={form.p_panou_wp}
                  onChange={(e) => update('p_panou_wp', e.target.value)}
                  className="fv-input"
                />
              </Field>

              <Field label="Zonă geografică (iradiație PVGIS)">
                <select
                  data-testid="fv-input-zona"
                  value={form.zona_geografica}
                  onChange={(e) => update('zona_geografica', e.target.value)}
                  className="fv-input"
                >
                  {ZONE_OPTIONS.map((z) => (
                    <option key={z.value} value={z.value}>{z.label}</option>
                  ))}
                </select>
              </Field>

              <div className="grid grid-cols-2 gap-3">
                <Field label="Cablu DC (m)" hint="String → invertor">
                  <input
                    data-testid="fv-input-ldc"
                    type="number" step="1" min="1"
                    value={form.lungime_dc_m}
                    onChange={(e) => update('lungime_dc_m', e.target.value)}
                    className="fv-input"
                  />
                </Field>
                <Field label="Cablu AC (m)" hint="Invertor → tablou">
                  <input
                    data-testid="fv-input-lac"
                    type="number" step="1" min="1"
                    value={form.lungime_ac_m}
                    onChange={(e) => update('lungime_ac_m', e.target.value)}
                    className="fv-input"
                  />
                </Field>
              </div>

              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input
                  data-testid="fv-input-monofazat"
                  type="checkbox"
                  checked={form.monofazat}
                  onChange={(e) => update('monofazat', e.target.checked)}
                  className="w-4 h-4 accent-black"
                />
                <span>Conectare monofazată (230 V)</span>
                <span className="text-[10px] text-gray-400 uppercase tracking-[0.18em] ml-auto">≤ 5 kWp</span>
              </label>
            </div>

            <div className="mt-6 grid grid-cols-2 gap-2">
              <button
                data-testid="fv-calc-btn"
                onClick={runCalc}
                disabled={loading}
                className="amber-btn text-sm py-2.5 disabled:opacity-60"
              >
                {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                {loading ? 'Calculează…' : 'Rulează & salvează'}
              </button>
              <button
                data-testid="fv-export-btn"
                onClick={exportJson}
                disabled={!results}
                className="outline-btn text-sm py-2.5 disabled:opacity-40"
              >
                <FileJson className="w-3.5 h-3.5" /> Export JSON
              </button>
            </div>
            <button
              data-testid="fv-tech-offer-pdf-btn"
              onClick={downloadTechOfferPdf}
              disabled={!results}
              className="mt-2 w-full text-sm py-2.5 px-3 bg-black text-[#FFB300] font-semibold flex items-center justify-center gap-2 hover:bg-[#FFB300] hover:text-black border-2 border-black transition-colors disabled:opacity-40 disabled:cursor-not-allowed uppercase tracking-wider text-xs"
            >
              <FileDown className="w-3.5 h-3.5" /> Generează Ofertă Tehnică FV (PDF)
            </button>
            {savedAt && <div className="text-[10px] text-gray-500 uppercase tracking-[0.18em] mt-3">Ultima rulare {savedAt}</div>}
          </div>
        </div>

        {/* ───────────── RESULTS ───────────── */}
        <div className="lg:col-span-8 space-y-4" data-testid="fv-results">
          {!results ? (
            <EmptyState />
          ) : (
            <>
              <CategoryCard cat={results.categorie_anre} pkwp={results.p_kwp} />
              <MetricsGrid results={results} />
              <CablesProtections results={results} />
            </>
          )}
        </div>
      </div>

      <style>{`
        .fv-input {
          width: 100%;
          padding: 0.55rem 0.75rem;
          background: #fff;
          border: 1px solid #e5e7eb;
          font-size: 13px;
          font-family: inherit;
          outline: none;
          transition: border-color 0.15s;
        }
        .fv-input:focus { border-color: #FFB300; box-shadow: 0 0 0 3px rgba(255,179,0,0.15); }
      `}</style>
    </AppShell>
  );
}

function Field({ label, hint, children }) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-1.5">
        <label className="text-[11px] uppercase tracking-[0.18em] text-gray-600 font-medium">{label}</label>
        {hint && <span className="text-[10px] text-gray-400 italic">{hint}</span>}
      </div>
      {children}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="bg-white border border-gray-200 p-12 text-center" data-testid="fv-empty">
      <Sun className="w-12 h-12 text-gray-300 mx-auto mb-4" />
      <div className="font-semibold mb-1">Niciun calcul rulat încă</div>
      <p className="text-sm text-gray-600 max-w-sm mx-auto">
        Introdu puterea instalată (kWp) și ceilalți parametri în panoul din stânga,
        apoi apasă <strong>Rulează &amp; salvează</strong> pentru a obține dimensionarea ANRE-compliantă.
      </p>
    </div>
  );
}

function CategoryCard({ cat, pkwp }) {
  const tone = CATEGORY_TONE[cat.categorie] || 'bg-gray-50 text-gray-800 border-gray-200';
  return (
    <div className={`border p-6 ${tone}`} data-testid="fv-cat-card">
      <div className="flex items-center justify-between gap-4 mb-3">
        <div className="flex items-center gap-3">
          <Building2 className="w-5 h-5" strokeWidth={2.2} />
          <div>
            <div className="text-[10px] uppercase tracking-[0.22em] opacity-70">Categorie ANRE</div>
            <div className="text-2xl font-bold tracking-tight">{cat.categorie} · {pkwp} kWp</div>
          </div>
        </div>
        <div className="text-[10px] uppercase tracking-[0.22em] px-2 py-1 bg-white/60 border border-current/20">
          Regim {cat.regim}
        </div>
      </div>
      <div className="text-sm font-medium mb-1">{cat.label}</div>
      <div className="grid sm:grid-cols-2 gap-x-6 gap-y-1 text-xs mt-3">
        <div><span className="opacity-60 uppercase tracking-wider mr-2">Racord:</span>{cat.tip_racord}</div>
        <div><span className="opacity-60 uppercase tracking-wider mr-2">Aviz:</span>{cat.aviz}</div>
        <div><span className="opacity-60 uppercase tracking-wider mr-2">Compensare cantitativă:</span>{cat.compensare_cantitativă ? 'DA' : 'NU'}</div>
      </div>
    </div>
  );
}

function MetricsGrid({ results }) {
  const items = [
    { k: 'Număr panouri', v: results.panouri.n_panouri, u: `× ${results.panouri.putere_unitara_wp} Wp`, icon: Sun },
    { k: 'Stringuri', v: `${results.string.n_string} × ${results.string.n_serie_optim}`, u: 'panouri/string', icon: Cable },
    { k: 'Invertor recomandat', v: `${results.invertor.p_invertor_recomandat_kw}`, u: `kW (DC/AC ${results.invertor.raport_dc_ac})`, icon: Zap },
    { k: 'Tensiune string STC', v: results.string.u_string_stc_v, u: 'V', icon: Zap },
    { k: 'Producție anuală', v: Math.round(results.productie.productie_anuala_kwh).toLocaleString('ro-RO'), u: 'kWh/an', icon: TrendingUp },
    { k: 'Producție specifică', v: results.productie.productie_specifica_kwh_kwp, u: 'kWh/kWp', icon: TrendingUp },
  ];
  return (
    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-px bg-gray-200 border border-gray-200" data-testid="fv-metrics">
      {items.map((it) => {
        const Icon = it.icon;
        return (
          <div key={it.k} className="bg-white p-5 flex flex-col" data-testid={`fv-metric-${it.k}`}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] uppercase tracking-[0.22em] text-gray-500 font-medium">{it.k}</span>
              <Icon className="w-3.5 h-3.5 text-[#FFB300]" />
            </div>
            <div className="text-3xl font-bold tracking-tight leading-none">{it.v}</div>
            <div className="text-[11px] text-gray-500 mt-1">{it.u}</div>
          </div>
        );
      })}
    </div>
  );
}

function CablesProtections({ results }) {
  const dc = results.cablu_dc;
  const ac = results.cablu_ac;
  return (
    <div className="grid lg:grid-cols-2 gap-4">
      <div className="bg-white border border-gray-200 p-6" data-testid="fv-cables">
        <div className="flex items-center gap-2 mb-4">
          <Cable className="w-4 h-4 text-[#FFB300]" />
          <span className="font-semibold tracking-tight">Cabluri</span>
          <span className="text-[10px] uppercase tracking-[0.22em] text-gray-400 ml-auto">SR EN 50618 · I7-2011</span>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-[10px] uppercase tracking-[0.18em] text-gray-500">
              <th className="text-left pb-2 font-medium">Tronson</th>
              <th className="text-right pb-2 font-medium">Calc</th>
              <th className="text-right pb-2 font-medium">STD</th>
              <th className="text-right pb-2 font-medium">ΔU</th>
            </tr>
          </thead>
          <tbody className="border-t border-gray-200">
            <tr className="border-b border-gray-100">
              <td className="py-2"><div className="font-medium">DC string</div><div className="text-[10px] text-gray-500">{dc.tip_cablu}</div></td>
              <td className="text-right">{dc.sectiune_calculata_mm2} mm²</td>
              <td className="text-right font-bold">{dc.sectiune_standard_mm2} mm²</td>
              <td className="text-right text-gray-600">{dc.caderea_pct}%</td>
            </tr>
            <tr>
              <td className="py-2"><div className="font-medium">AC invertor → tablou</div><div className="text-[10px] text-gray-500">{ac.tip_cablu}</div></td>
              <td className="text-right">{ac.sectiune_calculata_mm2} mm²</td>
              <td className="text-right font-bold">{ac.sectiune_standard_mm2} mm²</td>
              <td className="text-right text-gray-600">{ac.curent_a} A</td>
            </tr>
          </tbody>
        </table>
        <div className="mt-3 text-[10px] text-gray-500 italic mono bg-gray-50 px-2 py-1.5">{ac.formula}</div>
      </div>

      <div className="bg-white border border-gray-200 p-6" data-testid="fv-protectii">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-4 h-4 text-[#FFB300]" />
          <span className="font-semibold tracking-tight">Protecții recomandate</span>
          <span className="text-[10px] uppercase tracking-[0.22em] text-gray-400 ml-auto">{results.protectii.length} elem.</span>
        </div>
        <ul className="space-y-2">
          {results.protectii.map((p, i) => (
            <li key={i} className="flex items-start gap-3 text-sm border-b border-gray-100 pb-2 last:border-0 last:pb-0">
              <div className="w-1.5 h-1.5 bg-[#FFB300] mt-2 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="font-medium">{p.nume}</div>
                <div className="text-[11px] text-gray-500">{p.tip} — {p.rol}</div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
