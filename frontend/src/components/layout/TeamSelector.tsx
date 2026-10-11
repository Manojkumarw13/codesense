import { useApp } from '../../context/AppContext';

const TEAMS = ['team-alpha', 'team-beta', 'team-gamma'];

export default function TeamSelector() {
  const { teamId, setTeamId } = useApp();
  return (
    <label className="header-field">
      <span className="header-field-label">Team</span>
      <select
        aria-label="Team"
        value={teamId}
        onChange={(e) => setTeamId(e.target.value)}
        className="header-select"
      >
        {TEAMS.map((team) => (
          <option key={team} value={team}>
            {team}
          </option>
        ))}
      </select>
    </label>
  );
}
