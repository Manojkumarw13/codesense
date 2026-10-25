import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import Login from './Login';

describe('Login', () => {
  it('renders email/password form and submit button', () => {
    render(<Login />);
    expect(screen.getByLabelText(/email/i)).toBeTruthy();
    expect(screen.getByLabelText(/password/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeTruthy();
  });
});
