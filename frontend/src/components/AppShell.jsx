import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ActiveProjectBar from './ActiveProjectBar';
import LicenseTimer from './LicenseTimer';
import {
  LayoutDashboard, ClipboardList, Settings2, Calculator, FileText, FileCheck2,
  Stamp, ShieldCheck, Mail, BadgeCheck, GaugeCircle, CreditCard, Settings, LogOut,
  Sparkles, Wrench, ListChecks, Flame, ChevronRight, FolderKanban, Github, Banknote, MessageSquare, Building2,
  Layers, Compass, BarChart3, Sun,
} from 'lucide-react';

const SECTIONS = [
  {
    title: 'Operațional',
    items: [
      { to: '/dashboard', label: 'Panou principal', icon: LayoutDashboard, tid: 'nav-dashboard' },
      { to: '/proiecte', label: 'Proiecte', icon: FolderKanban, tid: 'nav-proiecte' },
      { to: '/industrii', label: 'Industrii (12)', icon: Compass, tid: 'nav-industrii' },
      { to: '/feat-uri', label: 'Feat-uri viziune', icon: Layers, tid: 'nav-feat-uri' },
      { to: '/proiect', label: 'Date proiect activ', icon: ClipboardList, tid: 'nav-proiect' },
      { to: '/tehnice', label: 'Date tehnice', icon: Settings2, tid: 'nav-tehnice' },
      { to: '/calcul', label: 'Calcul inteligent', icon: Calculator, tid: 'nav-calcul' },
      { to: '/fotovoltaic', label: 'Calcul fotovoltaic', icon: Sun, tid: 'nav-fotovoltaic' },
    ],
  },
  {
    title: 'Documentație',
    items: [
      { to: '/templates', label: 'Șabloane', icon: FileText, tid: 'nav-templates' },
      { to: '/documents', label: 'Documente', icon: FileCheck2, tid: 'nav-documents' },
      { to: '/stamps', label: 'Ștampile', icon: Stamp, tid: 'nav-stamps' },
      { to: '/certificate', label: 'Certificate PKI', icon: ShieldCheck, tid: 'nav-certificate' },
      { to: '/certificari', label: 'Certificări interne', icon: BadgeCheck, tid: 'nav-certificari' },
    ],
  },
  {
    title: 'Comunicare & Control',
    items: [
      { to: '/email', label: 'Email-uri', icon: Mail, tid: 'nav-email' },
      { to: '/forum', label: 'Forum comunitate', icon: MessageSquare, tid: 'nav-forum' },
      { to: '/verifica', label: 'Verifică documentație', icon: GaugeCircle, tid: 'nav-verifica' },
      { to: '/ai', label: 'AI Assistant', icon: Sparkles, tid: 'nav-ai' },
      { to: '/audit', label: 'Audit interfață', icon: ListChecks, tid: 'nav-audit' },
    ],
  },
  {
    title: 'Cont',
    items: [
      { to: '/company', label: 'Profil societate', icon: Building2, tid: 'nav-company' },
      { to: '/pricing', label: 'Planuri & achiziții', icon: CreditCard, tid: 'nav-pricing' },
      { to: '/logs', label: 'Registru audit', icon: ListChecks, tid: 'nav-logs' },
      { to: '/settings', label: 'Setări', icon: Settings, tid: 'nav-settings' },
    ],
  },
];

