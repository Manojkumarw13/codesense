import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render } from '@testing-library/react';
import OfflineNotice from './OfflineNotice';

afterEach(() => cleanup());

describe('OfflineNotice', () => {
  it('renders null in fully-available state (mode="normal", aiAvailable=true)', () => {
    const { container } = render(<OfflineNotice mode="normal" aiAvailable={true} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders the notice in offline state (mode="offline")', () => {
    const { getByRole, getByText } = render(<OfflineNotice mode="offline" aiAvailable={true} />);
    expect(getByRole('status')).toBeTruthy();
    expect(getByText('Working offline')).toBeTruthy();
    expect(getByText(/Core analytics keep working/)).toBeTruthy();
    expect(getByText(/until you're back online/)).toBeTruthy();
  });

  it('renders the notice in AI-unavailable state (mode="normal", aiAvailable=false)', () => {
    const { getByRole, getByText } = render(<OfflineNotice mode="normal" aiAvailable={false} />);
    expect(getByRole('status')).toBeTruthy();
    expect(getByText('AI unavailable')).toBeTruthy();
    expect(getByText(/Cloud AI isn't configured for this team/)).toBeTruthy();
  });

  it('exposes a polite status region (role="status")', () => {
    const { getByRole } = render(<OfflineNotice mode="offline" aiAvailable={false} />);
    expect(getByRole('status')).toBeTruthy();
  });

  it('has no focusable or interactive children', () => {
    render(<OfflineNotice mode="offline" aiAvailable={false} />);
    const focusable = document.querySelectorAll<HTMLElement>(
      'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"]), [contenteditable="true"]',
    );
    expect(focusable).toHaveLength(0);
  });
});
