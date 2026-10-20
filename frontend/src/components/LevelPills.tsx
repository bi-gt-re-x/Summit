/**
 * The seven levels as one row of pills: Easy through Grueling, each with the
 * XP it pays. The one control the app uses to say how hard a task is, so the
 * task dialogs, the rating prompt and Settings all draw this.
 *
 * Radios under the hood, like the rating stars: one choice of seven, arrow
 * keys for free, and a group label a screen reader announces.
 */
import { useId } from 'react';
import { LEVELS } from '@/utils/priority';
import '@/styles/level-pills.css';

export interface LevelPillsProps {
  /** The level chosen, 1-7, or 0 for none yet. */
  value: number;
  onChange: (level: number) => void;
  /** The group's name, read out and shown unless `hideLabel`. */
  label?: string;
  hint?: string;
  hideLabel?: boolean;
  /** Print each level's XP under its name. On by default. */
  showXp?: boolean;
  /** Smaller pills, for tight dialogs. */
  compact?: boolean;
}

export function LevelPills({
  value,
  onChange,
  label = 'How hard is it?',
  hint,
  hideLabel = false,
  showXp = true,
  compact = false,
}: LevelPillsProps) {
  const name = useId();
  return (
    <fieldset className={`lv-pills${compact ? ' is-compact' : ''}`}>
      <legend className={hideLabel ? 'lv-sr' : 'lv-label'}>
        {label}
        {hint && !hideLabel && <span>{hint}</span>}
      </legend>
      <div className="lv-row">
        {LEVELS.map((entry) => {
          const on = value === entry.level;
          return (
            <label key={entry.key} className={`lv-pill${on ? ' is-on' : ''}`} data-level={entry.level}>
              <input
                type="radio"
                name={name}
                value={entry.level}
                checked={on}
                onChange={() => onChange(entry.level)}
              />
              <span className="lv-name">{entry.label}</span>
              {showXp && <span className="lv-xp">{entry.xp} XP</span>}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
