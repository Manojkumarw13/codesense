import FlowDashboard from '../components/FlowDashboard';

export default function Delivery() {
  return (
    <FlowDashboard
      config={{
        title: 'Delivery',
        blurb: 'Deployment frequency, lead time, cycle time, throughput, WIP.',
        dimensions: ['delivery_flow'],
        bottleneckCategories: ['WORKFLOW', 'DEPLOYMENT'],
        keywords: ['deliver', 'deployment', 'lead time', 'cycle time', 'throughput', 'wip'],
      }}
    />
  );
}
