import { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import AppShell from '../components/AppShell';
import api from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';
import { MessageSquare, Plus, Heart, Eye, Reply, ArrowLeft, Trash2, Pin, Filter, TrendingUp, Clock, Send, X } from 'lucide-react';

marked.setOptions({ breaks: true, gfm: true });

function renderMarkdown(text) {
  if (!text) return { __html: '' };
  const html = DOMPurify.sanitize(marked.parse(text), {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'blockquote', 'code', 'pre', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td'],
    ALLOWED_ATTR: ['href', 'title', 'class'],
  });
  return { __html: html };
}

const INDUSTRIES = [
  { id: 'all', label: 'Toate', icon: '◉' },
  { id: 'general', label: 'General (inter-industrii)', icon: '🌐' },
  { id: 'gas_engineering', label: 'Gaze naturale', icon: '🔥' },
  { id: 'electrical_engineering', label: 'Electrică', icon: '⚡' },
  { id: 'water_sewage', label: 'Apă & canalizare', icon: '💧' },
  { id: 'civil_engineering', label: 'Construcții civile', icon: '🏗️' },
  { id: 'telecom', label: 'Telecomunicații', icon: '📡' },
  { id: 'photovoltaic', label: 'Fotovoltaice', icon: '☀️' },
  { id: 'construction', label: 'Construcții imobile', icon: '🏢' },
  { id: 'railway_infra', label: 'Infrastructură feroviară', icon: '🚆' },
  { id: 'sanitation', label: 'Salubritate & deșeuri', icon: '♻️' },
  { id: 'hvac', label: 'HVAC & termice', icon: '🌡️' },
  { id: 'environment', label: 'Mediu & avize', icon: '🌱' },
  { id: 'roads_bridges', label: 'Drumuri & poduri', icon: '🛣️' },
  { id: 'public_lighting', label: 'Iluminat public', icon: '💡' },
];

function timeAgo(iso) {
  if (!iso) return '';
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return 'acum câteva secunde';
  if (diff < 3600) return `acum ${Math.floor(diff / 60)} min`;
  if (diff < 86400) return `acum ${Math.floor(diff / 3600)} ore`;
  if (diff < 2592000) return `acum ${Math.floor(diff / 86400)} zile`;
  return new Date(iso).toLocaleDateString('ro-RO');
}

function industryLabel(id) {
  return INDUSTRIES.find(i => i.id === id)?.label || id;
}

function industryIcon(id) {
  return INDUSTRIES.find(i => i.id === id)?.icon || '◉';
}

export default function Forum() {
  const { user } = useAuth();
  const { threadId } = useParams();
  const nav = useNavigate();

  if (threadId) {
    return <ForumThreadView threadId={threadId} />;
  }
  return <ForumList />;
}

function ForumList() {
  const { user } = useAuth();
  const [industry, setIndustry] = useState('all');
  const [sort, setSort] = useState('recent');
  const [threads, setThreads] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [showCompose, setShowCompose] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [thr, s] = await Promise.all([
          api.get('/forum/threads', { params: { industry, sort, limit: 100 } }),
          api.get('/forum/industry-stats'),
        ]);
        setThreads(thr.data);
        setStats(s.data);
      } catch (e) {
        toast.error('Eroare încărcare forum.');
      } finally {
        setLoading(false);
      }
    })();
  }, [industry, sort, reloadKey]);

  const reload = () => setReloadKey(k => k + 1);

  // Aggregate stats for hero
  const totalThreads = threads.length;
  const totalReplies = threads.reduce((acc, t) => acc + (t.reply_count || 0), 0);
  const totalLikes = threads.reduce((acc, t) => acc + (t.likes || 0), 0);

  return (
    <AppShell>
      <div className="p-8 max-w-7xl" data-testid="forum-page">
        {/* Premium hero */}
        <div className="relative overflow-hidden mb-8 bg-gradient-to-br from-[#0A0A0A] via-[#171717] to-[#0A0A0A] text-white">
          <div className="absolute -right-24 -top-24 w-96 h-96 bg-[#FFB300]/15 blur-[120px] rounded-full pointer-events-none" />
          <div className="absolute inset-0 opacity-[0.04] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#FFB300 1px, transparent 1px)', backgroundSize: '16px 16px' }} />
          <div className="relative p-8 lg:p-10 flex items-start justify-between gap-6 flex-wrap">
            <div className="flex-1 min-w-[280px]">
              <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-[#FFB300] mb-3">
                <MessageSquare className="w-3.5 h-3.5" /> // forum comunitate
              </div>
              <h1 className="text-4xl lg:text-5xl font-bold leading-tight tracking-tight mb-3">
                Inginerie, <span className="text-[#FFB300]">la persoana întâi.</span>
              </h1>
              <p className="text-sm lg:text-base text-gray-300 leading-relaxed max-w-2xl">
                Discuții deschise între <strong className="text-white">proiectanți</strong>, <strong className="text-white">executanți</strong>, <strong className="text-white">verificatori VGD/RTE</strong> și autorizate ANRE. Filtrează pe industria ta sau navighează tematic.
              </p>
            </div>
            <div className="flex flex-col gap-3 items-end">
              <button
                onClick={() => {
                  if (!user) { toast.error('Loghează-te ca să postezi.'); return; }
                  setShowCompose(true);
                }}
                className="bg-[#FFB300] text-black px-5 py-3 flex items-center gap-2 hover:bg-white border-2 border-[#FFB300] font-bold text-sm uppercase tracking-wider transition-colors"
                data-testid="new-thread-btn"
              >
                <Plus className="w-4 h-4" /> Discuție nouă
              </button>
              <div className="flex gap-2">
                <span className="bg-white/5 backdrop-blur-md border border-white/10 px-3 py-1.5 text-xs"><strong className="text-[#FFB300]">{totalThreads}</strong> <span className="text-gray-400 uppercase tracking-wider text-[10px]">discuții</span></span>
                <span className="bg-white/5 backdrop-blur-md border border-white/10 px-3 py-1.5 text-xs"><strong className="text-emerald-400">{totalReplies}</strong> <span className="text-gray-400 uppercase tracking-wider text-[10px]">răspunsuri</span></span>
                <span className="bg-white/5 backdrop-blur-md border border-white/10 px-3 py-1.5 text-xs"><strong className="text-rose-400">{totalLikes}</strong> <span className="text-gray-400 uppercase tracking-wider text-[10px]">like-uri</span></span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar — industries */}
          <aside className="lg:col-span-1 space-y-1" data-testid="industry-sidebar">
            <div className="text-xs uppercase tracking-wider text-gray-500 px-3 py-2 flex items-center gap-2"><Filter className="w-3.5 h-3.5" /> Industrie</div>
            {INDUSTRIES.map((i) => (
              <button
                key={i.id}
                onClick={() => setIndustry(i.id)}
                className={`w-full text-left px-3 py-2 text-sm flex items-center justify-between hover:bg-gray-100 transition-colors ${industry === i.id ? 'bg-black text-[#FFB300]' : ''}`}
                data-testid={`industry-${i.id}`}
              >
                <span className="flex items-center gap-2">
                  <span className="text-base">{i.icon}</span>
                  <span className="truncate">{i.label}</span>
                </span>
                {stats[i.id] != null && i.id !== 'all' && <span className="text-xs opacity-70">{stats[i.id]}</span>}
              </button>
            ))}

            <div className="border-t border-gray-200 mt-4 pt-4">
              <div className="text-xs uppercase tracking-wider text-gray-500 px-3 py-2">Sortare</div>
              <button onClick={() => setSort('recent')} className={`w-full text-left px-3 py-2 text-sm flex items-center gap-2 hover:bg-gray-100 ${sort === 'recent' ? 'bg-gray-200 font-semibold' : ''}`} data-testid="sort-recent">
                <Clock className="w-3.5 h-3.5" /> Activitate recentă
              </button>
              <button onClick={() => setSort('top')} className={`w-full text-left px-3 py-2 text-sm flex items-center gap-2 hover:bg-gray-100 ${sort === 'top' ? 'bg-gray-200 font-semibold' : ''}`} data-testid="sort-top">
                <TrendingUp className="w-3.5 h-3.5" /> Top apreciate
              </button>
            </div>
          </aside>

          {/* Main thread list */}
          <main className="lg:col-span-3" data-testid="thread-list">
            {loading ? (
              <div className="bg-white border border-gray-200 p-8 text-center text-sm text-gray-500">Se încarcă discuțiile…</div>
            ) : threads.length === 0 ? (
              <div className="bg-white border border-gray-200 p-12 text-center" data-testid="empty-forum">
                <MessageSquare className="w-12 h-12 mx-auto text-gray-300 mb-3" />
                <div className="font-semibold text-lg">Niciun fir de discuție încă</div>
                <div className="text-sm text-gray-500 mt-1">Fii primul care începe o discuție pe &bdquo;{industryLabel(industry)}&rdquo;.</div>
                {user && (
                  <button onClick={() => setShowCompose(true)} className="mt-4 bg-black text-[#FFB300] px-5 py-2 text-sm border-2 border-black inline-flex items-center gap-2 hover:bg-[#FFB300] hover:text-black">
                    <Plus className="w-4 h-4" /> Pornește o discuție
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {threads.map((t) => (
                  <Link
                    key={t.thread_id}
                    to={`/forum/${t.thread_id}`}
                    className="group block bg-white border border-gray-200 hover:border-black hover:shadow-[0_8px_24px_rgba(0,0,0,0.06)] transition-all duration-200 p-5"
                    data-testid={`thread-${t.thread_id}`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 text-xs text-gray-500 mb-1.5">
                          {t.pinned && <Pin className="w-3.5 h-3.5 text-[#FFB300]" />}
                          <span className="bg-gray-100 px-2 py-0.5 text-[10px] uppercase tracking-wider font-semibold">{industryIcon(t.industry)} {industryLabel(t.industry)}</span>
                          {t.is_developer_post && <span className="bg-[#FFB300] text-black px-2 py-0.5 text-[10px] uppercase tracking-wider font-bold">Admin</span>}
                          <span>•</span>
                          <span>{t.author_name}</span>
                          <span>•</span>
                          <span>{timeAgo(t.last_activity_at)}</span>
                        </div>
                        <div className="font-bold text-lg truncate">{t.title}</div>
                        {t.tags?.length > 0 && (
                          <div className="flex gap-1.5 mt-2 flex-wrap">
                            {t.tags.map((tag) => (
                              <span key={tag} className="text-[10px] bg-gray-100 px-2 py-0.5 mono">#{tag}</span>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="shrink-0 flex flex-col items-end gap-1 text-xs text-gray-500">
                        <span className="flex items-center gap-1"><Reply className="w-3.5 h-3.5" /> {t.reply_count}</span>
                        <span className="flex items-center gap-1"><Heart className="w-3.5 h-3.5" /> {t.likes}</span>
                        <span className="flex items-center gap-1"><Eye className="w-3.5 h-3.5" /> {t.views}</span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </main>
        </div>

        {showCompose && (
          <ComposeModal
            onClose={() => setShowCompose(false)}
            onCreated={() => { setShowCompose(false); reload(); }}
            defaultIndustry={industry === 'all' ? 'general' : industry}
          />
        )}
      </div>
    </AppShell>
  );
}

function ComposeModal({ onClose, onCreated, defaultIndustry }) {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [industry, setIndustry] = useState(defaultIndustry || 'general');
  const [tagsStr, setTagsStr] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (title.trim().length < 4 || body.trim().length < 10) {
      toast.error('Titlul (min. 4) și conținutul (min. 10) sunt obligatorii.');
      return;
    }
    setBusy(true);
    try {
      const tags = tagsStr.split(',').map(t => t.trim()).filter(Boolean);
      await api.post('/forum/threads', { title, body, industry, tags });
      toast.success('Discuție publicată!');
      onCreated();
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Eroare publicare.');
    } finally { setBusy(false); }
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" data-testid="compose-modal">
      <div className="bg-white border-2 border-black w-full max-w-2xl max-h-[90vh] overflow-auto">
        <div className="flex items-center justify-between p-4 border-b-2 border-black">
          <h2 className="font-bold text-lg">Discuție nouă</h2>
          <button onClick={onClose} className="hover:bg-gray-100 p-1" data-testid="compose-close-btn"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="text-xs uppercase text-gray-600">Industrie</label>
            <select value={industry} onChange={(e) => setIndustry(e.target.value)} className="w-full mt-1 px-3 py-2 border border-black text-sm" data-testid="compose-industry">
              {INDUSTRIES.filter(i => i.id !== 'all').map(i => <option key={i.id} value={i.id}>{i.icon} {i.label}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs uppercase text-gray-600">Titlu (min. 4 caractere)</label>
            <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} className="w-full mt-1 px-3 py-2 border border-black text-sm font-semibold" maxLength={200} data-testid="compose-title" />
          </div>
          <div>
            <label className="text-xs uppercase text-gray-600 flex items-center justify-between">
              <span>Conținut</span>
              <span className="text-[10px] text-gray-400">Markdown acceptat: **bold**, *italic*, `cod`, &gt;citat, liste</span>
            </label>
            <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={8} className="w-full mt-1 px-3 py-2 border border-black text-sm font-mono" maxLength={8000} data-testid="compose-body" />
            <div className="text-[10px] text-gray-500 mt-1">{body.length}/8000 caractere</div>
          </div>
          <div>
            <label className="text-xs uppercase text-gray-600">Tag-uri (opțional, separate prin virgulă)</label>
            <input type="text" value={tagsStr} onChange={(e) => setTagsStr(e.target.value)} placeholder="distrigaz, branșament, OSD" className="w-full mt-1 px-3 py-2 border border-black text-xs mono" data-testid="compose-tags" />
          </div>
          <div className="flex gap-2">
            <button onClick={submit} disabled={busy} className="flex-1 bg-black text-[#FFB300] py-2.5 text-sm font-semibold flex items-center justify-center gap-2 hover:bg-[#FFB300] hover:text-black border-2 border-black disabled:opacity-50" data-testid="compose-submit">
              <Send className="w-4 h-4" /> {busy ? 'Se publică…' : 'Publică discuție'}
            </button>
            <button onClick={onClose} className="border border-black px-5 py-2.5 text-sm hover:bg-gray-100">Renunță</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function ForumThreadView({ threadId }) {
  const { user } = useAuth();
  const nav = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reply, setReply] = useState('');
  const [busy, setBusy] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const { data } = await api.get(`/forum/threads/${threadId}`);
        setData(data);
      } catch (e) {
        toast.error('Discuție inexistentă.');
        nav('/forum');
      } finally {
        setLoading(false);
      }
    })();
  }, [threadId, nav, reloadKey]);

  const reload = () => setReloadKey(k => k + 1);

  async function postReply() {
    if (!user) { toast.error('Loghează-te ca să răspunzi.'); return; }
    if (reply.trim().length < 2) { toast.error('Răspunsul e prea scurt.'); return; }
    setBusy(true);
    try {
      await api.post(`/forum/threads/${threadId}/replies`, { body: reply });
      setReply('');
      reload();
      toast.success('Răspuns publicat.');
    } catch (e) { toast.error(e?.response?.data?.detail || 'Eroare.'); }
    finally { setBusy(false); }
  }

  async function toggleLike() {
    if (!user) { toast.error('Loghează-te ca să apreciezi.'); return; }
    try {
      const { data: r } = await api.post(`/forum/threads/${threadId}/like`);
      setData((d) => d ? { ...d, thread: { ...d.thread, likes: r.likes } } : d);
    } catch (e) { toast.error('Eroare.'); }
  }

  async function deleteThread() {
    if (!window.confirm('Ștergi această discuție definitiv?')) return;
    try {
      await api.delete(`/forum/threads/${threadId}`);
      toast.success('Discuție ștearsă.');
      nav('/forum');
    } catch (e) { toast.error('Eroare.'); }
  }

  if (loading) return <AppShell><div className="p-8 text-sm text-gray-500">Se încarcă…</div></AppShell>;
  if (!data) return null;

  const { thread, replies } = data;

  return (
    <AppShell>
      <div className="p-8 max-w-4xl" data-testid="thread-view">
        <Link to="/forum" className="text-xs text-gray-600 hover:text-black flex items-center gap-1.5 mb-4" data-testid="back-to-forum">
          <ArrowLeft className="w-3.5 h-3.5" /> Înapoi la forum
        </Link>

        <div className="bg-white border-2 border-black p-6 mb-6">
          <div className="flex items-center gap-2 text-xs text-gray-500 mb-3">
            <span className="bg-gray-100 px-2 py-0.5 text-[10px] uppercase tracking-wider font-semibold">{industryIcon(thread.industry)} {industryLabel(thread.industry)}</span>
            {thread.is_developer_post && <span className="bg-[#FFB300] text-black px-2 py-0.5 text-[10px] uppercase tracking-wider font-bold">Admin</span>}
            <span>•</span>
            <span className="font-semibold">{thread.author_name}</span>
            <span>•</span>
            <span>{timeAgo(thread.created_at)}</span>
          </div>
          <h1 className="text-3xl font-bold mb-4" data-testid="thread-title">{thread.title}</h1>
          <div className="prose prose-sm max-w-none text-sm leading-relaxed forum-md" data-testid="thread-body" dangerouslySetInnerHTML={renderMarkdown(thread.body)} />

          {thread.tags?.length > 0 && (
            <div className="flex gap-1.5 mt-4 flex-wrap">
              {thread.tags.map((tag) => <span key={tag} className="text-[10px] bg-gray-100 px-2 py-0.5 mono">#{tag}</span>)}
            </div>
          )}

          <div className="flex items-center gap-4 mt-5 pt-4 border-t border-gray-200">
            <button onClick={toggleLike} className="flex items-center gap-1.5 text-sm hover:text-[#FFB300]" data-testid="like-btn">
              <Heart className="w-4 h-4" /> {thread.likes} apreciere{thread.likes === 1 ? '' : 'i'}
            </button>
            <span className="flex items-center gap-1.5 text-sm text-gray-500"><Eye className="w-4 h-4" /> {thread.views} vizualizări</span>
            <span className="flex items-center gap-1.5 text-sm text-gray-500"><Reply className="w-4 h-4" /> {thread.reply_count} răspuns(uri)</span>
            {user?.is_developer && (
              <button onClick={deleteThread} className="ml-auto text-xs text-red-700 hover:bg-red-700 hover:text-white px-3 py-1.5 border border-red-700 flex items-center gap-1.5" data-testid="delete-thread-btn">
                <Trash2 className="w-3.5 h-3.5" /> Șterge
              </button>
            )}
          </div>
        </div>

        {/* Replies */}
        <div className="space-y-3 mb-6" data-testid="replies-list">
          {replies.length === 0 ? (
            <div className="text-sm text-gray-500 text-center py-6">Niciun răspuns încă. Fii primul.</div>
          ) : replies.map((r) => (
            <div key={r.reply_id} className="bg-white border border-gray-200 p-4" data-testid={`reply-${r.reply_id}`}>
              <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                <span className="font-semibold">{r.author_name}</span>
                {r.is_developer_post && <span className="bg-[#FFB300] text-black px-1.5 text-[9px] uppercase font-bold">Admin</span>}
                <span>•</span>
                <span>{timeAgo(r.created_at)}</span>
              </div>
              <div className="whitespace-pre-wrap text-sm leading-relaxed forum-md" dangerouslySetInnerHTML={renderMarkdown(r.body)} />
            </div>
          ))}
        </div>

        {/* Compose reply */}
        {user ? (
          <div className="bg-white border-2 border-black p-4" data-testid="reply-compose">
            <label className="text-xs uppercase text-gray-600">Răspunsul tău</label>
            <textarea value={reply} onChange={(e) => setReply(e.target.value)} rows={4} className="w-full mt-1 px-3 py-2 border border-black text-sm" maxLength={5000} data-testid="reply-textarea" />
            <button onClick={postReply} disabled={busy} className="mt-3 bg-black text-[#FFB300] px-5 py-2 text-sm flex items-center gap-2 hover:bg-[#FFB300] hover:text-black border-2 border-black disabled:opacity-50 font-semibold" data-testid="reply-submit-btn">
              <Send className="w-4 h-4" /> {busy ? 'Se publică…' : 'Răspunde'}
            </button>
          </div>
        ) : (
          <div className="bg-gray-50 border border-gray-200 p-4 text-sm text-center">
            <Link to="/login" className="text-[#FFB300] underline">Loghează-te</Link> ca să răspunzi.
          </div>
        )}
      </div>
    </AppShell>
  );
}
