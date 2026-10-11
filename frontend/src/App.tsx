import { Outlet, Route, Routes } from 'react-router-dom';

/** Task 2 replaces this with the real app shell. */
function Layout() {
  return <Outlet />;
}

/** Task 3 replaces this with the real public header/footer. */
function PublicLayout() {
  return <Outlet />;
}

function stub(text: string) {
  return function Stub() {
    return <main>{text}</main>;
  };
}

// Placeholder pages — later tasks replace each with a real page module.
const Landing = stub('Landing');
const Product = stub('Product');
const DocsEntry = stub('DocsEntry');
const Overview = stub('Overview');
const Health = stub('Health');
const Delivery = stub('Delivery');
const Development = stub('Development');
const CICD = stub('CICD');
const Reliability = stub('Reliability');
const Insights = stub('Insights');
const InsightDetail = stub('InsightDetail');
const Anomalies = stub('Anomalies');
const AnomalyDetail = stub('AnomalyDetail');
const Bottlenecks = stub('Bottlenecks');
const BottleneckDetail = stub('BottleneckDetail');
const Trends = stub('Trends');
const Integrations = stub('Integrations');
const Simulator = stub('Simulator');
const AIAnalysis = stub('AIAnalysis');
const Settings = stub('Settings');
const NotFound = stub('NotFound');

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
