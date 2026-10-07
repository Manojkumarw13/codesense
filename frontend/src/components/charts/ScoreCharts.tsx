import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { dimensionLabel } from '../../types';

const ACCENT = '#533afd';
const GRID = '#e3e8ee';
const TICK = '#64748d';

const TOOLTIP_STYLE = {
  backgroundColor: '#0d253d',
  border: 'none',
  borderRadius: 8,
  color: '#e2e8f0',
  fontSize: 12,
};

function useAnim() {
  const reduced = useReducedMotion();
  // Emil: chart redraws on every nav — keep it fast; off entirely when reduced.
  return { isAnimationActive: !reduced, animationDuration: 400 };
}

export interface TrendPoint {
  label: string;
  score: number;
}

export function ScoreArea({ data, height = 220 }: { data: TrendPoint[]; height?: number }) {
  const anim = useAnim();
  if (data.length === 0) return <p className="muted">No score history yet.</p>;
  return (
    <div className="rechart" style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
          <defs>
            <linearGradient id="scoreFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={ACCENT} stopOpacity={0.28} />
              <stop offset="100%" stopColor={ACCENT} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: TICK, fontSize: 11 }} tickLine={false} axisLine={{ stroke: GRID }} minTickGap={28} />
          <YAxis domain={[0, 100]} tick={{ fill: TICK, fontSize: 11 }} tickLine={false} axisLine={false} width={36} />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Area type="monotone" dataKey="score" name="Score" stroke={ACCENT} strokeWidth={2.5} fill="url(#scoreFill)" dot={false} activeDot={{ r: 4 }} {...anim} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MiniSpark({ data, height = 64 }: { data: number[]; height?: number }) {
  const anim = useAnim();
  if (data.length === 0) return null;
  const points = data.map((score, i) => ({ i, score }));
  return (
    <div className="rechart" style={{ width: '100%', height }}>
      <ResponsiveContainer>
        <AreaChart data={points} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
          <Area type="monotone" dataKey="score" stroke={ACCENT} strokeWidth={2} fill={ACCENT} fillOpacity={0.12} dot={false} isAnimationActive={anim.isAnimationActive} animationDuration={300} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

const DIM_COLORS = ['#533afd', '#665efd', '#0ea5e9', '#ea2261', '#f59e0b', '#10b981'];

export function DimensionBarsChart({ dims }: { dims: Record<string, number> }) {
  const anim = useAnim();
  const entries = Object.entries(dims);
  if (entries.length === 0) return <p className="muted">No dimension data yet.</p>;
  const data = entries.map(([key, value], i) => ({
    name: dimensionLabel(key),
    value,
    fill: DIM_COLORS[i % DIM_COLORS.length],
  }));
  return (
    <div className="rechart" style={{ width: '100%', height: 24 + entries.length * 34 }}>
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 12, bottom: 0, left: 8 }}>
          <CartesianGrid stroke={GRID} strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" domain={[0, 100]} tick={{ fill: TICK, fontSize: 11 }} tickLine={false} axisLine={{ stroke: GRID }} />
          <YAxis type="category" dataKey="name" tick={{ fill: TICK, fontSize: 11 }} tickLine={false} axisLine={false} width={128} />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Bar dataKey="value" name="Score" radius={[4, 4, 4, 4]} barSize={14} {...anim}>
            {data.map((d) => (
              <Cell key={d.name} fill={d.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export interface MultiPoint {
  label: string;
  [dimension: string]: string | number;
}

export function MultiTrend({ data, series }: { data: MultiPoint[]; series: string[] }) {
  const anim = useAnim();
  if (data.length === 0) return <p className="muted">No trend data yet.</p>;
  return (
    <div className="rechart" style={{ width: '100%', height: 300 }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -12 }}>
          <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="label" tick={{ fill: TICK, fontSize: 11 }} tickLine={false} axisLine={{ stroke: GRID }} minTickGap={32} />
          <YAxis domain={[0, 100]} tick={{ fill: TICK, fontSize: 11 }} tickLine={false} axisLine={false} width={36} />
          <Tooltip contentStyle={TOOLTIP_STYLE} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {series.map((s, i) => (
            <Line key={s} type="monotone" dataKey={s} name={dimensionLabel(s)} stroke={DIM_COLORS[i % DIM_COLORS.length]} strokeWidth={2} dot={false} activeDot={{ r: 3 }} {...anim} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
