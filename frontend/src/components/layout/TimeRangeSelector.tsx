import { useApp } from '../../context/AppContext';
import type { TimeRange } from '../../types';

const RANGES: TimeRange[] = ['24h', '7d', '30d', '90d'];

export default function TimeRangeSelector() {
  const { timeRange, setTimeRange } = useApp();
  return (
    <label className="selector">
      Range
      <select value={timeRange} onChange={(e) => setTimeRange(e.target.value as TimeRange)}>
        {RANGES.map((r) => (
          <option key={r} value={r}>
            {r}
          </option>
        ))}
      </select>
    </label>
  );
}
