import FlowDashboard from '../components/FlowDashboard';

export default function Reliability() {
  return (
    <FlowDashboard
      config={{
        title: 'Reliability',
        blurb: 'Change failure rate, incident frequency, MTTR.',
        dimensions: ['operational_health', 'deployment_health'],
        bottleneckCategories: ['INCIDENT', 'DEPLOYMENT'],
        keywords: ['incident', 'mttr', 'reliab', 'failure', 'rollback'],
      }}
    />
  );
}
