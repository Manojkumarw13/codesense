import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import Overview from './Overview';
vi.mock('../api/client', () => ({ apiClient: { listHealthScores: async () => [], listInsights: async () => [], listAnomalies: async () => [], listBottlenecks: async () => [] } }));
describe('Overview', () => {
  it('guides fresh DBs to the simulator', async () => {
    render(<Overview />);
    expect(await screen.findByText(/run the simulator/i)).toBeTruthy();
  });
});
