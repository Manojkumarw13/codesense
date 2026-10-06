import TeamSelector from './TeamSelector';
import TimeRangeSelector from './TimeRangeSelector';
import UserMenu from './UserMenu';

export default function Header({ onMenu }: { onMenu: () => void }) {
  return (
    <header className="header">
      <button className="menu-btn" onClick={onMenu} aria-label="Toggle navigation">
        ☰
      </button>
      <div className="header-selectors">
        <TeamSelector />
        <TimeRangeSelector />
      </div>
      <UserMenu />
    </header>
  );
}
