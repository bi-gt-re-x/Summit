"""Review sessions: three ways to go back over your work, written by a model.

The brief is backend/tracking/review_ai.py; the endpoints are
/api/review_sessions in backend/api/subject_ai.py.
"""
import json
from datetime import date, datetime, timedelta

from backend.database import connection as db
from backend.tracking import review_ai, subject_ai
from backend.tracking.subject_brief import BriefUnavailable

TODAY = date(2026, 10, 20)
NAMES = {'mathematics': 'Mathematics', 'music': 'Music'}


def done(title, subject, days_ago, **extra):
    return {'title': title, 'subject': subject, 'status': 'done',
            'completed_at': (TODAY - timedelta(days=days_ago)).isoformat() + 'T10:00:00', **extra}


QUEUE = {
    'due_count': 2, 'this_week': 1, 'cleared_lately': 0,
    'due': [
        {'kind': 'problem', 'title': 'Equivalent Fractions', 'where': 'Fractions', 'weight': 'core',
         'prompt': 'Reduce 18/24 to lowest terms.', 'answer': '3/4', 'missed_on': '2026-10-18',
         'reviews_left': 4},
        {'kind': 'set', 'title': 'Quadratics #1-10', 'where': 'Mathematics', 'got': 6, 'of': 10,
         'missed_on': '2026-10-19', 'reviews_left': 4},
    ],
    'later': [{'kind': 'problem', 'title': 'Collect Like Terms', 'where': 'Algebra', 'due': '2026-10-21'}],
}


# ---- The brief -------------------------------------------------------------------
def test_due_misses_go_up_with_their_own_words():
    lines = review_ai.due_lines(QUEUE, TODAY)
    assert lines[0] == ('- Medium problem on "Equivalent Fractions" (Fractions) Problem: "Reduce 18/24 '
                        'to lowest terms." Answer: "3/4". Missed 2 days ago. 4 reviews left')
    assert lines[1] == '- Task "Quadratics #1-10" (Mathematics): got 6 of 10 right. Missed yesterday.'


def test_a_skill_problem_names_its_tree_and_the_brief_lists_subjects():
    queue = {'due': [dict(QUEUE['due'][0], tree_title='Mathematics')], 'later': []}
    assert '(Fractions, in Mathematics)' in review_ai.due_lines(queue, TODAY)[0]
    state = review_ai.state_for(queue, [done('Scales', 'music', 3)], TODAY, NAMES.get)
    assert state['review_counts'][0] == 'Subjects: Mathematics, Music.'


def test_whats_back_soon_is_named():
    assert review_ai.coming_lines(QUEUE, TODAY) == ['- "Collect Like Terms" (Algebra) is back tomorrow.']


def test_rough_sessions_say_why():
    tasks = [done('Proof set 3', 'mathematics', 4, execution=2, reason='unclear'),
             done('Scales', 'music', 2, execution=4), done('Old one', 'music', 60, execution=1)]
    lines = review_ai.rough_lines(tasks, TODAY, NAMES.get, {'unclear': "didn't know where to start"})
    assert lines == ['- "Proof set 3" (Mathematics), rated 2 out of 5, 4 days ago. '
                     "Why it went badly: didn't know where to start."]


def test_spaced_recall_picks_the_days_worth_recalling():
    tasks = [done('Stewart Ch. 7 #1-8', 'mathematics', 7, execution=4, level=5),
             done('Stewart Ch. 7 #9-16', 'mathematics', 7),
             done('Scales', 'music', 3, level=2), done('Bach', 'music', 5), done('Proofs', 'mathematics', 30, level=3)]
    lines = review_ai.recall_lines(tasks, TODAY, NAMES.get)
    # Day 5 is no recall point; two ranges of one chapter are one line.
    assert lines == [
        '- About 3 days ago: "Scales" (Music, Slightly Easy).',
        '- About 7 days ago: "Stewart Ch. 7 #1-8" (Mathematics, Hard, rated 4 out of 5).',
        '- About 30 days ago: "Proofs" (Mathematics, Medium).',
    ]


def test_hard_work_is_worth_reviewing_even_unrated():
    tasks = [done('Olympiad set 4', 'mathematics', 2, level=7),
             done('Olympiad set 5', 'mathematics', 1, level=6),
             done('Scales', 'music', 1, level=2),
             done('Proof set 3', 'mathematics', 4, level=5, execution=2),
             done('Old grind', 'mathematics', 40, level=7)]
    lines = review_ai.hard_lines(tasks, TODAY, NAMES.get)
    # Newest first, one line per name family; the rough one is left to its own section.
    assert lines == ['- "Olympiad set 5" (Mathematics), Challenging, yesterday.']
    state = review_ai.state_for({'due': [], 'later': []}, tasks, TODAY, NAMES.get)
    assert '<hard_work>' in review_ai.brief_from(state)


def test_with_no_misses_there_is_still_something_to_review():
    state = review_ai.state_for({'due': [], 'later': []}, [done('Scales', 'music', 3)], TODAY, NAMES.get)
    assert review_ai.has_material(state)
    assert '<spaced_recall>' in review_ai.brief_from(state)
    assert '<misses_due>' not in review_ai.brief_from(state)


def test_nothing_done_means_nothing_to_review():
    state = review_ai.state_for({'due': [], 'later': []}, [], TODAY, NAMES.get)
    assert not review_ai.has_material(state)


