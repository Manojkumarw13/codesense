import { Suspense, lazy } from 'react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import Layout from './components/layout/Layout';
import Loading from './components/ui/Loading';
import { ToastProvider } from './components/ui/Toast';
import NotFound from './pages/NotFound';

const Overview = lazy(() => import('./pages/Overview'));
const Health = lazy(() => import('./pages/Health'));
const Delivery = lazy(() => import('./pages/Delivery'));
const Development = lazy(() => import('./pages/Development'));
const CICD = lazy(() => import('./pages/CICD'));
const Reliability = lazy(() => import('./pages/Reliability'));
const Insights = lazy(() => import('./pages/Insights'));
const Anomalies = lazy(() => import('./pages/Anomalies'));
const Bottlenecks = lazy(() => import('./pages/Bottlenecks'));
const Trends = lazy(() => import('./pages/Trends'));
const Integrations = lazy(() => import('./pages/Integrations'));
const Simulator = lazy(() => import('./pages/Simulator'));
const AIAnalysis = lazy(() => import('./pages/AIAnalysis'));
const Settings = lazy(() => import('./pages/Settings'));

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <ToastProvider>
        <Suspense fallback={<Loading label="Loading section…" />}>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<Overview />} />
              <Route path="health" element={<Health />} />
              <Route path="delivery" element={<Delivery />} />
              <Route path="development" element={<Development />} />
              <Route path="cicd" element={<CICD />} />
              <Route path="reliability" element={<Reliability />} />
              <Route path="insights" element={<Insights />} />
              <Route path="anomalies" element={<Anomalies />} />
              <Route path="bottlenecks" element={<Bottlenecks />} />
              <Route path="trends" element={<Trends />} />
              <Route path="integrations" element={<Integrations />} />
              <Route path="simulator" element={<Simulator />} />
              <Route path="ai-analysis" element={<AIAnalysis />} />
              <Route path="settings" element={<Settings />} />
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </Suspense>
        </ToastProvider>
      </AppProvider>
    </BrowserRouter>
  );
}
