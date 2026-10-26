import Select from './ui/Select';

export const SEVERITY_OPTIONS = [
  { value: 'ALL', label: 'All severities' },
  { value: 'LOW', label: 'Low' },
  { value: 'MEDIUM', label: 'Medium' },
  { value: 'HIGH', label: 'High' },
  { value: 'CRITICAL', label: 'Critical' },
];

interface FilterBarProps {
  severity: string;
  onSeverityChange: (value: string) => void;
  category: string;
  onCategoryChange: (value: string) => void;
  categories?: string[];
}

/**
 * Shared severity/category filters (Task 5 → reused by Task 6).
 * Selects keep a 44px minimum target for touch use.
 */
export default function FilterBar({
  severity,
  onSeverityChange,
  category,
  onCategoryChange,
  categories = [],
}: FilterBarProps) {
  const categoryOptions = [
    { value: 'ALL', label: 'All categories' },
    ...categories.map((name) => ({ value: name, label: name })),
  ];

  return (
    <div className="filter-bar" role="group" aria-label="Signal filters">
      <Select
        label="Severity"
        value={severity}
        onChange={(event) => onSeverityChange(event.target.value)}
        options={SEVERITY_OPTIONS}
        style={{ minHeight: 44 }}
      />
      <Select
        label="Category"
        value={category}
        onChange={(event) => onCategoryChange(event.target.value)}
        options={categoryOptions}
        style={{ minHeight: 44 }}
      />
    </div>
  );
}
