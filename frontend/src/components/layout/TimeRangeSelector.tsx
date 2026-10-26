import { useApp } from '../../context/AppContext';
import type { TimeRange } from '../../types';

const RANGES: TimeRange[] = ['24h', '7d', '30d', '90d'];

export default function TimeRangeSelector() {
  const { timeRange, setTimeRange } = useApp();
  return (
    <div className="header-field" role="group" aria-label="Time range">
      <span className="header-field-label">Range</span>
      <select
        aria-label="Time range"
        value={timeRange}
        onChange={(e) => setTimeRange(e.target.value as TimeRange)}
        className="header-select"
      >
        {RANGES.map((range) => (
          <option key={range} value={range}>
            {range}
          </option>
        ))}
      </select>
    </div>
  );
}
