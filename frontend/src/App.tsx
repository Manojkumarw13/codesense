import { Suspense, lazy } from 'react';
import { Route, Routes, useNavigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import PublicLayout from './components/layout/PublicLayout';
import RequireAuth from './components/layout/RequireAuth';
import Loading from './components/ui/Loading';

const DocsEntry = lazy(() => import('./pages/DocsEntry'));
const Landing = lazy(() => import('./pages/Landing'));
const Product = lazy(() => import('./pages/Product'));
const Login = lazy(() => import('./pages/Login'));
const Overview = lazy(() => import('./pages/Overview'));
const Health = lazy(() => import('./pages/Health'));
const Trends = lazy(() => import('./pages/Trends'));
const Delivery = lazy(() => import('./pages/Delivery'));
const Development = lazy(() => import('./pages/Development'));
const CICD = lazy(() => import('./pages/CICD'));
const Reliability = lazy(() => import('./pages/Reliability'));
const Insights = lazy(() => import('./pages/Insights'));
const InsightDetail = lazy(() => import('./pages/InsightDetail'));
const Anomalies = lazy(() => import('./pages/Anomalies'));
const AnomalyDetail = lazy(() => import('./pages/AnomalyDetail'));
const Bottlenecks = lazy(() => import('./pages/Bottlenecks'));
const BottleneckDetail = lazy(() => import('./pages/BottleneckDetail'));
const Simulator = lazy(() => import('./pages/Simulator'));
const AIAnalysis = lazy(() => import('./pages/AIAnalysis'));
const Integrations = lazy(() => import('./pages/Integrations'));
const Settings = lazy(() => import('./pages/Settings'));
const NotFound = lazy(() => import('./pages/NotFound'));

export default function App() {
  const navigate = useNavigate();
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route element={<PublicLayout />}>
          <Route index element={<Landing />} />
          <Route path="product" element={<Product />} />
          <Route path="docs" element={<DocsEntry />} />
          <Route
            path="login"
            element={<Login onLogin={() => navigate('/app', { replace: true })} />}
          />
        </Route>
        <Route path="app" element={<RequireAuth><Layout /></RequireAuth>}>
          <Route index element={<Overview />} />
          <Route path="health" element={<Health />} />
          <Route path="delivery" element={<Delivery />} />
          <Route path="development" element={<Development />} />
          <Route path="cicd" element={<CICD />} />
          <Route path="reliability" element={<Reliability />} />
          <Route path="insights" element={<Insights />} />
          <Route path="insights/:id" element={<InsightDetail />} />
          <Route path="anomalies" element={<Anomalies />} />
          <Route path="anomalies/:id" element={<AnomalyDetail />} />
          <Route path="bottlenecks" element={<Bottlenecks />} />
          <Route path="bottlenecks/:id" element={<BottleneckDetail />} />
          <Route path="trends" element={<Trends />} />
          <Route path="integrations" element={<Integrations />} />
          <Route path="simulator" element={<Simulator />} />
          <Route path="ai-analysis" element={<AIAnalysis />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  );
}
