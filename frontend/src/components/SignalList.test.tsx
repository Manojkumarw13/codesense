import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import SignalList from './SignalList';
describe('SignalList', () => {
  it('renders Open links and empty hint', () => {
    const { rerender } = render(<MemoryRouter><SignalList items={[{ id: '1', title: 'Review backlog rising', severity: 'HIGH' }]} basePath="/app/insights" /></MemoryRouter>);
    expect(screen.getByText(/review backlog rising/i)).toBeTruthy();
    rerender(<MemoryRouter><SignalList items={[]} basePath="/app/insights" emptyHint="run the simulator" /></MemoryRouter>);
    expect(screen.getByText(/run the simulator/i)).toBeTruthy();
  });
});
