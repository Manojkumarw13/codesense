import { useApp } from '../../context/AppContext';

export default function TeamSelector() {
  const { teamId, setTeamId, teams } = useApp();
  return (
    <label className="selector">
      Team
      <select value={teamId} onChange={(e) => setTeamId(e.target.value)}>
        {teams.map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>
    </label>
  );
}
