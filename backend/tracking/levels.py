"""How hard a task is, and what it pays: the seven levels.

Easy, Slightly Easy, Medium, Medium Hard, Hard, Challenging, Grueling. A task's
level is picked from a pill bar when it's made and again when it's rated, and
its XP is that level's XP. The values live in shared/rules.json (`task_xp`),
which the browser reads too (frontend/src/utils/priority.ts).

Three older scales still meet this one, and each is folded here and only here:

  - **XP.** Tasks made before levels existed carry any XP from 10 to 250. They
    read as the highest level whose XP is at or under theirs.
  - **The 1-5 difficulty star.** Ratings written before the pill bar sit in
    `tasks.difficulty`. `from_five` maps them onto a level, and `five_of` maps
    a level back, because the quality math (difficulty x execution, 1-25) still
    runs on five.
  - **Priority.** `tasks.priority` is low, medium or high, with a CHECK behind
    it. `priority_for` folds the seven onto those three.
"""
from backend.config.shared import RULES

_RULES = RULES['task_xp']

#: The seven, low to high, each {level, key, label, xp, five}.
LEVELS = tuple(_RULES['levels'])
BY_LEVEL = {entry['level']: entry for entry in LEVELS}
LOWEST = LEVELS[0]['level']
HIGHEST = LEVELS[-1]['level']
DEFAULT = int(_RULES['default_level'])
MEDIUM_FROM = int(_RULES['medium_from'])
HARD_FROM = int(_RULES['hard_from'])
FROM_FIVE = {int(five): int(level) for five, level in _RULES['from_five'].items()}


def valid(level) -> bool:
    """True for a whole number that names one of the seven."""
    return isinstance(level, int) and not isinstance(level, bool) and level in BY_LEVEL


def clamp(level, fallback=DEFAULT) -> int:
    """A level, from anything. Out of range is pulled to the nearest end."""
    try:
        number = int(level)
    except (TypeError, ValueError):
        return fallback
    return max(LOWEST, min(HIGHEST, number))


def xp_for(level) -> int:
    """What finishing a task at this level pays."""
    return int(BY_LEVEL[clamp(level)]['xp'])


def label(level) -> str:
    return BY_LEVEL[clamp(level)]['label']


def five_of(level) -> int:
    """The level on the old 1-5 difficulty scale the quality math uses."""
    return int(BY_LEVEL[clamp(level)]['five'])


def from_five(five):
    """A rating on the old 1-5 scale as a level, or None if it isn't one."""
    try:
        return FROM_FIVE.get(int(five))
    except (TypeError, ValueError):
        return None


def from_xp(xp) -> int:
    """The highest level whose XP is at or under `xp`. Under the floor is Easy."""
    try:
        worth = float(xp or 0)
    except (TypeError, ValueError):
        worth = 0
    found = LOWEST
    for entry in LEVELS:
        if worth >= entry['xp']:
            found = entry['level']
    return found


def level_of(task) -> int:
    """A task's level: the one it carries, else its old star rating, else its XP."""
    stored = task.get('level')
    if stored is not None:
        return clamp(stored)
    rated = from_five(task.get('difficulty'))
    if rated is not None:
        return rated
    return from_xp(task.get('xp_value'))


def priority_for(level) -> str:
    """The three-value priority a level is stored as."""
    level = clamp(level)
    if level >= HARD_FROM:
        return 'high'
    if level >= MEDIUM_FROM:
        return 'medium'
    return 'low'


def from_five_mean(mean) -> int:
    """A level from a mean on the old 1-5 scale, read between the `from_five`
    points and rounded. The averages are still worked out on five; this is
    how they're named. Same rule as `fiveMeanToLevel` in utils/priority.ts."""
    try:
        at = max(1.0, min(5.0, float(mean)))
    except (TypeError, ValueError):
        return DEFAULT
    points = [FROM_FIVE.get(five, five) for five in range(1, 6)]
    low = int(at)
    high = min(5, low + 1)
    value = points[low - 1] + (points[high - 1] - points[low - 1]) * (at - low)
    # Half up, like Math.round, so both sides name 3.5 the same.
    return clamp(int(value + 0.5))


def name_for_five_mean(mean) -> str:
    return label(from_five_mean(mean))
