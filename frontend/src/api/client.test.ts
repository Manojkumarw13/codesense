import { describe, expect, it, vi } from 'vitest';
import { apiClient } from './client';
describe('apiClient', () => {
  it('unwraps {items} and never sends placeholder teams as UUID filters', async () => {
    const fetchMock = vi.fn(async () => ({ ok: true, json: async () => ({ total: 1, skip: 0, limit: 100, items: [{ id: 'x' }] }) }));
    vi.stubGlobal('fetch', fetchMock);
    const rows = await apiClient.listAnomalies({ team_id: 'team-alpha' });
    expect(rows).toEqual([{ id: 'x' }]);
    expect(String(fetchMock.mock.calls)).not.toContain('team-alpha');
  });
});
