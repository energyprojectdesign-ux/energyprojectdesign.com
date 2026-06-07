import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import AppShell from '../components/AppShell';
import api from '../lib/api';
import { toast } from 'sonner';
import { ArrowLeft, Save, Mail, Building2, Loader2 } from 'lucide-react';

const ROLES = [
  { id: 'beneficiar', label: 'Beneficiar', desc: 'Titularul lucrării — destinatarul natural al fiecărei faze.' },
  { id: 'primarie', label: 'Primărie / Consiliu Local', desc: 'Emitent CU + AC; recepție la finalizare.' },
  { id: 'osd', label: 'OSD (Distribuție gaze)', desc: 'Distrigaz Sud / Delgaz Grid / Premier Energy / etc.' },
  { id: 'isc', label: 'ISC — Inspectoratul de Stat în Construcții', desc: 'Aviz tehnic, verificări execuție.' },
  { id: 'anre', label: 'ANRE', desc: 'Autoritatea de reglementare în energie — pentru PIF.' },
  { id: 'mediu', label: 'APM — Mediu', desc: 'Aviz mediu pentru lucrări mari.' },
  { id: 'iscir', label: 'ISCIR', desc: 'Centrale termice & echipamente sub presiune.' },
  { id: 'verificator', label: 'Verificator de proiect (VGD)', desc: 'Verificare independentă DTAC/PT.' },
  { id: 'rte', label: 'Responsabil tehnic execuție', desc: 'Atestat MDLPA pentru execuție.' },
  { id: 'executant', label: 'Firmă executantă', desc: 'Autorizație ANRE EDD.' },
  { id: 'proiectant', label: 'Proiectant', desc: 'Atestat ANRE PDD.' },
];

export default function GasRecipients() {
  const [items, setItems] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => { (async () => {
    try { const { data } = await api.get('/gas-project/recipients'); setItems(data?.items || {}); }
    catch (_) { toast.error('Eroare încărcare destinatari'); }
    finally { setLoading(false); }
  })(); }, []);

  function update(role, value) {
    const list = value.split(/[,\s;\n]+/).map((e) => e.trim()).filter((e) => e.includes('@'));
    setItems((prev) => ({ ...prev, [role]: list }));
  }

  async function save() {
    setSaving(true);
    try {
      await api.put('/gas-project/recipients', { items });
      toast.success('Destinatari salvați');
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Eroare salvare');
    } finally { setSaving(false); }
  }

  return (
    <AppShell title="Destinatari autorități" subtitle="Configurează emailurile pe care le folosești la trimiterea fazelor de proiect">
      <Link to="/gaze-naturale" className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-black mb-4" data-testid="recipients-back">
        <ArrowLeft className="w-3 h-3" /> Înapoi la Gaze Naturale
      </Link>

      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 text-xs">
        <div className="flex items-start gap-3">
          <Mail className="w-4 h-4 mt-0.5 text-blue-700 shrink-0" />
          <div>
            <div className="font-semibold mb-1">Cum funcționează?</div>
            <p>Salvezi aici adresele oficiale pentru fiecare rol (primărie, OSD, ISC, etc.). Când completezi o fază în Studio și apeși «Trimite faza către autorități», sistemul auto-completează destinatarii folosind aceste adrese, în funcție de cerințele fazei.</p>
            <p className="mt-1">Trimiterea se face prin contul Gmail configurat în <Link to="/settings" className="underline">Setări</Link>. Adresa secundară business va fi CC automat.</p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-sm text-gray-500">Se încarcă…</div>
      ) : (
        <div className="space-y-4" data-testid="recipients-list">
          {ROLES.map((role) => (
            <div key={role.id} className="border border-gray-200 bg-white p-4" data-testid={`recipients-role-${role.id}`}>
              <div className="flex items-start gap-3 mb-2">
                <div className="w-9 h-9 bg-gray-100 flex items-center justify-center shrink-0"><Building2 className="w-4 h-4 text-gray-600" /></div>
                <div className="flex-1">
                  <div className="font-semibold text-sm">{role.label}</div>
                  <div className="text-[11px] text-gray-500">{role.desc}</div>
                </div>
                <span className="text-[10px] mono text-gray-400 self-start">{(items[role.id] || []).length} email{(items[role.id] || []).length !== 1 ? 'uri' : ''}</span>
              </div>
              <textarea
                value={(items[role.id] || []).join(', ')}
                onChange={(e) => update(role.id, e.target.value)}
                rows={2}
                placeholder="email1@autoritate.ro, email2@autoritate.ro"
                className="w-full border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:border-black focus:ring-2 focus:ring-black/15"
                data-testid={`recipients-input-${role.id}`}
              />
            </div>
          ))}
          <div className="sticky bottom-4 flex justify-end">
            <button onClick={save} disabled={saving} className="amber-btn" data-testid="recipients-save">
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />} Salvează toate
            </button>
          </div>
        </div>
      )}
    </AppShell>
  );
}
