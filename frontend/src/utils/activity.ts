/**
 * How much got done, in the words the app now leads with: tasks finished and
 * time focused. XP is a part of the picture, never the headline
 * (backend/tracking/analytics.py PRODUCTIVITY_WEIGHTS says the same).
 */
import type { Ratings } from '@/types';

/** "6.2 tasks and 48 min a working day", or the XP line for an older reply. */
export function productivityRaw(metric: Ratings['metrics']['productivity']): string {
  if (typeof metric.tasks_per_day !== 'number') {
    return `${Math.round(metric.avg_daily_xp).toLocaleString()} XP a day`;
  }
  const tasks = `${metric.tasks_per_day.toFixed(1)} tasks`;
  const focus = metric.focus_per_day ? ` and ${Math.round(metric.focus_per_day)} min` : '';
  return `${tasks}${focus} a working day`;
}

/**
 * How much a day got done, as one number: tasks finished, plus a task for
 * every half hour focused, plus a quarter of a task for every 50 XP (one
 * Medium task's worth). So two Medium tasks and an hour of focus come to 4.5.
 * XP moves it, but a day can't score high on XP alone. Used wherever days are
 * ranked against each other.
 */
export function dayActivity(day: { tasks_completed?: number; focus_minutes?: number; xp_earned?: number }): number {
  const tasks = Number(day.tasks_completed) || 0;
  const focus = Number(day.focus_minutes) || 0;
  const xp = Number(day.xp_earned) || 0;
  return tasks + focus / 30 + xp / 200;
}
