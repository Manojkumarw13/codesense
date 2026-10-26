import TeamSelector from './TeamSelector';
import TimeRangeSelector from './TimeRangeSelector';
import UserMenu from './UserMenu';

interface HeaderProps {
  onMenuClick: () => void;
}

export default function Header({ onMenuClick }: HeaderProps) {
  return (
    <header className="app-header">
      <button
        type="button"
        className="menu-button"
        onClick={onMenuClick}
        aria-label="Open navigation"
      >
        ☰
      </button>
      <span className="header-brand">CodeSense</span>
      <div className="header-controls">
        <TeamSelector />
        <TimeRangeSelector />
        <UserMenu />
      </div>
    </header>
  );
}
