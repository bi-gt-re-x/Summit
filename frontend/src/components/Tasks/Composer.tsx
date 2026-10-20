/**
 * Adding a task, as a row at the top of the list rather than a dialog.
 *
 * A dialog to add a task is a dialog to be dismissed: this page exists to have
 * a lot of tasks on it, and the reader adding one is usually adding three. The
 * form stays open, keeps the priority and subject they last chose, clears the
 * name, and puts the cursor back — so the second and third cost a sentence
 * each rather than a round trip through a modal.
 *
 * Only the name is required. Everything else has a default the backend would
 * have applied anyway, and asking for five fields to write down "email Mr Chen"
 * is how a task list stops being used.
 */
import { useEffect, useRef, useState } from 'react';
import { SubjectPicker } from '@/components';
import { GoalField, MATCH_BY_NAME } from './GoalField';
import type { Subject } from '@/services/subjects';
import type { NewTask } from '@/services/tasks';
import type { Goal } from '@/types';
import { LevelPills } from '@/components/LevelPills';
import { clampLevel, levelToPriority, levelXp } from '@/utils/priority';

export interface ComposerProps {
  subjects: Subject[];
  /** The account's goals, for the optional "counts toward" field. */
  goals: Goal[];
  busy: boolean;
  onAdd: (task: NewTask) => void;
  /** How hard a new task starts out, 1-7, before the reader picks. From Settings. */
  defaultLevel: number;
}

export function Composer({ subjects, goals, busy, onAdd, defaultLevel }: ComposerProps) {
  const [name, setName] = useState('');
  const [level, setLevel] = useState(clampLevel(defaultLevel));
  const [due, setDue] = useState('');
  const [subject, setSubject] = useState<string | null>(null);
  const [goalId, setGoalId] = useState(MATCH_BY_NAME);
  const [open, setOpen] = useState(false);
  const field = useRef<HTMLInputElement>(null);

  /* The preferences are read near the root and land a moment after the page
     does, so the form is often built before the account's default level is
     known. Following it until the reader picks one is what makes the
     preference true here rather than true-if-you-reload — and stopping there
     is what stops it from undoing a pick they just made. */
  const touched = useRef(false);
  useEffect(() => {
    if (!touched.current) setLevel(clampLevel(defaultLevel));
  }, [defaultLevel]);

  const chooseLevel = (value: number) => {
    touched.current = true;
    setLevel(value);
  };

  const submit = (event: React.FormEvent) => {
    event.preventDefault();
    const title = name.trim();
    if (!title || busy) return;
    onAdd({
      name: title,
      // The level decides both; the server works them out the same way.
      level,
      priority: levelToPriority(level),
      xp_reward: levelXp(level),
      due_date: due || null,
      subject,
      // Absent rather than empty when the reader left it alone: the backend
      // reads "no goal_id" as "let the matcher decide", and an empty string
      // would be a link to a goal that does not exist.
      ...(goalId ? { goal_id: goalId } : {}),
    });
    // The name is the only field cleared: the rest are almost always the same
    // for the next one, and re-choosing them every time is the friction this
    // form exists to remove.
    setName('');
    field.current?.focus();
  };

  return (
    <form className="tk-composer" onSubmit={submit}>
      <div className="tk-composer-main">
        <input
          ref={field}
          className="tk-composer-name"
          value={name}
          placeholder="Add a task…"
          aria-label="Task name"
          onChange={(event) => setName(event.target.value)}
          onFocus={() => setOpen(true)}
        />
        <button type="submit" className="tk-btn is-primary" disabled={busy || !name.trim()}>
          Add
        </button>
        <button
          type="button"
          className="tk-btn is-quiet"
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
        >
          {open ? 'Fewer options' : 'More options'}
        </button>
      </div>

      {open && (
        <div className="tk-composer-more">
          {/* One question for how hard it is, and the XP follows from it. The
              stored priority is folded from the level on the way out. */}
          <div className="tk-field tk-field-level">
            <LevelPills value={level} onChange={chooseLevel} label="How hard is it?" compact />
          </div>

          <label className="tk-field">
            <span>Due</span>
            <input
              className="tk-input"
              type="date"
              value={due}
              onChange={(event) => setDue(event.target.value)}
            />
          </label>

          <div className="tk-field tk-field-subject">
            <SubjectPicker
              subjects={subjects}
              value={subject}
              onChange={setSubject}
              label="Subject"
              id="tk-composer"
            />
          </div>

          {/* Kept, like the subject and the difficulty, when the name clears:
              somebody adding three tasks for one goal chooses it once. */}
          <GoalField goals={goals} value={goalId} onChange={setGoalId} id="tk-composer" />
        </div>
      )}
    </form>
  );
}
