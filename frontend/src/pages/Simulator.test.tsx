import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import Simulator from './Simulator';
vi.mock('../api/client', () => ({ simulatorClient: { getSimulatorStatus: async () => { throw new Error('down'); } } }));
describe('Simulator', () => {
  it('explains the fix when unreachable', async () => {
    render(<Simulator />);
    expect(await screen.findByText(/simulator unavailable/i)).toBeTruthy();
  });
});
