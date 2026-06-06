import { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import api from '../lib/api';
import { useAuth } from '../contexts/AuthContext';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { Mail, ShieldCheck, CreditCard, Check, AlertCircle, ExternalLink, Save } from 'lucide-react';

const QES_FIELDS = {
  certsign: [
    { name: 'client_id', label: 'Client ID', type: 'text' },
    { name: 'client_secret', label: 'Client Secret', type: 'password' },
    { name: 'endpoint_url', label: 'Endpoint URL', type: 'text', placeholder: 'https://api.certsign.ro/sign/v1' },
    { name: 'certificate_alias', label: 'Alias certificat alocat', type: 'text' },
  ],
  digisign: [
    { name: 'client_id', label: 'Client ID OAuth2', type: 'text' },
    { name: 'client_secret', label: 'Client Secret', type: 'password' },
    { name: 'callback_url', label: 'Callback URL', type: 'text' },
    { name: 'account_id', label: 'Account ID DigiSign', type: 'text' },
  ],
  transsped: [
    { name: 'api_key', label: 'API Key', type: 'password' },
    { name: 'endpoint_url', label: 'Endpoint URL', type: 'text' },
    { name: 'user_id', label: 'User ID Trans Sped', type: 'text' },
  ],
};

function QesCredentialsForm({ provider }) {
  const [creds, setCreds] = useState({});
  const [busy, setBusy] = useState(false);
  const fields = QES_FIELDS[provider] || [];

  const submit = async (e) => {
    e.preventDefault();
    if (Object.keys(creds).length === 0) { toast.error('Completați măcar un câmp'); return; }
    setBusy(true);
    try {
      await api.put('/qes/credentials', { provider, credentials: creds });
      toast.success('Credențiale QES salvate');
      setCreds({});
    } catch (err) { toast.error(err?.response?.data?.detail || 'Eroare'); }
    finally { setBusy(false); }
  };

  if (fields.length === 0) return null;

  return (
    <details className="text-xs mb-3 bg-[#F9FAFB] border border-gray-200">
      <summary className="cursor-pointer text-gray-700 font-semibold p-2.5">Completează credențialele API</summary>
      <form onSubmit={submit} className="p-3 space-y-2.5 border-t border-gray-200" data-testid={`qes-creds-${provider}`}>
        {fields.map(f => (
          <div key={f.name}>
            <label className="label block mb-0.5 text-[9px]">{f.label}</label>
            <input
              type={f.type}
              placeholder={f.placeholder}
              value={creds[f.name] || ''}
              onChange={(e) => setCreds({ ...creds, [f.name]: e.target.value })}
              className="w-full border border-gray-300 px-2 py-1.5 text-xs rounded-sm mono"
              data-testid={`qes-${provider}-${f.name}`}
            />
          </div>
        ))}
        <button disabled={busy} className="amber-btn w-full text-xs py-1.5" data-testid={`qes-save-${provider}`}>
          <Save className="w-3 h-3" /> {busy ? 'Se salvează...' : 'Salvează credențiale'}
        </button>
        <p className="text-[10px] text-gray-500">Datele sunt stocate criptate pe contul dvs. Nu sunt afișate niciodată după salvare.</p>
      </form>
    </details>
  );
}

export default function Settings() {
  const { user, refresh } = useAuth();
  const [gmailUser, setGmailUser] = useState('');
  const [gmailPwd, setGmailPwd] = useState('');
  const [secondaryEmail, setSecondaryEmail] = useState('');
  const [configured, setConfigured] = useState(false);
  const [busy, setBusy] = useState(false);
  const [secBusy, setSecBusy] = useState(false);
  const [providers, setProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState(user?.qes_provider || null);

  useEffect(() => {
    (async () => {
      try {
        const [{ data: e }, { data: p }] = await Promise.all([
          api.get('/users/me/email-config'),
          api.get('/qes/providers'),
        ]);
        setConfigured(e.configured);
        setGmailUser(e.gmail_user || '');
        setSecondaryEmail(e.secondary_email || '');
        setProviders(p);
      } catch (err) {
        console.error('Settings load failed:', err);
      }
    })();
  }, []);

  const saveSecondaryEmail = async (e) => {
    e.preventDefault();
    setSecBusy(true);
    try {
      await api.patch('/users/me', { secondary_email: secondaryEmail.trim() });
      toast.success(secondaryEmail ? 'Email business secundar salvat — va fi adăugat automat în CC' : 'Email business eliminat');
      await refresh();
    } catch (err) { toast.error(err?.response?.data?.detail || 'Eroare'); }
    finally { setSecBusy(false); }
  };

  const saveGmail = async (e) => {
    e.preventDefault();
    if (!gmailUser || !gmailPwd) { toast.error('Completați ambele câmpuri'); return; }
    setBusy(true);
    try {
      await api.patch('/users/me', {
        gmail_user: gmailUser.trim(),
        gmail_app_password: gmailPwd.replace(/\s/g, ''),
      });
      toast.success('Credențiale Gmail salvate');
      setConfigured(true);
      setGmailPwd('');
      await refresh();
    } catch (err) { toast.error(err?.response?.data?.detail || 'Eroare'); }
    finally { setBusy(false); }
  };

  const removeGmail = async () => {
    if (!window.confirm('Eliminați credențialele Gmail?')) return;
    try {
      await api.patch('/users/me', { gmail_user: '', gmail_app_password: '' });
      setConfigured(false); setGmailUser(''); setGmailPwd('');
      toast.success('Credențiale eliminate');
      await refresh();
    } catch (err) { toast.error(err?.response?.data?.detail || 'Eroare'); }
  };

  const saveProvider = async (id) => {
    try {
      await api.patch('/users/me', { qes_provider: id });
      setSelectedProvider(id);
      toast.success('Provider QES actualizat');
      await refresh();
    } catch (err) { toast.error(err?.response?.data?.detail || 'Eroare'); }
  };

  return (
    <AppShell title="Setări">
      {/* Profile + Plan */}
      <div className="grid lg:grid-cols-3 gap-px bg-gray-200 border border-gray-200 mb-8">
        <div className="lg:col-span-2 bg-white p-8">
          <div className="label mb-4">// Profil</div>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between border-b border-gray-100 pb-2"><dt className="text-gray-500">Nume</dt><dd className="font-medium" data-testid="settings-name">{user?.name}</dd></div>
            <div className="flex justify-between border-b border-gray-100 pb-2"><dt className="text-gray-500">Email cont</dt><dd className="font-medium" data-testid="settings-email">{user?.email}</dd></div>
            <div className="flex justify-between border-b border-gray-100 pb-2"><dt className="text-gray-500">Firmă</dt><dd className="font-medium">{user?.company || '—'}</dd></div>
            <div className="flex justify-between border-b border-gray-100 pb-2"><dt className="text-gray-500">Autentificare</dt><dd className="font-medium uppercase">{user?.auth_provider}</dd></div>
            <div className="flex justify-between"><dt className="text-gray-500">Membru din</dt><dd className="font-medium">{user?.created_at ? new Date(user.created_at).toLocaleDateString('ro-RO') : '—'}</dd></div>
          </dl>
        </div>
        <div className="bg-white p-8">
          <div className="label mb-4">// Plan & facturare</div>
          <div className="flex items-center gap-2 mb-2"><CreditCard className="w-4 h-4" /> <span className="text-xs uppercase tracking-[0.2em] text-gray-500">Plan curent</span></div>
          <div className="text-2xl font-bold uppercase tracking-tight mb-2" data-testid="current-plan">{user?.plan}</div>
          {user?.plan_renews_at && (<div className="text-xs text-gray-500 mb-4">Reînnoire: {new Date(user.plan_renews_at).toLocaleDateString('ro-RO')}</div>)}
          <Link to="/pricing" className="amber-btn w-full" data-testid="manage-plan-btn">Gestionează plan</Link>
        </div>
      </div>

      {/* Gmail config */}
      <div className="bg-white border border-gray-200 p-8 mb-8" data-testid="gmail-config-section">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-10 h-10 bg-black text-[#FFB300] flex items-center justify-center shrink-0"><Mail className="w-5 h-5" /></div>
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-xl font-semibold tracking-tight">Configurare email — Gmail</h2>
              {configured ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-[#16A34A]/10 text-[#16A34A] text-xs font-semibold uppercase tracking-wider"><Check className="w-3 h-3" />Configurat</span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-[#DC2626]/10 text-[#DC2626] text-xs font-semibold uppercase tracking-wider"><AlertCircle className="w-3 h-3" />Neconfigurat</span>
              )}
            </div>
            <p className="text-sm text-gray-600 mt-2">Emailurile cu documentele generate vor fi trimise <strong>din contul dvs. Gmail</strong>. Folosim SMTP cu App Password — Google nu permite parola normală pentru aplicații externe.</p>
          </div>
        </div>

        <details className="mb-6 bg-[#F9FAFB] border border-gray-200 p-4 text-sm">
          <summary className="cursor-pointer font-semibold flex items-center gap-2"><span className="text-[#FFB300]">→</span> Cum obțin un App Password Google?</summary>
          <ol className="mt-4 space-y-2 list-decimal pl-5 text-gray-700">
            <li>Mergeți la <a href="https://myaccount.google.com/security" target="_blank" rel="noreferrer" className="underline font-medium inline-flex items-center gap-1">myaccount.google.com/security <ExternalLink className="w-3 h-3" /></a></li>
            <li>Activați <strong>verificarea în 2 pași</strong> (dacă nu e deja).</li>
            <li>În aceeași pagină, accesați <strong>App passwords</strong> (sau <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" className="underline">myaccount.google.com/apppasswords</a>).</li>
            <li>Creați parolă nouă pentru aplicația &bdquo;StampDoc&rdquo;. Veți primi 16 caractere — copiați-le și lipiți-le mai jos.</li>
            <li>Salvați. Gata!</li>
          </ol>
        </details>

        <form onSubmit={saveGmail} className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="label block mb-2">Adresă Gmail</label>
            <input
              data-testid="gmail-user-input"
              type="email"
              value={gmailUser}
              onChange={e => setGmailUser(e.target.value)}
              placeholder="nume@gmail.com"
              className="w-full border border-gray-300 px-3 py-2.5 text-sm rounded-sm focus:outline-none focus:border-[#FFB300] focus:ring-2 focus:ring-[#FFB300]/30"
              required
            />
          </div>
          <div>
            <label className="label block mb-2">App Password (16 caractere)</label>
            <input
              data-testid="gmail-password-input"
              type="password"
              value={gmailPwd}
              onChange={e => setGmailPwd(e.target.value)}
              placeholder={configured ? '•••• •••• •••• ••••' : 'xxxx xxxx xxxx xxxx'}
              className="w-full border border-gray-300 px-3 py-2.5 text-sm rounded-sm mono focus:outline-none focus:border-[#FFB300] focus:ring-2 focus:ring-[#FFB300]/30"
            />
          </div>
          <div className="md:col-span-2 flex items-center gap-2">
            <button type="submit" disabled={busy} className="amber-btn disabled:opacity-50" data-testid="save-gmail-btn">
              {busy ? 'Se salvează...' : (configured ? 'Actualizează' : 'Salvează')}
            </button>
            {configured && (
              <button type="button" onClick={removeGmail} className="ghost-btn text-[#DC2626]" data-testid="remove-gmail-btn">Elimină credențialele</button>
            )}
          </div>
        </form>
      </div>

      {/* Secondary Business Email */}
      <div className="bg-white border border-gray-200 p-8 mb-8" data-testid="secondary-email-section">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-10 h-10 bg-[#FFB300] text-black flex items-center justify-center shrink-0"><Mail className="w-5 h-5" /></div>
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-xl font-semibold tracking-tight">Email business secundar</h2>
              {secondaryEmail && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-[#16A34A]/10 text-[#16A34A] text-xs font-semibold uppercase tracking-wider"><Check className="w-3 h-3" />Activ</span>
              )}
            </div>
            <p className="text-sm text-gray-600 mt-2">Adresa companiei (ex: <span className="mono">contact@firma.ro</span>) primește automat <strong>CC</strong> la fiecare email trimis prin platformă. Util pentru evidență centralizată a corespondenței tehnice.</p>
          </div>
        </div>
        <form onSubmit={saveSecondaryEmail} className="grid md:grid-cols-[1fr_auto] gap-3 items-end">
          <div>
            <label className="label block mb-2">Adresă business (opțional)</label>
            <input
              data-testid="secondary-email-input"
              type="email"
              value={secondaryEmail}
              onChange={(e) => setSecondaryEmail(e.target.value)}
              placeholder="contact@firma-ta.ro"
              className="w-full border border-gray-300 px-3 py-2.5 text-sm rounded-sm focus:outline-none focus:border-[#FFB300] focus:ring-2 focus:ring-[#FFB300]/30"
            />
          </div>
          <button type="submit" disabled={secBusy} className="amber-btn disabled:opacity-50 h-[42px]" data-testid="save-secondary-email-btn">
            <Save className="w-3.5 h-3.5" /> {secBusy ? 'Se salvează…' : (secondaryEmail ? 'Salvează' : 'Elimină')}
          </button>
        </form>
      </div>

      {/* Admin panel teaser (only for admins/devs) */}
      {(user?.is_developer || user?.is_admin) && (
        <Link to="/admin/config" data-testid="admin-config-link" className="block relative overflow-hidden mb-8 bg-gradient-to-br from-[#0A0A0A] via-[#1a1a1a] to-[#0A0A0A] text-white p-6 border-l-4 border-[#FFB300] hover:border-l-8 transition-all group">
          <div className="absolute -right-12 -top-12 w-40 h-40 bg-[#FFB300]/10 blur-3xl rounded-full pointer-events-none" />
          <div className="relative flex items-center gap-4">
            <div className="w-12 h-12 bg-[#FFB300] text-black flex items-center justify-center shrink-0"><ShieldCheck className="w-6 h-6" /></div>
            <div className="flex-1">
              <div className="text-[10px] uppercase tracking-[0.25em] text-[#FFB300] mb-1">// admin only</div>
              <div className="text-lg font-bold tracking-tight">Configurare globală platformă</div>
              <p className="text-sm text-gray-300 mt-1">SMTP global · Feature flags · Gestionare utilizatori · Bannere & mentenanță</p>
            </div>
            <div className="text-[#FFB300] group-hover:translate-x-1 transition-transform text-2xl">→</div>
          </div>
        </Link>
      )}

      {/* QES provider */}
      <div className="bg-white border border-gray-200 p-8 mb-8" data-testid="qes-config-section">
        <div className="flex items-start gap-4 mb-6">
          <div className="w-10 h-10 bg-[#FFB300] text-black flex items-center justify-center shrink-0"><ShieldCheck className="w-5 h-5" /></div>
          <div className="flex-1">
            <h2 className="text-xl font-semibold tracking-tight">Furnizor semnătură electronică calificată (QES)</h2>
            <p className="text-sm text-gray-600 mt-2">Pentru semnături conforme eIDAS de nivel <strong>calificat</strong> (QES) sunt necesare contracte cu prestatori autorizați. În prezent folosim semnătura locală PKCS#12 (Mock). Pentru activarea integrărilor reale, completați credențialele primite de la furnizor după semnarea contractului.</p>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-px bg-gray-200 border border-gray-200">
          {providers.map((p) => {
            const isSelected = selectedProvider === p.id;
            const isActive = p.status === 'active';
            return (
              <div key={p.id} className={`bg-white p-5 ${isSelected ? 'ring-2 ring-[#FFB300] ring-inset' : ''}`} data-testid={`qes-${p.id}`}>
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold">{p.name}</h3>
                  <span className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 ${isActive ? 'bg-[#16A34A]/10 text-[#16A34A]' : 'bg-gray-100 text-gray-500'}`}>
                    {isActive ? 'Activ' : 'În așteptare'}
                  </span>
                </div>
                <p className="text-xs text-gray-600 mb-3">{p.description}</p>
                {p.setup_guide && (
                  <details className="text-xs mb-3">
                    <summary className="cursor-pointer text-gray-700 font-semibold">Ghid de activare</summary>
                    <ul className="mt-2 space-y-1 text-gray-600 list-decimal pl-4">
                      {p.setup_guide.map((step) => <li key={step}>{step.replace(/^\d+\.\s*/, '')}</li>)}
                    </ul>
                  </details>
                )}

                {/* Credentials form for real providers (non-mock) */}
                {p.id !== 'mock' && (
                  <QesCredentialsForm provider={p.id} />
                )}

                <button
                  onClick={() => saveProvider(p.id)}
                  disabled={isSelected}
                  className={isSelected ? 'outline-btn w-full justify-center text-xs py-2 cursor-default mt-2' : 'amber-btn w-full text-xs py-2 disabled:opacity-40 disabled:cursor-not-allowed mt-2'}
                  data-testid={`qes-select-${p.id}`}
                >
                  {isSelected ? '✓ Selectat' : 'Selectează ca provider activ'}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      <div className="text-xs text-gray-500 text-center">
        Vezi <Link to="/termeni" className="underline">Termeni</Link> · <Link to="/confidentialitate" className="underline">Confidențialitate</Link> · <Link to="/gdpr" className="underline">GDPR</Link>
      </div>
    </AppShell>
  );
}