export default function AppShell({ children, title, subtitle }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#F9FAFB] flex">
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col sticky top-0 h-screen overflow-y-auto" data-testid="app-sidebar">
        <div className="px-6 py-5 border-b border-gray-200">
          <Link to="/dashboard" className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-black text-[#FFB300] flex items-center justify-center">
              <Flame className="w-5 h-5" strokeWidth={2.5} />
            </div>
            <div>
              <div className="font-bold tracking-tight text-[15px] leading-tight">Energy Project<span className="text-[#FFB300]"> Design</span></div>
              <div className="text-[9px] uppercase tracking-[0.22em] text-gray-500 mt-0.5">v5.2 · Services</div>
            </div>
          </Link>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-5">
          {SECTIONS.map((section) => (
            <div key={section.title}>
              <div className="px-3 mb-2 text-[10px] uppercase tracking-[0.2em] text-gray-400">{section.title}</div>
              <div className="space-y-0.5">
                {section.items.map((n) => {
                  const Icon = n.icon;
                  const active = location.pathname === n.to || (n.to !== '/dashboard' && location.pathname.startsWith(n.to));
                  return (
                    <Link
                      key={n.to}
                      to={n.to}
                      data-testid={n.tid}
                      className={`flex items-center gap-3 px-3 py-2 text-[13px] transition-colors rounded-sm ${
                        active ? 'bg-black text-white' : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5 shrink-0" />
                      <span className="flex-1 truncate">{n.label}</span>
                      {active && <ChevronRight className="w-3 h-3" />}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}

          {(user?.is_developer || user?.is_admin) && (
            <div>
              <div className="px-3 mb-2 text-[10px] uppercase tracking-[0.2em] text-[#FFB300]">// Intern</div>
              <Link to="/admin/config" data-testid="nav-admin-config" className={`flex items-center gap-3 px-3 py-2 text-[13px] transition-colors rounded-sm ${location.pathname.startsWith('/admin/config') ? 'bg-black text-white' : 'text-gray-700 hover:bg-gray-100'}`}>
                <ShieldCheck className="w-3.5 h-3.5 shrink-0" /><span className="flex-1">Admin Config</span>
              </Link>
              <Link to="/developer" data-testid="nav-developer" className={`flex items-center gap-3 px-3 py-2 text-[13px] transition-colors rounded-sm ${location.pathname === '/developer' ? 'bg-black text-white' : 'text-gray-700 hover:bg-gray-100'}`}>
                <Wrench className="w-3.5 h-3.5 shrink-0" /><span className="flex-1">AI Developer Plan</span>
              </Link>
              <Link to="/developer/chat" data-testid="nav-developer-chat" className={`flex items-center gap-3 px-3 py-2 text-[13px] transition-colors rounded-sm ${location.pathname.startsWith('/developer/chat') ? 'bg-black text-white' : 'text-gray-700 hover:bg-gray-100'}`}>
                <Sparkles className="w-3.5 h-3.5 shrink-0" /><span className="flex-1">AI Developer Chat</span>
              </Link>
              <Link to="/developer/github" data-testid="nav-developer-github" className={`flex items-center gap-3 px-3 py-2 text-[13px] transition-colors rounded-sm ${location.pathname.startsWith('/developer/github') ? 'bg-black text-white' : 'text-gray-700 hover:bg-gray-100'}`}>
                <Github className="w-3.5 h-3.5 shrink-0" /><span className="flex-1">Push pe GitHub</span>
              </Link>
              <Link to="/admin/payment-accounts" data-testid="nav-payment-accounts" className={`flex items-center gap-3 px-3 py-2 text-[13px] transition-colors rounded-sm ${location.pathname.startsWith('/admin/payment-accounts') ? 'bg-black text-white' : 'text-gray-700 hover:bg-gray-100'}`}>
                <Banknote className="w-3.5 h-3.5 shrink-0" /><span className="flex-1">Conturi încasări</span>
              </Link>
            </div>
          )}
        </nav>

        <div className="border-t border-gray-200 p-4">
          <div className="flex items-center gap-3 mb-3">
            {user?.picture ? (
              <img src={user.picture} alt="" className="w-9 h-9 rounded-full object-cover" />
            ) : (
              <div className="w-9 h-9 bg-[#FFB300] text-black font-bold flex items-center justify-center rounded-full text-sm">
                {user?.name?.[0]?.toUpperCase() || 'U'}
              </div>
            )}
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium truncate" data-testid="user-name">{user?.name}</div>
              <div className="text-[10px] text-gray-500 uppercase tracking-wider">Plan: {user?.plan}</div>
            </div>
          </div>
          <button
            data-testid="logout-btn"
            onClick={async () => { await logout(); navigate('/'); }}
            className="w-full flex items-center gap-2 text-sm text-gray-700 hover:text-black px-3 py-2 hover:bg-gray-100 rounded-sm"
          >
            <LogOut className="w-4 h-4" /> Deconectare
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-40 bg-white border-b border-gray-200 px-8 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight" data-testid="page-title">{title}</h1>
            {subtitle && <div className="text-xs text-gray-500 mt-0.5">{subtitle}</div>}
          </div>
          <div className="flex items-center gap-3">
            <LicenseTimer />
            <ActiveProjectBar />
            <div className="text-xs text-gray-500 uppercase tracking-[0.2em] hidden xl:block">{user?.email}</div>
          </div>
        </header>
        <main className="flex-1 px-8 py-8 page-enter">{children}</main>
      </div>
    </div>
  );
}
