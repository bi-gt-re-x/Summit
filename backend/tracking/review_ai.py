"""Review sessions: three ways to go back over your work, written by a model.

The review queue (backend/tracking/review.py) says what's due. This hands it
to a model, with the rest of what's worth going back over, and gets back
three review sessions in the same shape as the Next sessions panel's
(backend/tracking/subject_ai.py `plan`): a title, the material, a timed plan,
checkable success criteria, a difficulty and a length. So they're planned,
booked and ticked off the same way, from the same ledger.

## What goes in the brief

  misses_due       the queue's due items, with each problem's own words and
                   answer, so the session can say exactly what to redo
  coming_back      what's back in the next few days
  rough_sessions   finished tasks rated 1 or 2 out of 5 lately, and why
  spaced_recall    work finished about 1, 3, 7, 14 and 30 days ago: the
                   points where recalling something does the most good
  about_the_reader what they told Summit, as the Next sessions brief has it
  previous_recommendations / recommendation_outcomes
                   earlier review sessions and whether they were done

Misses need the reader to mark them, and most accounts haven't. Rough
sessions and spaced recall come from plain finished tasks, so there's
something to review on any account that does work.

## The three

Different on purpose, so one fits the time there is: a short redo of the
oldest misses, a drill on the pattern behind them with new problems like the
missed ones, and a longer mixed recall session.
"""
import re
from datetime import date, timedelta
from typing import Any, Dict, List

from backend.tracking import figures, planner
from backend.tracking import subject_ai
from backend.tracking.subject_brief import BriefUnavailable, _object
from backend.tracking.plainwords import plain

#: The ledger key review sessions are filed under, like next_sessions.OVERALL.
SUBJECT = 'Review sessions'

#: Days back worth recalling, each with how far either side still counts.
RECALL = ((1, 0), (3, 1), (7, 1), (14, 2), (30, 3))
#: Titles per recall day, newest first.
RECALL_EACH = 4
#: How far back a rough session counts, and how many go up.
ROUGH_DAYS = 30
ROUGH_MOST = 8
#: How many due items go up with their full words.
DUE_MOST = 10

_WEIGHT_WORD = {'warmup': 'Easy', 'core': 'Medium', 'stretch': 'Hard'}


def _day(value):
    try:
        return date.fromisoformat(str(value or '')[:10])
    except ValueError:
        return None


