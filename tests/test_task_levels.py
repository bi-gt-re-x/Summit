"""The seven levels: a task's level sets its XP, and rating it again re-pays.

Easy to Grueling, from shared/rules.json. A level sent with a new task decides
its XP and priority. A rating that changes the level of a finished task pays
the account the difference, once, and late work keeps its cut.
"""
from datetime import datetime, timedelta

from backend.database import connection as db
from backend.tracking import levels
from backend.config.shared import RULES


def account():
    return next(u for u in db.read_table('users') if u['username'] == 'tester')


def task(task_id):
    return db.find_row('tasks', task_id, user_id='tester')


def make(client, **fields):
    reply = client.post('/api/tasks', json={'name': 'Problem set', **fields}).json()
    assert reply['success']
    return reply['task_id']


def test_the_rules_name_seven_levels_in_order():
    names = [entry['label'] for entry in RULES['task_xp']['levels']]
    assert names == ['Easy', 'Slightly Easy', 'Medium', 'Medium Hard', 'Hard', 'Challenging', 'Grueling']
    xps = [entry['xp'] for entry in RULES['task_xp']['levels']]
    assert xps == sorted(xps) and len(set(xps)) == 7
    assert (xps[0], xps[-1]) == (RULES['task_xp']['min'], RULES['task_xp']['max'])


def test_old_scales_fold_onto_levels():
    assert levels.from_xp(90) == 4
    assert levels.from_xp(0) == 1
    assert levels.from_xp(9000) == 7
    assert levels.level_of({'level': 6, 'difficulty': 1, 'xp_value': 10}) == 6
    assert levels.level_of({'difficulty': 5, 'xp_value': 10}) == 7
    assert levels.level_of({'xp_value': 120}) == 5
    assert [levels.priority_for(n) for n in range(1, 8)] == [
        'low', 'low', 'medium', 'medium', 'high', 'high', 'high']


def test_a_level_sets_the_xp_and_priority(client):
    task_id = make(client, level=6, xp_reward=10, priority='low')
    row = task(task_id)
    assert (row['level'], row['xp_value'], row['priority']) == (6, 170, 'high')


def test_an_older_caller_keeps_its_xp_and_gets_a_level(client):
    row = task(make(client, xp_reward=90))
    assert (row['level'], row['xp_value']) == (4, 90)


def test_rating_a_finished_task_harder_pays_the_difference_once(client):
    task_id = make(client, level=3)
    before = account()['xp'] or 0
    client.post('/api/complete_task', json={'task_id': task_id})
    assert account()['xp'] - before == 50

    reply = client.post('/api/rate_task', json={'task_id': task_id, 'level': 7, 'execution': 4}).json()
    assert reply['success']
    assert (reply['level'], reply['xp_value'], reply['xp_change']) == (7, 250, 200)
    assert account()['xp'] - before == 250
    # The quality math still reads a 1-5 difficulty.
    assert task(task_id)['difficulty'] == 5

    again = client.post('/api/rate_task', json={'task_id': task_id, 'level': 7}).json()
    assert again['xp_change'] == 0
    assert account()['xp'] - before == 250

    down = client.post('/api/rate_task', json={'task_id': task_id, 'level': 1}).json()
    assert down['xp_change'] == -240
    assert account()['xp'] - before == 10
    # The extra events count no task.
    events = [e for e in db.rows_for('xp_events', 'tester') if str(e.get('task_id')) == str(task_id)]
    assert sum(int(e.get('tasks_completed') or 0) for e in events) == 1


def test_late_work_keeps_its_cut_when_re_rated(client):
    due = (datetime.now() - timedelta(days=2)).replace(hour=12).isoformat(timespec='seconds')
    task_id = make(client, level=5, due_date=due)
    before = account()['xp'] or 0
    paid = client.post('/api/complete_task', json={'task_id': task_id}).json()['xp_earned']
    assert paid < 120
    reply = client.post('/api/rate_task', json={'task_id': task_id, 'level': 7}).json()
    assert 0 < reply['xp_change'] < 130
    assert account()['xp'] - before < 250


def test_an_open_task_is_re_priced_without_paying(client):
    task_id = make(client, level=2)
    before = account()['xp'] or 0
    reply = client.post('/api/rate_task', json={'task_id': task_id, 'level': 5}).json()
    assert reply['xp_change'] == 0
    assert task(task_id)['xp_value'] == 120
    assert (account()['xp'] or 0) == before


def test_a_level_out_of_range_is_refused(client):
    task_id = make(client, level=3)
    assert not client.post('/api/rate_task', json={'task_id': task_id, 'level': 8}).json()['success']
    assert not client.put('/api/tasks/{}'.format(task_id), json={'level': 0}).json()['success']


def test_editing_the_level_re_prices(client):
    task_id = make(client, level=1)
    client.put('/api/tasks/{}'.format(task_id), json={'level': 4})
    row = task(task_id)
    assert (row['level'], row['xp_value'], row['priority']) == (4, 80, 'medium')
