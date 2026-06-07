import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import AppShell from '../components/AppShell';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Briefcase, MapPin, Plus, Trash2, Globe } from 'lucide-react';
import api from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

const INDUSTRIES = [
  { id: 'gas_engineering', label: 'Inginerie Gaze' },
  { id: 'electrical_engineering', label: 'Inginerie Electrică' },
  { id: 'photovoltaic', label: 'Fotovoltaic' },
  { id: 'civil_engineering', label: 'Construcții civile' },
  { id: 'hvac', label: 'HVAC' },
  { id: 'water_sewage', label: 'Apă & Canalizare' },
  { id: 'telecom', label: 'Telecom' },
  { id: 'general', label: 'General' },
];

const TYPES = [
  { id: 'full_time', label: 'Full-time' },
  { id: 'part_time', label: 'Part-time' },
  { id: 'contract', label: 'Contract' },
  { id: 'project', label: 'Per Proiect' },
];

export default function Jobs() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.is_admin || user?.is_developer;
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ industry: 'all', type: 'all', location: '' });
  const [form, setForm] = useState({ title: '', industry: 'general', location: '', type: 'full_time', description: '', is_public: true });

  const refresh = async () => {
    setLoading(true);
    try {
      const path = isAdmin ? '/dev/jobs' : '/jobs';
      const { data } = await api.get(path);
      setItems(data || []);
    } catch {
      toast.error('Eroare la încărcarea ofertelor');
    } finally { setLoading(false); }
  };

  useEffect(() => {
    (async () => {
      try {
        const path = isAdmin ? '/dev/jobs' : '/jobs';
        const { data } = await api.get(path);
        setItems(data || []);
      } catch (_) { /* silent */ }
      finally { setLoading(false); }
    })();
  }, [isAdmin]);

  const create = async () => {
    if (!form.title.trim()) { toast.error('Titlul este obligatoriu'); return; }
    try {
      await api.post('/dev/jobs', form);
      toast.success('Anunț publicat');
      setForm({ title: '', industry: 'general', location: '', type: 'full_time', description: '', is_public: true });
      refresh();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Eroare la publicare');
    }
  };

  const remove = async (id) => {
    if (!window.confirm('Ștergeți acest anunț?')) return;
    try { await api.delete(`/dev/jobs/${id}`); toast.success('Șters'); refresh(); }
    catch { toast.error('Eroare la ștergere'); }
  };

  return (
    <AppShell>
      <div className="space-y-6" data-testid="jobs-page">
        <header className="flex items-end justify-between border-b border-zinc-800 pb-4">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-amber-400/80">// MARKETPLACE</p>
            <h1 className="text-4xl font-bold mt-2">Job Board ANRE</h1>
            <p className="text-sm text-zinc-400 mt-2">Anunțuri publice pentru proiectanți autorizați, executanți și verificatori VGD/RTE.</p>
          </div>
          <Badge variant="outline" className="border-amber-500/40 text-amber-300">
            <Globe className="w-3.5 h-3.5 mr-1" /> {isAdmin ? 'Vizualizare ADMIN' : 'Listing public'}
          </Badge>
        </header>

        {isAdmin && (
          <Card className="p-6 bg-zinc-950/70 border-zinc-800" data-testid="jobs-create-card">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2"><Plus className="w-4 h-4 text-amber-400" /> Anunț nou</h2>
            <div className="grid md:grid-cols-2 gap-3">
              <Input data-testid="job-title" placeholder="Titlu (ex: Proiectant gaze naturale RO)" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} />
              <Input data-testid="job-location" placeholder="Locație (ex: București, Cluj)" value={form.location} onChange={e => setForm({ ...form, location: e.target.value })} />
              <Select value={form.industry} onValueChange={v => setForm({ ...form, industry: v })}>
                <SelectTrigger data-testid="job-industry"><SelectValue /></SelectTrigger>
                <SelectContent>{INDUSTRIES.map(i => <SelectItem key={i.id} value={i.id}>{i.label}</SelectItem>)}</SelectContent>
              </Select>
              <Select value={form.type} onValueChange={v => setForm({ ...form, type: v })}>
                <SelectTrigger data-testid="job-type"><SelectValue /></SelectTrigger>
                <SelectContent>{TYPES.map(i => <SelectItem key={i.id} value={i.id}>{i.label}</SelectItem>)}</SelectContent>
              </Select>
              <Textarea className="md:col-span-2" rows={3} data-testid="job-description" placeholder="Descriere completă" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
              <label className="md:col-span-2 inline-flex items-center gap-2 text-sm">
                <input type="checkbox" checked={form.is_public} onChange={e => setForm({ ...form, is_public: e.target.checked })} /> Public (vizibil în feed-ul /jobs)
              </label>
            </div>
            <Button onClick={create} data-testid="job-publish-btn" className="mt-4 bg-amber-500 hover:bg-amber-400 text-black font-semibold">Publică anunțul</Button>
          </Card>
        )}

        {loading ? (
          <div className="text-center text-zinc-500 py-12">Se încarcă…</div>
        ) : (
          <>
            <Card className="p-4 bg-zinc-950/50 border-zinc-800" data-testid="jobs-filters">
              <div className="grid md:grid-cols-4 gap-3 items-end">
                <div>
                  <p className="text-xs text-zinc-500 mb-1">Industrie</p>
                  <Select value={filters.industry} onValueChange={v => setFilters({ ...filters, industry: v })}>
                    <SelectTrigger data-testid="filter-industry"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Toate industriile</SelectItem>
                      {INDUSTRIES.map(i => <SelectItem key={i.id} value={i.id}>{i.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 mb-1">Tip contract</p>
                  <Select value={filters.type} onValueChange={v => setFilters({ ...filters, type: v })}>
                    <SelectTrigger data-testid="filter-type"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Toate tipurile</SelectItem>
                      {TYPES.map(t => <SelectItem key={t.id} value={t.id}>{t.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div className="md:col-span-2">
                  <p className="text-xs text-zinc-500 mb-1">Locație</p>
                  <Input data-testid="filter-location" placeholder="ex: București, Cluj…" value={filters.location} onChange={e => setFilters({ ...filters, location: e.target.value })} />
                </div>
              </div>
              <p className="text-xs text-zinc-500 mt-3" data-testid="jobs-count">
                {(() => {
                  const f = items.filter(j =>
                    (filters.industry === 'all' || j.industry === filters.industry) &&
                    (filters.type === 'all' || j.type === filters.type) &&
                    (!filters.location.trim() || (j.location || '').toLowerCase().includes(filters.location.trim().toLowerCase()))
                  );
                  return `${f.length} din ${items.length} anunțuri afișate`;
                })()}
              </p>
            </Card>
            {(() => {
              const filtered = items.filter(j =>
                (filters.industry === 'all' || j.industry === filters.industry) &&
                (filters.type === 'all' || j.type === filters.type) &&
                (!filters.location.trim() || (j.location || '').toLowerCase().includes(filters.location.trim().toLowerCase()))
              );
              return filtered.length === 0 ? (
                <div className="text-center text-zinc-500 py-12 border border-dashed border-zinc-800 rounded-lg">
                  <Briefcase className="w-12 h-12 mx-auto mb-3 opacity-40" />
                  Niciun anunț corespunzător filtrelor.
                </div>
              ) : (
                <div className="grid md:grid-cols-2 gap-4" data-testid="jobs-list">
                  {filtered.map(job => (
                    <Card key={job.id} className="p-5 bg-zinc-950/70 border-zinc-800 hover:border-amber-500/40 transition" data-testid={`job-${job.id}`}>
                      <div className="flex justify-between items-start gap-3 mb-3">
                        <div>
                          <h3 className="font-semibold text-lg">{job.title}</h3>
                          <div className="flex flex-wrap gap-2 mt-2 text-xs text-zinc-400">
                            <Badge variant="outline" className="border-zinc-700">{INDUSTRIES.find(i => i.id === job.industry)?.label || job.industry}</Badge>
                            <Badge variant="outline" className="border-zinc-700">{TYPES.find(t => t.id === job.type)?.label || job.type}</Badge>
                            {job.location && <span className="inline-flex items-center gap-1"><MapPin className="w-3 h-3" /> {job.location}</span>}
                          </div>
                        </div>
                        {isAdmin && (
                          <Button size="sm" variant="ghost" onClick={() => remove(job.id)} className="text-red-400 hover:text-red-300" data-testid={`job-delete-${job.id}`}>
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                      {job.description && <p className="text-sm text-zinc-300 whitespace-pre-line">{job.description}</p>}
                    </Card>
                  ))}
                </div>
              );
            })()}
          </>
        )}
      </div>
    </AppShell>
  );
}
