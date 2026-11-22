/**
 * The seven levels, at their edges.
 *
 * A level decides a task's XP, and older tasks are read back from their XP,
 * so both directions are pinned: each level's own XP reads as that level, one
 * under it reads as the level below, and the stored priority folds the same
 * way the server folds it (backend/tracking/levels.py).
 */
import { describe, expect, it } from 'vitest';
import {
  DEFAULT_LEVEL,
  HARD_FROM,
  LEVELS,
  MAX_TASK_XP,
  MEDIUM_FROM,
  MIN_TASK_XP,
  clampLevel,
  fiveToLevel,
  levelOf,
  levelToPriority,
  levelXp,
  xpToBand,
  xpToDifficulty,
  xpToLevel,
  xpToPriority,
} from './priority';

describe('the seven levels', () => {
  it('are named in order, from Easy to Grueling', () => {
    expect(LEVELS.map((entry) => entry.label)).toEqual([
      'Easy',
      'Slightly Easy',
      'Medium',
      'Medium Hard',
      'Hard',
      'Challenging',
      'Grueling',
    ]);
  });

  it('pay more at every step, from the floor to the ceiling', () => {
    const xps = LEVELS.map((entry) => entry.xp);
    expect([...xps].sort((a, b) => a - b)).toEqual(xps);
    expect(new Set(xps).size).toBe(7);
    expect(xps[0]).toBe(MIN_TASK_XP);
    expect(xps[6]).toBe(MAX_TASK_XP);
  });

  it('start new tasks at Medium', () => {
    expect(DEFAULT_LEVEL).toBe(3);
    expect(levelXp(DEFAULT_LEVEL)).toBe(50);
  });
});

describe('xpToLevel', () => {
  it('reads each level back from its own XP, and one under it as the level below', () => {
    LEVELS.forEach((entry, index) => {
      expect(xpToLevel(entry.xp)).toBe(entry.level);
      if (index > 0) expect(xpToLevel(entry.xp - 1)).toBe(entry.level - 1);
    });
  });

  it('reads anything under the floor as Easy and anything over as Grueling', () => {
    expect(xpToLevel(0)).toBe(1);
    expect(xpToLevel(-40)).toBe(1);
    expect(xpToLevel(9000)).toBe(7);
  });

  it('is what the cards print, one scale', () => {
    expect(xpToBand(90)).toBe('Medium Hard');
    [10, 40, 80, 120, 160, 200, 137].forEach((xp) => {
      expect(xpToDifficulty(xp)).toBe(xpToBand(xp));
    });
  });
});

describe('a task level', () => {
  it('prefers the level it carries, then its old star, then its XP', () => {
    expect(levelOf({ level: 6, difficulty: 1, xp_value: 10 })).toBe(6);
    expect(levelOf({ difficulty: 5, xp_value: 10 })).toBe(7);
    expect(levelOf({ xp_value: 120 })).toBe(5);
    expect(levelOf({})).toBe(1);
  });

  it('maps the old 1-5 star onto levels', () => {
    expect([1, 2, 3, 4, 5].map(fiveToLevel)).toEqual([1, 2, 3, 5, 7]);
    expect(fiveToLevel(0)).toBeNull();
  });

  it('pulls anything out of range to the nearest end', () => {
    expect(clampLevel(0)).toBe(1);
    expect(clampLevel(12)).toBe(7);
    expect(clampLevel('x')).toBe(DEFAULT_LEVEL);
  });
});

describe('the stored priority', () => {
  it('folds the seven onto three at the shared edges', () => {
    expect(LEVELS.map((entry) => levelToPriority(entry.level))).toEqual([
      'low', 'low', 'medium', 'medium', 'high', 'high', 'high',
    ]);
    expect(levelToPriority(MEDIUM_FROM)).toBe('medium');
    expect(levelToPriority(HARD_FROM)).toBe('high');
  });

  it('reads an older task XP the same way', () => {
    expect(xpToPriority(10)).toBe('low');
    expect(xpToPriority(90)).toBe('medium');
    expect(xpToPriority(250)).toBe('high');
  });
});
