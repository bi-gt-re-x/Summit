/**
 * How hard a task is, and what it pays: the seven levels.
 *
 *   1  Easy             10 XP
 *   2  Slightly Easy    25 XP
 *   3  Medium           50 XP
 *   4  Medium Hard      80 XP
 *   5  Hard            120 XP
 *   6  Challenging     170 XP
 *   7  Grueling        250 XP
 *
 * A task's level is picked from a pill bar (components/LevelPills) when it's
 * made and again when it's rated, and its XP is that level's XP. The values
 * live in shared/rules.json, which the server reads too
 * (backend/tracking/levels.py), so the two sides can't drift.
 *
 * Tasks made before levels existed carry any XP from 10 to 250. They read as
 * the highest level whose XP is at or under theirs, so 90 XP is Medium Hard.
 */
import type { TaskPriority } from '@/types';
import { RULES } from '@/utils/sharedRules';

/** The ends of the XP scale: Easy's XP and Grueling's. */
export const MIN_TASK_XP: number = RULES.task_xp.min;
export const MAX_TASK_XP: number = RULES.task_xp.max;

/** A level's name, as the pills and cards print it ("Easy" … "Grueling"). */
export type XpBand = string;

export interface Level {
  level: number;
  key: string;
  label: string;
  xp: number;
  /** The level on the old 1-5 difficulty star, which the quality math reads. */
  five: number;
}

/** The seven, low to high. */
export const LEVELS: ReadonlyArray<Level> = RULES.task_xp.levels;

/** Where a new task starts when the account hasn't picked a default. */
export const DEFAULT_LEVEL: number = RULES.task_xp.default_level;

/** The levels where the stored priority (low, medium, high) steps up. */
export const MEDIUM_FROM: number = RULES.task_xp.medium_from;
export const HARD_FROM: number = RULES.task_xp.hard_from;

/** Kept for the cards that band by XP: each level, named by the XP it starts at. */
export const XP_BANDS: ReadonlyArray<{ from: number; label: XpBand }> = LEVELS.map((entry) => ({
  from: entry.xp,
  label: entry.label,
}));

/** A level from anything. Out of range is pulled to the nearest end. */
export function clampLevel(level: unknown, fallback: number = DEFAULT_LEVEL): number {
  const n = Math.round(Number(level));
  if (!Number.isFinite(n) || level === null || level === undefined || level === '') return fallback;
  return Math.max(LEVELS[0]!.level, Math.min(LEVELS[LEVELS.length - 1]!.level, n));
}

export function levelEntry(level: unknown): Level {
  const n = clampLevel(level);
  return LEVELS.find((entry) => entry.level === n) ?? LEVELS[0]!;
}

/** What finishing a task at this level pays. */
export function levelXp(level: unknown): number {
  return levelEntry(level).xp;
}

export function levelLabel(level: unknown): string {
  return levelEntry(level).label;
}

/** The highest level whose XP is at or under `xp`. Under the floor is Easy. */
export function xpToLevel(xp: number): number {
  let found = LEVELS[0]!.level;
  for (const entry of LEVELS) {
    if (Number(xp) >= entry.xp) found = entry.level;
  }
  return found;
}

/** A rating on the old 1-5 star, as a level, or null if it isn't one. */
export function fiveToLevel(five: unknown): number | null {
  const key = String(Math.round(Number(five))) as keyof typeof RULES.task_xp.from_five;
  const found = RULES.task_xp.from_five[key];
  return typeof found === 'number' ? found : null;
}

/** A task's level: the one it carries, else its old star rating, else its XP. */
export function levelOf(task: { level?: number | null; difficulty?: number | null; xp_value?: number | null }): number {
  if (task.level !== null && task.level !== undefined) return clampLevel(task.level);
  const rated = fiveToLevel(task.difficulty);
  if (rated !== null) return rated;
  return xpToLevel(Number(task.xp_value) || 0);
}

/** The three-value priority a level is stored as. */
export function levelToPriority(level: number): TaskPriority {
  const n = clampLevel(level);
  if (n >= HARD_FROM) return 'high';
  if (n >= MEDIUM_FROM) return 'medium';
  return 'low';
}

export function xpToPriority(xp: number): TaskPriority {
  return levelToPriority(xpToLevel(xp));
}

/** The level name an XP amount falls in. */
export function xpToBand(xp: number): XpBand {
  return levelLabel(xpToLevel(xp));
}

/** The same seven names, as the cards print them. */
export function xpToDifficulty(xp: number): XpBand {
  return xpToBand(xp);
}

/**
 * A level from a mean on the old 1-5 difficulty scale, which the averages
 * are still worked out on. Read between the `from_five` points, so 3.4 lands
 * between Medium and Hard, and rounded to the nearest level.
 */
export function fiveMeanToLevel(mean: number): number {
  const points = [1, 2, 3, 4, 5].map((five) => fiveToLevel(five) ?? five);
  const at = Math.max(1, Math.min(5, Number(mean) || 1));
  const low = Math.floor(at);
  const high = Math.min(5, low + 1);
  const span = points[high - 1]! - points[low - 1]!;
  return clampLevel(points[low - 1]! + span * (at - low));
}

/** The level name for a mean on the old 1-5 difficulty scale ("Medium Hard"). */
export function difficultyName(mean: number): string {
  return levelLabel(fiveMeanToLevel(mean));
}
