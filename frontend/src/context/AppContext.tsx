import { createContext, useContext, useState, type ReactNode } from 'react';
import type { TimeRange } from '../types';

interface AppState {
  teamId: string;
  setTeamId: (t: string) => void;
  timeRange: TimeRange;
  setTimeRange: (t: TimeRange) => void;
  teams: string[];
}

const AppContext = createContext<AppState | null>(null);

// Placeholder teams until Phase 21/22 provides org/team APIs.
const DEFAULT_TEAMS = ['team-alpha', 'team-beta'];

export function AppProvider({ children }: { children: ReactNode }) {
  const [teamId, setTeamId] = useState(DEFAULT_TEAMS[0]);
  const [timeRange, setTimeRange] = useState<TimeRange>('7d');
  return (
    <AppContext.Provider
      value={{ teamId, setTeamId, timeRange, setTimeRange, teams: DEFAULT_TEAMS }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used inside AppProvider');
  return ctx;
}
