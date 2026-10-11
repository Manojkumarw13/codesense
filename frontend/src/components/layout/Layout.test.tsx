import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Layout from './Layout';
describe('Layout', () => {
  it('exposes skip link, main landmark, aria-current nav', () => {
    render(<MemoryRouter initialEntries={['/app/health']}><Layout /></MemoryRouter>);
    expect(screen.getByText(/skip to content/i)).toBeTruthy();
    expect(document.querySelector('main#main-content')).toBeTruthy();
    expect(document.querySelector('[aria-current="page"]')).toBeTruthy();
  });
});