def _int(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _ago(day, today):
    gap = (today - day).days
    return 'today' if gap == 0 else 'yesterday' if gap == 1 else '{} days ago'.format(gap)


def _short(text, cap=220):
    text = re.sub(r'\s+', ' ', str(text or '')).strip()
    return text if len(text) <= cap else text[:cap - 1].rstrip() + '…'


def due_lines(queue, today):
    """The due items, one line each, with the problem's words where there are some."""
    lines = []
    for item in queue.get('due', [])[:DUE_MOST]:
        missed = _day(item.get('missed_on'))
        when = 'Missed {}'.format(_ago(missed, today)) if missed else 'Missed'
        tries = '{} reviews left'.format(item.get('reviews_left')) if item.get('reviews_left') else ''
        where = item.get('where') or ''
        if item.get('kind') in ('problem', 'step') and item.get('tree_title') and item.get('tree_title') != where:
            where = '{}, in {}'.format(where, item['tree_title'])
        if item.get('kind') == 'problem':
            words = ' Problem: "{}" Answer: "{}".'.format(_short(item['prompt']), _short(item['answer'], 120)) \
                if item.get('prompt') and item.get('answer') else ''
            lines.append('- {} problem on "{}" ({}){} {}. {}'.format(
                _WEIGHT_WORD.get(item.get('weight'), 'A'), item.get('title'), where, words, when, tries).strip())
        elif item.get('kind') == 'step':
            lines.append('- Practice logged on "{}" ({}) with misses. {}.'.format(item.get('title'), where, when))
        else:
            lines.append('- Task "{}" ({}): got {} of {} right. {}.'.format(
                item.get('title'), where or 'no subject', item.get('got'), item.get('of'), when))
    return lines


def coming_lines(queue, today, days=4):
    soon = today + timedelta(days=days)
    lines = []
    for item in queue.get('later', []):
        due = _day(item.get('due'))
        if due and due <= soon:
            lines.append('- "{}" ({}) is back {}.'.format(
                item.get('title'), item.get('where') or 'no subject',
                'tomorrow' if (due - today).days == 1 else 'in {} days'.format((due - today).days)))
    return lines[:6]


def rough_lines(tasks, today, name_of, reasons=None):
    """Finished tasks rated 1-2 lately, newest first, with the reason picked."""
    reasons = reasons or {}
    rough = []
    for task in tasks:
        done = _day(task.get('completed_at'))
        rating = _int(task.get('execution'))
        if task.get('status') != 'done' or not done or not 0 < rating <= 2 or (today - done).days > ROUGH_DAYS:
            continue
        rough.append((done, task))
    rough.sort(key=lambda pair: pair[0], reverse=True)
    lines = []
    for done, task in rough[:ROUGH_MOST]:
        why = reasons.get(task.get('reason')) if task.get('reason') else None
        subject = name_of(task['subject']) if task.get('subject') else 'no subject'
        lines.append('- "{}" ({}), rated {} out of 5, {}.{}'.format(
            task.get('title') or 'Untitled', subject, _int(task.get('execution')), _ago(done, today),
            ' Why it went badly: {}.'.format(why) if why else ''))
    return lines


def recall_lines(tasks, today, name_of):
    """Work finished about 1, 3, 7, 14 and 30 days ago, by day."""
    finished = [(_day(task.get('completed_at')), task) for task in tasks
                if task.get('status') == 'done' and _day(task.get('completed_at'))]
    lines = []
    for days, slack in RECALL:
        hits = []
        seen = set()
        for done, task in sorted(finished, key=lambda pair: pair[0], reverse=True):
            if abs((today - done).days - days) > slack:
                continue
            key = re.sub(r'\d+', '#', str(task.get('title') or '').strip().lower())
            if not key or key in seen:
                continue
            seen.add(key)
            rated = _int(task.get('execution'))
            hits.append('"{}" ({}{})'.format(
                task.get('title'), name_of(task['subject']) if task.get('subject') else 'no subject',
                ', rated {} out of 5'.format(rated) if rated else ''))
            if len(hits) >= RECALL_EACH:
                break
        if hits:
            lines.append('- About {} day{} ago: {}.'.format(days, '' if days == 1 else 's', '; '.join(hits)))
    return lines


def state_for(queue, tasks, today, name_of=lambda key: key, reasons=None,
              background=(), previous=(), outcomes=()):
    """Everything the brief is written from."""
    subjects = []
    for item in queue.get('due', []) + queue.get('later', []):
        name = name_of(item['subject']) if item.get('subject') else item.get('tree_title')
        if name and name not in subjects:
            subjects.append(name)
    for task in tasks:
        if task.get('status') == 'done' and task.get('subject'):
            name = name_of(task['subject'])
            if name not in subjects:
                subjects.append(name)
    counts = ['Subjects: {}.'.format(', '.join(subjects[:12])) if subjects else '',
              'Due to redo today: {}.'.format(queue.get('due_count', 0)),
              'Coming back in the next 7 days: {}.'.format(queue.get('this_week', 0)),
              'Cleared in the last 14 days: {}.'.format(queue.get('cleared_lately', 0))]
    return {
        'review_counts': counts,
        'misses_due': due_lines(queue, today),
        'coming_back': coming_lines(queue, today),
        'rough_sessions': rough_lines(tasks, today, name_of, reasons),
        'spaced_recall': recall_lines(tasks, today, name_of),
        'about_the_reader': list(background),
        'previous_recommendations': list(previous),
        'recommendation_outcomes': list(outcomes),
    }


def has_material(state):
    """Whether there's anything to review at all."""
    return any(state.get(key) for key in ('misses_due', 'coming_back', 'rough_sessions', 'spaced_recall'))


SECTIONS = ('review_counts', 'misses_due', 'coming_back', 'rough_sessions', 'spaced_recall',
            'about_the_reader', 'previous_recommendations', 'recommendation_outcomes')


def brief_from(state):
    return '\n\n'.join(part for part in (subject_ai._section(name, state.get(name) or []) for name in SECTIONS)
                       if part)


REVIEW_SYSTEM = """\
You plan three review sessions for one student, for a study-tracking app. \
Review means going back over work they've already done so it sticks: \
redoing what they got wrong, and recalling what they learned days ago before \
it fades. Everything in the brief comes from their own record.

THE THREE OPTIONS
Three different ways to review, so the reader can pick the one that fits the \
time they have. In this order:
  1. A short one, 10 to 15 minutes: redo the misses in <misses_due> that have \
waited longest, exactly as written there. With no misses, a quick recall of \
the oldest work in <spaced_recall>.
  2. One that fixes the pattern, 20 to 30 minutes: find what the misses or the \
<rough_sessions> have in common (the same skill, the same kind of slip) and \
drill it with 3 to 5 NEW problems like the missed ones, with different \
numbers, so it isn't just remembering an answer. WRITE THE PROBLEMS OUT, \
numbered and short, in the `what` of the plan part where they're solved: \
"1) Reduce 20/30. 2) Reduce 14/21. 3) Write 2/5 with a denominator of 35." \
Put the answers in the plan's last part: "Answers: 1) 2/3 2) 2/3 3) 14/35." \
Never write "five new problems" without the problems themselves. When the \
subject isn't one with short problems (an instrument, an essay), write the \
exact exercises instead: which bars, which prompt, what to change.
  3. A mixed recall session, 25 to 45 minutes: pull from several days in \
<spaced_recall> and from the misses, mixed together rather than one block \
each, answered from memory first and checked after.
With no misses at all, build all three from <rough_sessions> and \
<spaced_recall>: retell, re-solve or re-play the work from those days without \
looking, then check.

HOW REVIEW WORKS BEST
  - Recall first, then check. Cover the notes or the worked solution, try, \
then look.
  - For a miss, name exactly what to redo, and ask for one line on why it \
went wrong.
  - In longer sessions, mix topics instead of doing them in blocks.
  - `type` is "review" for all three.
  - `focus` is one of the names on the Subjects line in <review_counts>, \
exactly as written there, so the app can file the session. Use the one most \
of the session is about. A skill's name (like "Fractions") is not a subject.
  - The `reason` quotes the record: how long ago, how many right, the rating. \
Every number you write about the reader must appear in the brief.

"""
#: The step rules, link rules and wording rules are the Next sessions ones,
#: word for word, so the two panels read as one feature.
REVIEW_SYSTEM += subject_ai.STEPS_SYSTEM[subject_ai.STEPS_SYSTEM.index('FREE AND QUICK TO START'):]


def plan(state: Dict[str, Any], model_id: str = '') -> List[Dict[str, Any]]:
    """Three review sessions from `state_for`. Raises BriefUnavailable with
    something the page can say out loud."""
    if not subject_ai.configured():
        raise BriefUnavailable(subject_ai.NO_KEY)
    if not has_material(state):
        raise BriefUnavailable("There's nothing to review yet. Finish some work, or mark what you "
                               "miss in the skill tree, and review sessions show up here.")
    brief = brief_from(state)
    try:
        text = planner.from_provider(
            brief,
            system=REVIEW_SYSTEM,
            schema=subject_ai.STEPS_SCHEMA,
            instruction='Plan three review sessions from the sections below.',
            model_id=model_id or subject_ai.MODEL_DEFAULT,
            max_tokens=subject_ai.STEPS_MAX_TOKENS,
        )
    except planner.PlannerUnavailable as exc:
        raise BriefUnavailable(str(exc)) from exc
    allowed = figures.allowed_from(brief)
    steps = subject_ai._steps(plain(_object(text)), lambda *texts: figures.all_clean(texts, allowed))
    if not steps:
        raise BriefUnavailable('The model sent back no sessions. Try again.')
    # Review, whatever the model called it: the feedback loop counts by type.
    return [dict(step, type='review') for step in steps]
