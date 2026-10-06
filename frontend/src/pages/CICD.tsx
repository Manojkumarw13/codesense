import FlowDashboard from '../components/FlowDashboard';

export default function CICD() {
  return (
    <FlowDashboard
      config={{
        title: 'CI/CD',
        blurb: 'Build success, pipeline duration, deployment success and rollbacks.',
        dimensions: ['cicd_reliability'],
        bottleneckCategories: ['CI', 'DEPLOYMENT'],
        keywords: ['ci', 'build', 'pipeline', 'deploy'],
      }}
    />
  );
}
