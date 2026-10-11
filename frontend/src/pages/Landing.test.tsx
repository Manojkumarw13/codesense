import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Landing from './Landing';
describe('Landing', () => {
  it('presents pipeline, privacy boundary, and app CTA', () => {
    render(<MemoryRouter><Landing /></MemoryRouter>);
    expect(screen.getByRole('heading', { name: /codesense/i })).toBeTruthy();
    expect(screen.getByText(/team-level/i)).toBeTruthy();
    expect(screen.getByRole('link', { name: /open dashboard/i })).toBeTruthy();
  });
});
