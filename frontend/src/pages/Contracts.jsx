import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import AppShell from '../components/AppShell';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { FileText, Plus, Trash2, Calendar, Euro } from 'lucide-react';
import api from '../lib/api';

const STATUSES = [
  { id: 'draft',    label: 'Ciornă',     class: 'border-zinc-600 text-zinc-300' },
  { id: 'pending',  label: 'În așteptare', class: 'border-amber-500/40 text-amber-300' },
  { id: 'active',   label: 'Activ',      class: 'border-emerald-500/40 text-emerald-300' },
  { id: 'closed',   label: 'Închis',     class: 'border-zinc-600 text-zinc-500' },
];

export default function Contracts() {
  const [items, setItems] = useState([]);
  const [subs, setSubs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: 'all', minValue: '', maxValue: '' });
  const [form, setForm] = useState({ subscriber_id: '', title: '', value_eur: 0, status: 'draft', start_date: '', end_date: '', notes: '' });

  const refresh = async () => {
    try {
      const [c, s] = await Promise.all([
        api.get('/dev/contracts'),
        api.get('/crm/subscribers').catch(() => ({ data: [] })),
      ]);
      setItems(c.data || []);
      setSubs(s.data || []);
    } catch {
      toast.error('Eroare la încărcarea contractelor');
    } finally { setLoading(false); }
  };

  useEffect(() => {
    (async () => {
      try {
        const [c, s] = await Promise.all([
          api.get('/dev/contracts'),
          api.get('/crm/subscribers').catch(() => ({ data: [] })),
        ]);
        setItems(c.data || []);
        setSubs(s.data || []);
      } catch (_) { /* silent */ }
      finally { setLoading(false); }
    })();
  }, []);

  const create = async () => {
    if (!form.title.trim()) { toast.error('Titlul este obligatoriu'); return; }
    try {
      await api.post('/dev/contracts', { ...form, value_eur: Number(form.value_eur || 0) });
      toast.success('Contract creat');
      setForm({ subscriber_id: '', title: '', value_eur: 0, status: 'draft', start_date: '', end_date: '', notes: '' });
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Eroare la creare');
    }
  };

  const remove = async (id) => {
    if (!window.confirm('Ștergeți acest contract?')) return;
    try { await api.delete(`/dev/contracts/${id}`); toast.success('Șters'); refresh(); }
    catch { toast.error('Eroare'); }
  };

  const totalActive = items.filter(c => c.status === 'active').reduce((s, c) => s + (c.value_eur || 0), 0);

  return (
    <AppShell>
      <div className="space-y-6" data-testid="contracts-page">
        <header className="flex items-end justify-between border-b border-zinc-800 pb-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-amber-400/80">// CRM</p>
            <h1 className="text-4xl font-bold mt-2">Contracte</h1>
            <p className="text-sm text-zinc-400 mt-2">Gestionați contractele active, valorile recurente și legaturile cu abonații CRM.</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-zinc-500 uppercase">Total Active</p>
            <p className="text-3xl font-bold text-emerald-400">{totalActive.toLocaleString('ro-RO')} €</p>
          </div>
        </header>

        <Card className="p-6 bg-zinc-950/70 border-zinc-800">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><Plus className="w-4 h-4 text-amber-400" /> Contract nou</h2>
          <div className="grid md:grid-cols-3 gap-3">
            <Input data-testid="ctr-title" placeholder="Titlu contract" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
            <Input data-testid="ctr-value" type="number" placeholder="Valoare EUR" value={form.value_eur} onChange={e => setForm({ ...form, value_eur: e.target.value })} />
            <Select value={form.status} onValueChange={v => setForm({ ...form, status: v })}>
              <SelectTrigger data-testid="ctr-status"><SelectValue /></SelectTrigger>
              <SelectContent>{STATUSES.map(s => <SelectItem key={s.id} value={s.id}>{s.label}</SelectItem>)}</SelectContent>
            </Select>
            <Input data-testid="ctr-start" type="date" placeholder="Început" value={form.start_date || ''} onChange={e => setForm({ ...form, start_date: e.target.value })} />
            <Input data-testid="ctr-end" type="date" placeholder="Sfârșit" value={form.end_date || ''} onChange={e => setForm({ ...form, end_date: e.target.value })} />
            <Select value={form.subscriber_id || 'none'} onValueChange={v => setForm({ ...form, subscriber_id: v === 'none' ? '' : v })}>
              <SelectTrigger data-testid="ctr-subscriber"><SelectValue placeholder="Abonat asociat (opțional)" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="none">— niciun abonat —</SelectItem>
                {subs.map(s => <SelectItem key={s.id || s.sub_id} value={s.id || s.sub_id}>{s.name || s.email}</SelectItem>)}
              </SelectContent>
            </Select>
            <Textarea className="md:col-span-3" rows={2} data-testid="ctr-notes" placeholder="Note (opțional)" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} />
          </div>
          <Button onClick={create} data-testid="ctr-create-btn" className="mt-4 bg-amber-500 hover:bg-amber-400 text-black font-semibold">Creează contract</Button>
        </Card>

        {loading ? (
          <div className="text-center text-zinc-500 py-12">Se încarcă…</div>
        ) : items.length === 0 ? (
          <div className="text-center text-zinc-500 py-12 border border-dashed border-zinc-800 rounded-lg">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-40" />
            Niciun contract înregistrat.
          </div>
        ) : (
          <div className="space-y-3" data-testid="contracts-list">
            {items.map(c => {
              const st = STATUSES.find(s => s.id === c.status) || STATUSES[0];
              return (
                <Card key={c.id} className="p-5 bg-zinc-950/70 border-zinc-800 flex items-center justify-between" data-testid={`ctr-${c.id}`}>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold">{c.title}</h3>
                      <Badge variant="outline" className={st.class}>{st.label}</Badge>
                    </div>
                    <div className="flex flex-wrap gap-4 text-xs text-zinc-400">
                      <span className="inline-flex items-center gap-1"><Euro className="w-3 h-3" /> {(c.value_eur || 0).toLocaleString('ro-RO')} €</span>
                      {c.start_date && <span className="inline-flex items-center gap-1"><Calendar className="w-3 h-3" /> {c.start_date} → {c.end_date || '∞'}</span>}
                    </div>
                    {c.notes && <p className="text-xs text-zinc-500 mt-2 italic">{c.notes}</p>}
                  </div>
                  <Button size="sm" variant="ghost" onClick={() => remove(c.id)} className="text-red-400 hover:text-red-300" data-testid={`ctr-delete-${c.id}`}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </AppShell>
  );
}