# ---- The model call ----------------------------------------------------------------
ANSWER = {'next_steps': [{
    'title': 'Redo Equivalent Fractions misses', 'problems': 'Reduce 20/30, 14/21 and 36/48.',
    'pace': '2 min each', 'resources': [], 'focus': 'Mathematics', 'type': 'targeted_practice',
    'difficulty': 2, 'duration_minutes': 15, 'reason': 'You missed it 2 days ago and got 6 of 10.',
    'equipment': '', 'plan': [{'label': 'Redo', 'minutes': 15, 'what': 'Cover the answer, then check.'}],
    'success': ['Redo all three.'],
}]}


def test_plan_asks_for_review_and_files_everything_as_review(monkeypatch):
    seen = {}

    def answer(brief, **kwargs):
        seen.update(kwargs, brief=brief)
        return json.dumps(ANSWER)

    monkeypatch.setattr(subject_ai, 'configured', lambda: True)
    monkeypatch.setattr(review_ai.planner, 'from_provider', answer)
    state = review_ai.state_for(QUEUE, [], TODAY, NAMES.get)
    [step] = review_ai.plan(state)
    assert step['type'] == 'review'
    # New problems are instructions, not claims, so their numbers stand.
    assert step['problems'] == 'Reduce 20/30, 14/21 and 36/48.'
    assert step['reason'] == 'You missed it 2 days ago and got 6 of 10.'
    assert 'THE THREE OPTIONS' in seen['system'] and 'FREE AND QUICK TO START' in seen['system']
    assert 'review sessions' in seen['instruction']
    assert 'Reduce 18/24 to lowest terms.' in seen['brief']


def test_a_reason_quoting_a_number_nobody_counted_is_dropped(monkeypatch):
    bad = json.loads(json.dumps(ANSWER))
    bad['next_steps'][0]['reason'] = 'You got 17 of 40 wrong.'
    monkeypatch.setattr(subject_ai, 'configured', lambda: True)
    monkeypatch.setattr(review_ai.planner, 'from_provider', lambda brief, **kwargs: json.dumps(bad))
    [step] = review_ai.plan(review_ai.state_for(QUEUE, [], TODAY, NAMES.get))
    assert step['reason'] == ''


def test_nothing_to_review_says_so(monkeypatch):
    monkeypatch.setattr(subject_ai, 'configured', lambda: True)
    try:
        review_ai.plan(review_ai.state_for({'due': [], 'later': []}, [], TODAY, NAMES.get))
    except BriefUnavailable as exc:
        assert "nothing to review yet" in str(exc)
    else:
        raise AssertionError('expected BriefUnavailable')


# ---- The endpoints -------------------------------------------------------------------
STEPS = [
    {'title': 'Redo your two misses', 'focus': 'Mathematics', 'type': 'review', 'difficulty': 2,
     'minutes': 15, 'reason': 'two missed', 'drills': [], 'plan': [], 'success': []},
    {'title': 'Fraction reductions drill', 'focus': 'Mathematics', 'type': 'review', 'difficulty': 3,
     'minutes': 25, 'reason': 'same slip twice', 'drills': [], 'plan': [], 'success': []},
    {'title': 'Mixed recall: last two weeks', 'focus': 'Music', 'type': 'review', 'difficulty': 3,
     'minutes': 40, 'reason': 'from 7 days ago', 'drills': [], 'pace': '2 min each',
     'plan': [{'label': 'Recall', 'minutes': 30, 'what': '1) Play bars 1-8 from memory.'},
              {'label': 'Check', 'minutes': 10, 'what': 'Answers: compare with the score.'}],
     'success': []},
]


def _seed():
    day = (date.today() - timedelta(days=7)).isoformat()
    db.insert_row('tasks', {'id': 'rs1', 'user_id': 'tester', 'title': 'Scales', 'subject': 'music',
                            'status': 'done', 'priority': 'low', 'xp_value': 10,
                            'completed_at': day + 'T10:00:00', 'created_at': day + 'T09:00:00'})


def _stub(monkeypatch, record=None):
    def plan(state, model_id=''):
        if record is not None:
            record.update(state=state)
        return [dict(step) for step in STEPS]

    monkeypatch.setattr(subject_ai, 'configured', lambda: True)
    monkeypatch.setattr(review_ai, 'plan', plan)


def test_none_suggested_yet(client):
    body = client.get('/api/review_sessions').json()
    assert body['success'] and body['steps'] == []


def test_three_are_suggested_kept_and_come_back(client, monkeypatch):
    _seed()
    seen = {}
    _stub(monkeypatch, seen)
    body = client.post('/api/review_sessions', json={}).json()
    assert body['success'], body
    assert [step['title'] for step in body['steps']] == [step['title'] for step in STEPS]
    assert all(step['state'] == 'open' for step in body['steps'])
    assert any('Scales' in line for line in seen['state']['spaced_recall'])
    again = client.get('/api/review_sessions').json()
    assert [step['title'] for step in again['steps']] == [step['title'] for step in STEPS]
    # Filed apart from next sessions.
    assert client.get('/api/next_sessions').json()['steps'] == []


def test_a_review_session_is_booked_under_its_subject(client, monkeypatch):
    _seed()
    _stub(monkeypatch)
    first = client.post('/api/review_sessions', json={}).json()['steps'][2]
    made = client.post('/api/subject_recommendation/plan', json={'id': first['id']}).json()
    assert made['success'], made
    task = db.find_row('tasks', made['task']['id'], user_id='tester')
    assert task['title'] == 'Mixed recall: last two weeks'
    assert task['subject'] == 'music'
    # The plan is the work, so it goes on the task.
    assert task['description'] == ('2 min each\nRecall (30 min): 1) Play bars 1-8 from memory.\n'
                                   'Check (10 min): Answers: compare with the score.')
    assert client.get('/api/review_sessions').json()['steps'][2]['state'] == 'planned'
