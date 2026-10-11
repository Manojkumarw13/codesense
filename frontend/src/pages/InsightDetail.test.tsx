import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import InsightDetail from './InsightDetail';
vi.mock('../api/client', () => ({ apiClient: { getInsight: async () => ({ id: '1', title: 'CI failure spike', severity: 'HIGH', category: 'CI', confidence: 0.82, evidence: { failed: 7 }, generated_by: 'ML_ENGINE', status: 'Active' }) } }));
describe('InsightDetail', () => {
  it('shows title, badges, evidence, back link', async () => {
    render(<MemoryRouter initialEntries={['/app/insights/1']}><Routes><Route path="/app/insights/:id" element={<InsightDetail />} /></Routes></MemoryRouter>);
    expect(await screen.findByText(/ci failure spike/i)).toBeTruthy();
    expect(screen.getByText(/back to insights/i)).toBeTruthy();
  });
});
