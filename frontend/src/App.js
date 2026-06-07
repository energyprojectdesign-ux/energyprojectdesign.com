import './App.css';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Toaster } from 'sonner';

import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import Developer from './pages/Developer';
import DeveloperChat from './pages/DeveloperChat';
import DeveloperGithub from './pages/DeveloperGithub';
import PaymentAccounts from './pages/PaymentAccounts';
import Forum from './pages/Forum';
import CompanyProfile from './pages/CompanyProfile';
import AuditLogs from './pages/AuditLogs';
import ProjectData from './pages/ProjectData';
import TechnicalData from './pages/TechnicalData';
import SmartCalc from './pages/SmartCalc';
import PhotovoltaicCalc from './pages/PhotovoltaicCalc';
import Verification from './pages/Verification';
import AIAssistantPage from './pages/AIAssistantPage';
import AuditPage from './pages/AuditPage';
import InternalCertifications from './pages/InternalCertifications';
import EmailComposer from './pages/EmailComposer';
import Templates from './pages/Templates';
import TemplateEditor from './pages/TemplateEditor';
import Stamps from './pages/Stamps';
import Certificates from './pages/Certificates';
import Documents from './pages/Documents';
import Pricing from './pages/Pricing';
import Settings from './pages/Settings';
import AuthCallback from './pages/AuthCallback';
import Termeni from './pages/Termeni';
import Confidentialitate from './pages/Confidentialitate';
import Gdpr from './pages/Gdpr';
import IndustriesHub from './pages/IndustriesHub';
import IndustryDetail from './pages/IndustryDetail';
import FeaturesHub from './pages/FeaturesHub';
import FeatureDetail from './pages/FeatureDetail';
import DeveloperProgres from './pages/DeveloperProgres';
import AdminConfig from './pages/AdminConfig';
import AIAgents from './pages/AIAgents';
import SEAPAlerts from './pages/SEAPAlerts';
import CRMSubscribers from './pages/CRMSubscribers';
import ANAFInvoicing from './pages/ANAFInvoicing';
import PublicStatus from './pages/PublicStatus';
import EnergyAdvisor from './pages/EnergyAdvisor';
import Jobs from './pages/Jobs';
import Contracts from './pages/Contracts';
import Personas from './pages/Personas';
import GasNaturalProject from './pages/GasNaturalProject';
import GasRecipients from './pages/GasRecipients';
import Subscribers from './pages/Subscribers';
import VerifyGasProject from './pages/VerifyGasProject';
import Clients from './pages/Clients';
import Companies from './pages/Companies';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="h-screen flex items-center justify-center text-sm text-gray-500">Se încarcă…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRouter() {
  const location = useLocation();
  if (location.hash?.includes('session_id=')) return <AuthCallback />;

  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route path="/termeni" element={<Termeni />} />
      <Route path="/confidentialitate" element={<Confidentialitate />} />
      <Route path="/gdpr" element={<Gdpr />} />
      <Route path="/pentru/:role" element={<Personas />} />
      <Route path="/gaze-naturale" element={<ProtectedRoute><GasNaturalProject /></ProtectedRoute>} />
      <Route path="/gaze-naturale/recipients" element={<ProtectedRoute><GasRecipients /></ProtectedRoute>} />
      <Route path="/gaze-naturale/:pid" element={<ProtectedRoute><GasNaturalProject /></ProtectedRoute>} />
      <Route path="/subscribers" element={<ProtectedRoute><Subscribers /></ProtectedRoute>} />
      <Route path="/clients" element={<ProtectedRoute><Clients /></ProtectedRoute>} />
      <Route path="/companies" element={<ProtectedRoute><Companies /></ProtectedRoute>} />
      <Route path="/verify/gas-project/:pid" element={<VerifyGasProject />} />

      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/proiecte" element={<ProtectedRoute><Projects /></ProtectedRoute>} />
      <Route path="/developer" element={<ProtectedRoute><Developer /></ProtectedRoute>} />
      <Route path="/developer/chat" element={<ProtectedRoute><DeveloperChat /></ProtectedRoute>} />
      <Route path="/developer/github" element={<ProtectedRoute><DeveloperGithub /></ProtectedRoute>} />
      <Route path="/admin/payment-accounts" element={<ProtectedRoute><PaymentAccounts /></ProtectedRoute>} />
      <Route path="/forum" element={<ProtectedRoute><Forum /></ProtectedRoute>} />
      <Route path="/forum/:threadId" element={<ProtectedRoute><Forum /></ProtectedRoute>} />
      <Route path="/company" element={<ProtectedRoute><CompanyProfile /></ProtectedRoute>} />
      <Route path="/logs" element={<ProtectedRoute><AuditLogs /></ProtectedRoute>} />
      <Route path="/proiect" element={<ProtectedRoute><ProjectData /></ProtectedRoute>} />
      <Route path="/tehnice" element={<ProtectedRoute><TechnicalData /></ProtectedRoute>} />
      <Route path="/calcul" element={<ProtectedRoute><SmartCalc /></ProtectedRoute>} />
      <Route path="/fotovoltaic" element={<ProtectedRoute><PhotovoltaicCalc /></ProtectedRoute>} />
      <Route path="/verifica" element={<ProtectedRoute><Verification /></ProtectedRoute>} />
      <Route path="/ai" element={<ProtectedRoute><AIAssistantPage /></ProtectedRoute>} />
      <Route path="/audit" element={<ProtectedRoute><AuditPage /></ProtectedRoute>} />
      <Route path="/certificari" element={<ProtectedRoute><InternalCertifications /></ProtectedRoute>} />
      <Route path="/email" element={<ProtectedRoute><EmailComposer /></ProtectedRoute>} />
      <Route path="/templates" element={<ProtectedRoute><Templates /></ProtectedRoute>} />
      <Route path="/templates/:id" element={<ProtectedRoute><TemplateEditor /></ProtectedRoute>} />
      <Route path="/stamps" element={<ProtectedRoute><Stamps /></ProtectedRoute>} />
      <Route path="/certificate" element={<ProtectedRoute><Certificates /></ProtectedRoute>} />
      <Route path="/documents" element={<ProtectedRoute><Documents /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />

      {/* Industries Hub + per-industry skeleton */}
      <Route path="/industrii" element={<ProtectedRoute><IndustriesHub /></ProtectedRoute>} />
      <Route path="/industrii/:industryId" element={<ProtectedRoute><IndustryDetail /></ProtectedRoute>} />

      {/* Features Hub (Feat-uri vision) + skeleton sub-pages */}
      <Route path="/feat-uri" element={<ProtectedRoute><FeaturesHub /></ProtectedRoute>} />
      <Route path="/feat-uri/:featureId" element={<ProtectedRoute><FeatureDetail /></ProtectedRoute>} />

      {/* Progress page (developer-only) */}
      <Route path="/developer/progres" element={<ProtectedRoute><DeveloperProgres /></ProtectedRoute>} />
      <Route path="/admin/config" element={<ProtectedRoute><AdminConfig /></ProtectedRoute>} />
      <Route path="/ai-agents" element={<ProtectedRoute><AIAgents /></ProtectedRoute>} />
      <Route path="/seap-alerts" element={<ProtectedRoute><SEAPAlerts /></ProtectedRoute>} />
      <Route path="/crm-abonati" element={<ProtectedRoute><CRMSubscribers /></ProtectedRoute>} />
      <Route path="/anaf-efactura" element={<ProtectedRoute><ANAFInvoicing /></ProtectedRoute>} />
      <Route path="/status" element={<PublicStatus />} />
      <Route path="/consultant-ai" element={<ProtectedRoute><EnergyAdvisor /></ProtectedRoute>} />
      <Route path="/jobs" element={<Jobs />} />
      <Route path="/contracts" element={<ProtectedRoute><Contracts /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRouter />
        <Toaster position="top-right" richColors />
      </BrowserRouter>
    </AuthProvider>
  );
}
