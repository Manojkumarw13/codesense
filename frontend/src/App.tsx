import { Route, Routes } from 'react-router-dom';
import Layout from './components/layout/Layout';
import PublicLayout from './components/layout/PublicLayout';
import DocsEntry from './pages/DocsEntry';
import Landing from './pages/Landing';
import Product from './pages/Product';
import Overview from './pages/Overview';
import Health from './pages/Health';
import Trends from './pages/Trends';
import Delivery from './pages/Delivery';
import Development from './pages/Development';
import CICD from './pages/CICD';
import Reliability from './pages/Reliability';
import Insights from './pages/Insights';
import InsightDetail from './pages/InsightDetail';
import Anomalies from './pages/Anomalies';
import AnomalyDetail from './pages/AnomalyDetail';
import Bottlenecks from './pages/Bottlenecks';
import BottleneckDetail from './pages/BottleneckDetail';
import Simulator from './pages/Simulator';
import AIAnalysis from './pages/AIAnalysis';
import Integrations from './pages/Integrations';
import Settings from './pages/Settings';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<Landing />} />
        <Route path="product" element={<Product />} />
        <Route path="docs" element={<DocsEntry />} />
      </Route>
      <Route path="app" element={<Layout />}>
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
  );
}
