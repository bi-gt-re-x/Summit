/**
 * The rating prompt's queue entry, and what a saved rating writes back onto
 * the task on screen. Shared by every page that raises the prompt, so a
 * re-rated level shows its new XP the same way everywhere.
 */
import type { RatingAnswers, TaskRating } from '@/services/tasks';
import type { Task } from '@/types';
import { announceStatsChanged } from '@/utils/statsBus';
import { levelOf } from '@/utils/priority';

export interface RatingTarget {
  id: string;
  name: string;
  /** The task's level, which the prompt's pill bar starts on. */
  level: number;
}

export function ratingTarget(task: Task | undefined, id: string, fallback = 'that task'): RatingTarget {
  return {
    id: String(id),
    name: task?.title || fallback,
    level: task ? levelOf(task) : 0,
  };
}

/** The task with the answers and the server's new level and XP on it. */
export function withRating(entry: Task, values: RatingAnswers, result: Partial<TaskRating>): Task {
  const next: Task = { ...entry, ...values };
  if (result.level !== undefined && result.level !== null) next.level = result.level;
  if (typeof result.xp_value === 'number') next.xp_value = result.xp_value;
  if (typeof result.difficulty === 'number') next.difficulty = result.difficulty;
  return next;
}

/** Tell the rail its XP moved, when a re-rated level paid a difference. */
export function announceXpChange(result: Partial<TaskRating>): void {
  if (result.xp_change) announceStatsChanged();
}
