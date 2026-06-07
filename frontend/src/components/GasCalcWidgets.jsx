/* Phase-aware engineering calculator widget.
   Renders inline calc forms appropriate to the active phase id. */
import { useState } from 'react';
import { Calculator, Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';
import { runCalc, REGIME_OPTIONS, MATERIAL_OPTIONS, ZONE_OPTIONS } from '../lib/gas_calc';

function Row({ label, children }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[11px] uppercase tracking-wider text-gray-500">{label}</label>
      {children}
    </div>
  );
}

function In({ value, onChange, type = 'number', step = 'any', placeholder, ...rest }) {
  return (
    <input
      type={type} step={step} value={value} placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      className="border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-black focus:ring-2 focus:ring-black/15 bg-white"
      {...rest}
    />
  );
}

function Sel({ value, onChange, options, testid }) {
  return (
    <select
      value={value} onChange={(e) => onChange(e.target.value)}
      data-testid={testid}
      className="border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-black focus:ring-2 focus:ring-black/15 bg-white">
      {options.map((o) => (
        typeof o === 'string'
          ? <option key={o} value={o}>{o}</option>
          : <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

function ResultBox({ result, transformer }) {
  if (!result) return null;
  if (result.error) return (
    <div className="mt-3 p-3 bg-red-50 border-l-4 border-red-500 text-xs">
      <AlertTriangle className="w-3 h-3 inline mr-1" /> {result.error}
    </div>
  );
  const rows = transformer ? transformer(result) : Object.entries(result).map(([k, v]) => [k, JSON.stringify(v)]);
  const verdict = result.verdict || (result.recommended ? 'OK' : null);
  return (
    <div className="mt-3 p-3 bg-green-50 border-l-4 border-green-600 text-xs space-y-1" data-testid="calc-result">
      {verdict && (
        <div className="flex items-center gap-1 font-semibold mb-1">
          <CheckCircle2 className="w-3 h-3 text-green-700" /> Verdict: {verdict}
        </div>
      )}
      {rows.map(([k, v]) => (
        <div key={k} className="flex justify-between gap-3 border-b border-green-100 last:border-0 pb-1 last:pb-0">
          <span className="text-gray-600">{k}</span>
          <span className="mono text-right">{v}</span>
        </div>
      ))}
    </div>
  );
}

function CalcShell({ title, children, onRun, loading, result, transformer, dataKey }) {
  return (
    <div className="border border-gray-200 bg-white p-4" data-testid={`calc-${dataKey}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Calculator className="w-4 h-4 text-[#FFB300]" />
          <h4 className="text-sm font-semibold">{title}</h4>
        </div>
        <button onClick={onRun} disabled={loading}
          className="text-xs px-3 py-1.5 bg-black text-white hover:bg-gray-800 disabled:opacity-50 flex items-center gap-1"
          data-testid={`calc-run-${dataKey}`}>
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Calculează'}
        </button>
      </div>
      <div className="grid sm:grid-cols-2 gap-3">{children}</div>
      <ResultBox result={result} transformer={transformer} />
    </div>
  );
}

// ============= Dimensionare conducta =============
export function CalcDimensionare() {
  const [regime, setRegime] = useState('joasa');
  const [length, setLength] = useState(50);
  const [debit, setDebit] = useState(4.5);
  const [p1, setP1] = useState(2);
  const [material, setMaterial] = useState('PE 100 SDR 11');
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  async function run() {
    setLoading(true);
    try { const r = await runCalc('dimensionare_conducta', { regime, length_m: length, debit_mc_h: debit, p1_bar: p1, material }); setRes(r); }
    finally { setLoading(false); }
  }
  return (
    <CalcShell title="Dimensionare DN recomandat (Renouard)" onRun={run} loading={loading} result={res} dataKey="dim"
      transformer={(r) => r.recommended ? [
        ['DN recomandat', r.recommended.DN],
        ['Diametru exterior', r.recommended.od_mm + ' mm'],
        ['Diametru interior', r.recommended.id_mm + ' mm'],
        ['ΔP', (r.recommended.delta_p ?? 0) + (regime === 'joasa' ? ' mbar' : ' bar')],
        ['Viteză', r.recommended.viteza_m_s + ' m/s'],
        ['Material', r.material],
        ['Candidați evaluați', r.candidates.length],
      ] : []}>
      <Row label="Regim presiune"><Sel value={regime} onChange={setRegime} options={REGIME_OPTIONS} testid="calc-dim-regime" /></Row>
      <Row label="Material"><Sel value={material} onChange={setMaterial} options={MATERIAL_OPTIONS} testid="calc-dim-material" /></Row>
      <Row label="Lungime (m)"><In value={length} onChange={setLength} data-testid="calc-dim-length" /></Row>
      <Row label="Debit (m³/h)"><In value={debit} onChange={setDebit} data-testid="calc-dim-debit" /></Row>
      {regime === 'medie' && <Row label="Presiune intrare P1 (bar)"><In value={p1} onChange={setP1} data-testid="calc-dim-p1" /></Row>}
    </CalcShell>
  );
}

// ============= Pierderi presiune =============
export function CalcPierderi() {
  const [regime, setRegime] = useState('joasa');
  const [length, setLength] = useState(60);
  const [debit, setDebit] = useState(6);
  const [dn, setDn] = useState(26);
  const [p1, setP1] = useState(2);
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  async function run() {
    setLoading(true);
    try { const r = await runCalc('pierderi_presiune', { regime, length_m: length, debit_mc_h: debit, dn_id_mm: dn, p1_bar: p1 }); setRes(r); }
    finally { setLoading(false); }
  }
  return (
    <CalcShell title="Pierderi de presiune (Renouard)" onRun={run} loading={loading} result={res} dataKey="loss"
      transformer={(r) => [
        ['Formula', r.formula],
        ['ΔP', regime === 'joasa' ? r.delta_p_mbar + ' mbar' : r.delta_p_bar + ' bar'],
        ...(regime === 'medie' ? [['P1', r.p1_bar + ' bar'], ['P2', r.p2_bar + ' bar']] : []),
        ['Limita', regime === 'joasa' ? r.limit_mbar + ' mbar' : r.limit_bar + ' bar'],
      ]}>
      <Row label="Regim"><Sel value={regime} onChange={setRegime} options={REGIME_OPTIONS} testid="calc-loss-regime" /></Row>
      <Row label="Lungime (m)"><In value={length} onChange={setLength} data-testid="calc-loss-length" /></Row>
      <Row label="Debit (m³/h)"><In value={debit} onChange={setDebit} data-testid="calc-loss-debit" /></Row>
      <Row label="DN intern (mm)"><In value={dn} onChange={setDn} data-testid="calc-loss-dn" /></Row>
      {regime === 'medie' && <Row label="P1 (bar)"><In value={p1} onChange={setP1} data-testid="calc-loss-p1" /></Row>}
    </CalcShell>
  );
}

// ============= Debit cu Ks =============
export function CalcDebit() {
  const [n, setN] = useState(10);
  const [q, setQ] = useState(5.5);
  const [tip, setTip] = useState('casnic');
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  async function run() {
    setLoading(true);
    try { const r = await runCalc('debit_calculat', { nr_consumers: n, debit_individual_mc_h: q, consumer_type: tip }); setRes(r); }
    finally { setLoading(false); }
  }
  return (
    <CalcShell title="Debit calculat (n × q × Ks)" onRun={run} loading={loading} result={res} dataKey="debit"
      transformer={(r) => [
        ['Formula', r.formula],
        ['Nr. consumatori', r.nr_consumers],
        ['Debit individual', r.debit_individual_mc_h + ' m³/h'],
        ['Coef. simultaneitate Ks', r.ks],
        ['Debit calculat', r.debit_calculat_mc_h + ' m³/h'],
      ]}>
      <Row label="Nr. consumatori"><In value={n} onChange={setN} data-testid="calc-debit-n" /></Row>
      <Row label="Debit individual (m³/h)"><In value={q} onChange={setQ} data-testid="calc-debit-q" /></Row>
      <Row label="Tip consumator"><Sel value={tip} onChange={setTip} options={['casnic','necasnic']} testid="calc-debit-tip" /></Row>
    </CalcShell>
  );
}

// ============= Viteza gaz =============
export function CalcViteza() {
  const [debit, setDebit] = useState(50);
  const [dn, setDn] = useState(51.4);
  const [p, setP] = useState(0);
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  async function run() {
    setLoading(true);
    try { const r = await runCalc('viteza_gaz', { debit_mc_h: debit, dn_id_mm: dn, presiune_bar: p }); setRes(r); }
    finally { setLoading(false); }
  }
  return (
    <CalcShell title="Viteza gaz în conductă" onRun={run} loading={loading} result={res} dataKey="vit"
      transformer={(r) => [
        ['Debit', r.debit_mc_h + ' m³/h'],
        ['DN intern', r.diametru_mm + ' mm'],
        ['Presiune op.', r.presiune_bar + ' bar'],
        ['Viteză', r.viteza_m_s + ' m/s'],
        ['Limită', r.limit_m_s + ' m/s'],
      ]}>
      <Row label="Debit (m³/h)"><In value={debit} onChange={setDebit} data-testid="calc-vit-debit" /></Row>
      <Row label="DN intern (mm)"><In value={dn} onChange={setDn} data-testid="calc-vit-dn" /></Row>
      <Row label="Presiune (bar)"><In value={p} onChange={setP} data-testid="calc-vit-p" /></Row>
    </CalcShell>
  );
}

// ============= Adancime pozare =============
export function CalcPozare() {
  const [zona, setZona] = useState('trotuar');
  const [adancime, setAdancime] = useState(0.9);
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  async function run() {
    setLoading(true);
    try { const r = await runCalc('validare_adancime_pozare', { zona, adancime_m: adancime }); setRes(r); }
    finally { setLoading(false); }
  }
  return (
    <CalcShell title="Validare adâncime pozare (NTPEE art.56)" onRun={run} loading={loading} result={res} dataKey="poz"
      transformer={(r) => [
        ['Zona', r.zona],
        ['Adâncime introdusă', r.adancime_m + ' m'],
        ['Adâncime minimă', r.limit_min_m + ' m'],
        ['Bandă avertizare recomandată', (r.rec_banda_avertizare_m ?? '—') + ' m'],
      ]}>
      <Row label="Zona pozării"><Sel value={zona} onChange={setZona} options={ZONE_OPTIONS} testid="calc-poz-zona" /></Row>
      <Row label="Adâncime (m)"><In value={adancime} onChange={setAdancime} data-testid="calc-poz-adancime" /></Row>
    </CalcShell>
  );
}

// ============= Probe =============
export function CalcProbe() {
  const [pl, setPl] = useState(2);
  const [pr, setPr] = useState(6);
  const [pe, setPe] = useState(2.5);
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  async function run() {
    setLoading(true);
    try { const r = await runCalc('validare_probe', { p_lucru_bar: pl, p_rezistenta_bar: pr, p_etanseitate_bar: pe }); setRes(r); }
    finally { setLoading(false); }
  }
  return (
    <CalcShell title="Validare probe rezistență/etanșeitate" onRun={run} loading={loading} result={res} dataKey="probe"
      transformer={(r) => [
        ['P lucru', r.p_lucru_bar + ' bar'],
        ['Rezistență introdusă', r.p_rezistenta_bar + ' bar'],
        ['Rezistență minimă', r.rezistenta_min_bar + ' bar'],
        ['Rezistență OK?', r.rezistenta_ok ? 'DA' : 'NU'],
        ['Etanșeitate introdusă', r.p_etanseitate_bar + ' bar'],
        ['Etanșeitate minimă', r.etanseitate_min_bar + ' bar'],
        ['Etanșeitate OK?', r.etanseitate_ok ? 'DA' : 'NU'],
      ]}>
      <Row label="Presiune lucru (bar)"><In value={pl} onChange={setPl} data-testid="calc-probe-pl" /></Row>
      <Row label="P rezistență (bar)"><In value={pr} onChange={setPr} data-testid="calc-probe-pr" /></Row>
      <Row label="P etanșeitate (bar)"><In value={pe} onChange={setPe} data-testid="calc-probe-pe" /></Row>
    </CalcShell>
  );
}

// ============= Cost =============
export function CalcCost() {
  const [material, setMaterial] = useState('PE 100 SDR 11');
  const [dn, setDn] = useState(32);
  const [length, setLength] = useState(100);
  const [arm, setArm] = useState(2);
  const [post, setPost] = useState(false);
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  async function run() {
    setLoading(true);
    try { const r = await runCalc('cost_estimativ', { material, dn, length_m: length, nr_armaturi: arm, include_post_reglare: post }); setRes(r); }
    finally { setLoading(false); }
  }
  return (
    <CalcShell title="Cost estimativ (lei, fără TVA)" onRun={run} loading={loading} result={res} dataKey="cost"
      transformer={(r) => [
        ['Material', r.material],
        ['DN tarifare', r.dn_used_for_pricing],
        ['Preț unitar', r.unit_lei_per_m + ' lei/m'],
        ['Lungime', r.length_m + ' m'],
        ['Cost conductă', r.cost_conducta_lei + ' lei'],
        ['Armături', r.nr_armaturi + ' × 450 = ' + r.cost_armaturi_lei + ' lei'],
        ['Post reglare', r.cost_post_reglare_lei + ' lei'],
        ['TOTAL', r.cost_total_estimativ_lei + ' lei'],
      ]}>
      <Row label="Material"><Sel value={material} onChange={setMaterial} options={MATERIAL_OPTIONS} testid="calc-cost-material" /></Row>
      <Row label="DN (mm)"><In value={dn} onChange={setDn} data-testid="calc-cost-dn" /></Row>
      <Row label="Lungime (m)"><In value={length} onChange={setLength} data-testid="calc-cost-length" /></Row>
      <Row label="Nr. armături"><In value={arm} onChange={setArm} data-testid="calc-cost-arm" /></Row>
      <Row label="Include post reglare">
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={post} onChange={(e) => setPost(e.target.checked)} data-testid="calc-cost-post" /> Da
        </label>
      </Row>
    </CalcShell>
  );
}

// ============= Phase → Calcs Map =============
// Each phase suggests relevant calcs from the engineering toolkit.
export const PHASE_CALCS = {
  tema: ['debit'],
  sf: ['dim', 'cost'],
  cu: [],
  dtac: [],
  ac: [],
  pt: ['dim', 'loss', 'vit', 'debit'],
  de: ['poz'],
  executie: [],
  probe: ['probe'],
  receptie: [],
  pif: [],
};

const REGISTRY = {
  dim: CalcDimensionare,
  loss: CalcPierderi,
  debit: CalcDebit,
  vit: CalcViteza,
  poz: CalcPozare,
  probe: CalcProbe,
  cost: CalcCost,
};

export function PhaseCalcsPanel({ phaseId }) {
  const calcs = PHASE_CALCS[phaseId] || [];
  if (calcs.length === 0) {
    return (
      <div className="border border-dashed border-gray-300 p-4 text-xs text-gray-500 text-center">
        Această fază nu are calcule inginerești asociate. Continuă cu completarea câmpurilor.
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {calcs.map((k) => {
        const C = REGISTRY[k];
        return C ? <C key={k} /> : null;
      })}
    </div>
  );
}
