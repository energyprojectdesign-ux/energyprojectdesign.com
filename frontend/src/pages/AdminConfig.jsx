import { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import api from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheck, Mail, ToggleLeft, ToggleRight, Save, AlertTriangle, Search,
  Users, FileText, Activity, MessagesSquare, Megaphone, Wrench, Crown, Ban, RefreshCw, KeyRound,
} from 'lucide-react';

const FEATURE_FLAGS = [
  { key: 'feature_forum_enabled', label: 'Forum comunitate', icon: MessagesSquare },
  { key: 'feature_email_enabled', label: 'Trimitere email-uri', icon: Mail },
  { key: 'feature_pdf_enabled', label: 'Export PDF', icon: FileText },
  { key: 'feature_photovoltaic_enabled', label: 'Modul fotovoltaic', icon: Activity },
  { key: 'feature_ai_assistant_enabled', label: 'AI Assistant', icon: Wrench },
  { key: 'feature_payments_enabled', label: 'Plăți Stripe', icon: KeyRound },
];

const LEVEL_OPTIONS = [
  { v: 'info', label: 'Informativ', color: 'bg-sky-50 text-sky-700 border-sky-200' },
  { v: 'success', label: 'Succes', color: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  { v: 'warning', label: 'Avertisment', color: 'bg-amber-50 text-amber-800 border-amber-200' },
  { v: 'danger', label: 'Critic', color: 'bg-rose-50 text-rose-700 border-rose-200' },
];

function Toggle({ value, onChange, testid }) {
  return (
    <button
      onClick={() => onChange(!value)}
      data-testid={testid}
      className={`inline-flex items-center gap-1 px-2 py-1 text-[11px] uppercase tracking-wider font-semibold border transition-all ${value ? 'bg-emerald-50 text-emerald-700 border-emerald-300' : 'bg-gray-50 text-gray-500 border-gray-200'}`}
    >
      {value ? <ToggleRight className="w-3.5 h-3.5" /> : <ToggleLeft className="w-3.5 h-3.5" />}
      {value ? 'Activ' : 'Inactiv'}
    </button>
  );
}

export default function AdminConfig() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const isAdmin = user?.is_developer || user?.is_admin;
  const [cfg, setCfg] = useState(null);
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [userSearch, setUserSearch] = useState('');
  const [usersLoading, setUsersLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [smtpPwd, setSmtpPwd] = useState('');

  useEffect(() => {
    if (!isAdmin) { navigate('/settings', { replace: true }); return; }
    (async () => {
      try {
        const [c, s] = await Promise.all([
          api.get('/admin/config'),
          api.get('/admin/stats'),
        ]);
        setCfg(c.data);
        setStats(s.data);
      } catch (err) {
        toast.error(err?.response?.data?.detail || 'Eroare încărcare config admin');
      }
    })();
  }, [isAdmin, navigate]);

  const loadUsers = async (q) => {
    try {
      const { data } = await api.get('/admin/users', { params: { search: q || undefined, limit: 50 } });
      setUsers(data.users || []);
    } catch (err) {
      toast.error('Eroare listare utilizatori');
    } finally {
      setUsersLoading(false);
    }
  };

  useEffect(() => {
    if (!isAdmin) return;
    (async () => {
      setUsersLoading(true);
      await loadUsers('');
    })();
  }, [isAdmin]);

  if (!isAdmin) return null;
  const levelMeta = LEVEL_OPTIONS.find((l) => l.v === cfg?.announcement_level) || LEVEL_OPTIONS[0];
  if (!cfg) return <AppShell title="Admin Config"><div className="p-12 text-sm text-gray-500">Se încarcă…</div></AppShell>;

  const updateCfg = (patch) => setCfg((c) => ({ ...c, ...patch }));

  const save = async (patch) => {
    setBusy(true);
    try {
      const payload = { ...patch };
      if (smtpPwd) payload.smtp_global_password = smtpPwd;
      const { data } = await api.put('/admin/config', payload);
      setCfg(data);
      setSmtpPwd('');
      toast.success('Configurare salvată');
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Eroare salvare');
    } finally { setBusy(false); }
  };

  const updateUser = async (uid, patch) => {
    try {
      await api.patch(`/admin/users/${uid}`, patch);
      toast.success('Utilizator actualizat');
      loadUsers(userSearch);
    } catch (err) { toast.error(err?.response?.data?.detail || 'Eroare actualizare'); }
  };

  return (
    <AppShell title="Admin Configuration" subtitle="Panou de control rezervat administratorilor platformei">
      {/* Hero stats */}
      <div className="relative overflow-hidden mb-8 bg-gradient-to-br from-[#0A0A0A] via-[#1a1a1a] to-[#0A0A0A] text-white p-6 lg:p-8 border-l-4 border-[#FFB300]" data-testid="admin-hero">
        <div className="absolute -right-12 -top-12 w-48 h-48 bg-[#FFB300]/10 blur-3xl rounded-full pointer-events-none" />
        <div className="absolute -left-8 bottom-0 w-32 h-32 bg-[#FFB300]/5 blur-2xl rounded-full pointer-events-none" />
        <div className="relative flex items-start gap-5">
          <div className="w-14 h-14 bg-[#FFB300] text-black flex items-center justify-center shrink-0">
            <ShieldCheck className="w-7 h-7" strokeWidth={2.4} />
          </div>
          <div className="flex-1">
            <div className="text-[10px] uppercase tracking-[0.25em] text-[#FFB300] mb-1">// platform control center</div>
            <h2 className="text-2xl lg:text-3xl font-bold tracking-tight mb-2">Bun venit, {user.name}.</h2>
            <p className="text-sm text-gray-300 max-w-2xl leading-relaxed">Configurarea globală afectează <strong>toți utilizatorii</strong>. Modificările sunt logate în registrul de audit și ireversibile odată propagate.</p>
          </div>
        </div>
        {stats && (
          <div className="relative mt-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3" data-testid="admin-stats">
            {[
              ['Utilizatori', stats.users_total, Users],
              ['Admini', stats.admins_total, Crown],
              ['Proiecte', stats.projects_total, FileText],
              ['Documente', stats.documents_total, FileText],
              ['Email-uri', stats.emails_sent, Mail],
              ['Discuții forum', stats.forum_threads, MessagesSquare],
            ].map(([label, val, Icon]) => (
              <div key={label} className="bg-white/5 backdrop-blur-sm border border-white/10 p-3" data-testid={`stat-${label}`}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[9px] uppercase tracking-[0.2em] text-gray-400">{label}</span>
                  <Icon className="w-3 h-3 text-[#FFB300]" />
                </div>
                <div className="text-2xl font-bold tracking-tight">{val}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Maintenance + Announcement */}
      <div className="grid lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white border border-gray-200 p-6" data-testid="admin-maintenance">
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h3 className="font-semibold tracking-tight">Mod mentenanță</h3>
            <span className="ml-auto"><Toggle value={cfg.maintenance_mode} onChange={(v) => updateCfg({ maintenance_mode: v })} testid="toggle-maintenance" /></span>
          </div>
          <textarea
            value={cfg.maintenance_message || ''}
            onChange={(e) => updateCfg({ maintenance_message: e.target.value })}
            placeholder="Mesaj afișat în timpul mentenanței (vizibil tuturor utilizatorilor)"
            className="w-full border border-gray-200 px-3 py-2 text-sm rounded-sm h-20 focus:border-[#FFB300] focus:ring-2 focus:ring-[#FFB300]/30 outline-none resize-none"
            data-testid="maintenance-message"
          />
          <button onClick={() => save({ maintenance_mode: cfg.maintenance_mode, maintenance_message: cfg.maintenance_message })} disabled={busy} className="mt-3 amber-btn text-xs py-2 px-3" data-testid="save-maintenance">
            <Save className="w-3 h-3" /> Salvează
          </button>
        </div>

        <div className="bg-white border border-gray-200 p-6" data-testid="admin-announcement">
          <div className="flex items-center gap-3 mb-4">
            <Megaphone className="w-5 h-5 text-sky-600" />
            <h3 className="font-semibold tracking-tight">Banner anunțuri</h3>
            <span className={`ml-auto text-[10px] px-2 py-0.5 uppercase tracking-wider font-semibold border ${levelMeta.color}`}>{levelMeta.label}</span>
          </div>
          <input
            type="text"
            value={cfg.announcement_banner || ''}
            onChange={(e) => updateCfg({ announcement_banner: e.target.value })}
            placeholder="Anunț scurt (ex: Actualizare v5.4 disponibilă)"
            className="w-full border border-gray-200 px-3 py-2 text-sm rounded-sm focus:border-[#FFB300] focus:ring-2 focus:ring-[#FFB300]/30 outline-none mb-3"
            data-testid="announcement-input"
          />
          <div className="flex flex-wrap gap-2">
            {LEVEL_OPTIONS.map((l) => (
              <button
                key={l.v}
                onClick={() => updateCfg({ announcement_level: l.v })}
                data-testid={`level-${l.v}`}
                className={`text-[10px] px-2 py-1 uppercase tracking-wider font-semibold border transition-all ${cfg.announcement_level === l.v ? l.color : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'}`}
              >{l.label}</button>
            ))}
          </div>
          <button onClick={() => save({ announcement_banner: cfg.announcement_banner, announcement_level: cfg.announcement_level })} disabled={busy} className="mt-3 amber-btn text-xs py-2 px-3" data-testid="save-announcement">
            <Save className="w-3 h-3" /> Salvează
          </button>
        </div>
      </div>

      {/* Global SMTP */}
      <div className="bg-white border border-gray-200 p-6 mb-8" data-testid="admin-smtp">
        <div className="flex items-start gap-4 mb-5">
          <div className="w-11 h-11 bg-black text-[#FFB300] flex items-center justify-center shrink-0"><Mail className="w-5 h-5" /></div>
          <div>
            <h3 className="font-semibold text-lg tracking-tight">SMTP global (fallback platformă)</h3>
            <p className="text-xs text-gray-500 mt-1">Folosit când utilizatorul <strong>nu</strong> are propriul cont Gmail configurat. Conține Gmail-ul oficial Energy Project Design.</p>
          </div>
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="label block mb-1.5">From Name</label>
            <input type="text" value={cfg.smtp_from_name || ''} onChange={(e) => updateCfg({ smtp_from_name: e.target.value })} className="w-full border border-gray-200 px-3 py-2 text-sm rounded-sm focus:border-[#FFB300] focus:ring-2 focus:ring-[#FFB300]/30 outline-none" data-testid="smtp-from-name" />
          </div>
          <div>
            <label className="label block mb-1.5">Gmail platformă</label>
            <input type="email" value={cfg.smtp_global_user || ''} onChange={(e) => updateCfg({ smtp_global_user: e.target.value })} placeholder="platforma@energyprojectdesign.ro" className="w-full border border-gray-200 px-3 py-2 text-sm rounded-sm focus:border-[#FFB300] focus:ring-2 focus:ring-[#FFB300]/30 outline-none" data-testid="smtp-user" />
          </div>
          <div>
            <label className="label block mb-1.5">App Password {cfg.smtp_global_password_set && <span className="text-[10px] text-emerald-600 ml-1">(configurat)</span>}</label>
            <input type="password" value={smtpPwd} onChange={(e) => setSmtpPwd(e.target.value)} placeholder={cfg.smtp_global_password_set ? '•••• •••• •••• ••••' : 'xxxx xxxx xxxx xxxx'} className="w-full border border-gray-200 px-3 py-2 text-sm rounded-sm mono focus:border-[#FFB300] focus:ring-2 focus:ring-[#FFB300]/30 outline-none" data-testid="smtp-password" />
          </div>
        </div>
        <div className="mt-5 flex items-center justify-between border-t border-gray-100 pt-4">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input type="checkbox" checked={!!cfg.smtp_cc_secondary_default} onChange={(e) => updateCfg({ smtp_cc_secondary_default: e.target.checked })} className="w-4 h-4 accent-black" data-testid="smtp-cc-default" />
            <span>CC automat email business secundar al fiecărui utilizator</span>
          </label>
          <button onClick={() => save({ smtp_from_name: cfg.smtp_from_name, smtp_global_user: cfg.smtp_global_user, smtp_cc_secondary_default: cfg.smtp_cc_secondary_default })} disabled={busy} className="amber-btn text-xs py-2 px-4" data-testid="save-smtp">
            <Save className="w-3 h-3" /> Salvează SMTP
          </button>
        </div>
      </div>

      {/* Feature flags */}
      <div className="bg-white border border-gray-200 p-6 mb-8" data-testid="admin-features">
        <div className="flex items-center gap-3 mb-5">
          <Activity className="w-5 h-5 text-[#FFB300]" />
          <h3 className="font-semibold tracking-tight">Module platformă (feature flags)</h3>
          <button onClick={() => save({
            feature_forum_enabled: cfg.feature_forum_enabled,
            feature_email_enabled: cfg.feature_email_enabled,
            feature_pdf_enabled: cfg.feature_pdf_enabled,
            feature_photovoltaic_enabled: cfg.feature_photovoltaic_enabled,
            feature_ai_assistant_enabled: cfg.feature_ai_assistant_enabled,
            feature_payments_enabled: cfg.feature_payments_enabled,
          })} disabled={busy} className="ml-auto amber-btn text-xs py-2 px-3" data-testid="save-features">
            <Save className="w-3 h-3" /> Salvează toate
          </button>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-px bg-gray-200 border border-gray-200">
          {FEATURE_FLAGS.map((f) => {
            const Icon = f.icon;
            const enabled = cfg[f.key];
            return (
              <div key={f.key} className="bg-white p-4 flex items-center gap-3" data-testid={`feature-flag-${f.key}`}>
                <div className={`w-10 h-10 flex items-center justify-center ${enabled ? 'bg-emerald-50 text-emerald-600' : 'bg-gray-100 text-gray-400'}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm">{f.label}</div>
                  <div className="text-[10px] text-gray-500 mono uppercase tracking-wider">{f.key}</div>
                </div>
                <Toggle value={enabled} onChange={(v) => updateCfg({ [f.key]: v })} testid={`flag-${f.key}`} />
              </div>
            );
          })}
        </div>
      </div>

      {/* Users mgmt */}
      <div className="bg-white border border-gray-200 p-6 mb-8" data-testid="admin-users">
        <div className="flex items-center gap-3 mb-5">
          <Users className="w-5 h-5 text-[#FFB300]" />
          <h3 className="font-semibold tracking-tight">Gestionare utilizatori</h3>
          <div className="ml-auto flex items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-2.5" />
              <input
                type="text"
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && loadUsers(userSearch)}
                placeholder="Caută email/nume/firmă…"
                className="text-sm border border-gray-200 pl-8 pr-3 py-1.5 rounded-sm focus:border-[#FFB300] focus:ring-2 focus:ring-[#FFB300]/30 outline-none w-64"
                data-testid="user-search"
              />
            </div>
            <button onClick={() => { setUsersLoading(true); loadUsers(userSearch); }} className="outline-btn text-xs py-1.5 px-3" data-testid="user-search-btn">
              <RefreshCw className={`w-3 h-3 ${usersLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-black text-[#FFB300] text-[10px] uppercase tracking-wider">
              <tr>
                <th className="text-left px-3 py-2.5 font-semibold">Email</th>
                <th className="text-left px-3 py-2.5 font-semibold">Nume</th>
                <th className="text-left px-3 py-2.5 font-semibold">Firmă</th>
                <th className="text-left px-3 py-2.5 font-semibold">Plan</th>
                <th className="text-center px-3 py-2.5 font-semibold">Rol</th>
                <th className="text-center px-3 py-2.5 font-semibold">Status</th>
                <th className="text-right px-3 py-2.5 font-semibold">Acțiuni</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const isAdminU = u.is_admin || u.is_developer;
                return (
                  <tr key={u.user_id} className="border-b border-gray-100 hover:bg-gray-50" data-testid={`user-row-${u.user_id}`}>
                    <td className="px-3 py-2.5 font-mono text-[12px]">{u.email}</td>
                    <td className="px-3 py-2.5">{u.name}</td>
                    <td className="px-3 py-2.5 text-gray-600">{u.company || '—'}</td>
                    <td className="px-3 py-2.5"><span className="text-[10px] uppercase tracking-wider font-semibold bg-gray-100 px-1.5 py-0.5">{u.plan}</span></td>
                    <td className="px-3 py-2.5 text-center">
                      {isAdminU ? (
                        <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-wider font-semibold text-[#FFB300] bg-black px-1.5 py-0.5"><Crown className="w-3 h-3" />Admin</span>
                      ) : (
                        <span className="text-[10px] uppercase tracking-wider text-gray-500">User</span>
                      )}
                    </td>
                    <td className="px-3 py-2.5 text-center">
                      {u.is_banned ? (
                        <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-wider font-semibold text-rose-700 bg-rose-50 px-1.5 py-0.5"><Ban className="w-3 h-3" />Suspendat</span>
                      ) : (
                        <span className="text-[10px] uppercase tracking-wider text-emerald-600">Activ</span>
                      )}
                    </td>
                    <td className="px-3 py-2.5 text-right">
                      <div className="inline-flex gap-1">
                        {!u.is_developer && (
                          <button onClick={() => updateUser(u.user_id, { is_admin: !isAdminU })} className="text-[10px] px-2 py-1 border border-gray-300 hover:bg-black hover:text-[#FFB300] uppercase tracking-wider" data-testid={`toggle-admin-${u.user_id}`}>
                            {isAdminU ? 'Retrogradează' : 'Promovează'}
                          </button>
                        )}
                        <button onClick={() => updateUser(u.user_id, { is_banned: !u.is_banned })} className={`text-[10px] px-2 py-1 border uppercase tracking-wider ${u.is_banned ? 'border-emerald-300 text-emerald-700 hover:bg-emerald-50' : 'border-rose-300 text-rose-700 hover:bg-rose-50'}`} data-testid={`toggle-ban-${u.user_id}`}>
                          {u.is_banned ? 'Reactivează' : 'Suspendă'}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {users.length === 0 && (
                <tr><td colSpan={7} className="px-3 py-8 text-center text-gray-400 text-sm">Niciun utilizator găsit</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="text-[10px] text-gray-400 text-center uppercase tracking-[0.2em]">
        // Energy Project Design · Admin Panel · {new Date().getFullYear()}
      </div>
    </AppShell>
  );
}
