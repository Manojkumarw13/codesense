import FlowDashboard from '../components/FlowDashboard';

export default function Development() {
  return (
    <FlowDashboard
      config={{
        title: 'Development Flow',
        blurb: 'PR cycle time, review turnaround, review backlog, change size.',
        dimensions: ['development_flow', 'review_flow'],
        bottleneckCategories: ['REVIEW', 'WORKFLOW'],
        keywords: ['review', 'pull', 'development', 'change'],
      }}
    />
  );
}
