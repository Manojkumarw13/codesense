import { createContext, useContext, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import type { TimeRange } from '../types';

interface AppContextValue {
  teamId: string;
  timeRange: TimeRange;
  setTeamId: (teamId: string) => void;
  setTimeRange: (range: TimeRange) => void;
}

const AppContext = createContext<AppContextValue>({
  teamId: 'team-alpha',
  timeRange: '30d',
  setTeamId: () => {},
  setTimeRange: () => {},
});

export function AppProvider({ children }: { children: ReactNode }) {
  const [teamId, setTeamId] = useState('team-alpha');
  const [timeRange, setTimeRange] = useState<TimeRange>('30d');
  const value = useMemo(
    () => ({ teamId, timeRange, setTeamId, setTimeRange }),
    [teamId, timeRange],
  );
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  return useContext(AppContext);
}
