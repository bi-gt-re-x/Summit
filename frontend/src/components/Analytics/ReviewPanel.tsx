/**
 * Review sessions, on the Recommendations tab: three ways to go back over your
 * work, and the misses that are due to redo.
 *
 * The top half is the Next sessions panel's twin (components/NextSessions):
 * a model reads what you missed, what went badly and what you did 1 to 30
 * days ago (backend/tracking/review_ai.py) and writes three review sessions,
 * a short redo, a drill on the pattern with new problems, and a mixed recall
 * session. Each is drawn, planned and ticked off with the same card and the
 * same buttons as a next session.
 *
 * Under it, the misses that are due (backend/tracking/review.py), each redone
 * right here (components/Review/ReviewList). They come back after 1 day, then
 * 3, 7 and 14, until they stick.
 */
import { useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { PanelNote } from './charts';
import { ReviewList } from '@/components/Review/ReviewList';
import { NextSteps, BATCH } from '@/components/Subject/NextSteps';
import { AuthContext, UserDataContext } from '@/context/contexts';
import { planSession, takeRecommendation, type NextStep, type SuggestedSession } from '@/services/analytics';
import {
  reviewQueue,
  reviewSessions,
  suggestReviewSessions,
  type ReviewItem,
  type ReviewQueue,
} from '@/services/review';
import { announceStatsChanged } from '@/utils/statsBus';
import { withPlannedTask } from '@/utils/plannedTask';
import '@/styles/subject-state.css';
import '@/styles/next-sessions.css';
import '@/styles/review.css';

/** "Thursday" inside a week, "Oct 24" past it. */
export function dayWord(iso: string, today: Date = new Date()): string {
  const [year = 1970, month = 1, day = 1] = iso.split('-').map(Number);
  const when = new Date(year, month - 1, day);
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const gap = Math.round((when.getTime() - start.getTime()) / 86400000);
  if (gap <= 0) return 'today';
  if (gap === 1) return 'tomorrow';
  if (gap < 7) return when.toLocaleDateString('en-US', { weekday: 'long' });
  return when.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function ComingBack({ items }: { items: ReviewItem[] }) {
  if (items.length === 0) return null;
  const shown = items.slice(0, 8);
  return (
    <details className="rq-later">
      <summary>Coming back ({items.length})</summary>
      <ul>
        {shown.map((item) => (
          <li key={item.key}>
            <span className="rq-later-title">{item.kind === 'set' ? `"${item.title}"` : item.title}</span>
            <span className="rq-later-when">{item.due ? dayWord(item.due) : ''}</span>
          </li>
        ))}
      </ul>
      {items.length > shown.length && <p className="rq-note">And {items.length - shown.length} more.</p>}
    </details>
  );
}

/** The due misses, redone in place. Read once; answers count down here. */
function DueMisses({ queue, onAnswered }: { queue: ReviewQueue; onAnswered: (item: ReviewItem) => void }) {
  /* Keys answered on this visit. */
  const [answered, setAnswered] = useState<ReadonlySet<string>>(new Set());
  const { due, later, due_count: dueCount, sitting, minutes, cleared_lately: cleared, next_due: nextDue } = queue;
  if (dueCount === 0 && later.length === 0 && cleared === 0) {
    /* Empty because nothing's been marked yet, which is most accounts. Say
       what fills it rather than leaving a gap under the sessions. */
    return (
      <div className="rv-misses is-empty">
        <div className="rv-misses-head">
          <h3>Redo what you missed</h3>
          <p className="rv-misses-note">Nothing to redo yet.</p>
        </div>
        <p className="rq-note">
          Misses land here when you add a score to a finished task and get some wrong, or mark a skill tree
          problem Missed it. Each one comes back until it sticks.
        </p>
      </div>
    );
  }
  const left = Math.max(0, dueCount - answered.size);
  const sittingLeft = due.slice(0, sitting).filter((item) => !answered.has(item.key));
  const minutesLeft = sittingLeft.reduce((sum, item) => sum + item.minutes, 0);

  const note = [
    dueCount > 0 && left === 0
      ? 'All done for today. Nice work.'
      : left > 0
        ? `${left} due · about ${minutesLeft || minutes} min`
        : nextDue
          ? `All caught up. The next one's back ${dayWord(nextDue)}.`
          : 'All caught up.',
    cleared > 0 ? `${cleared} cleared lately` : null,
  ]
    .filter(Boolean)
    .join(' · ');

  return (
    <div className="rv-misses">
      <div className="rv-misses-head">
        <h3>Redo what you missed</h3>
        <p className="rv-misses-note">{note}</p>
      </div>
      {dueCount > 0 && (
        <>
          <ReviewList
            items={due.slice(0, sitting)}
            onAnswered={(item) => {
              setAnswered((was) => new Set(was).add(item.key));
              onAnswered(item);
            }}
          />
          {dueCount > sitting && (
            <p className="rq-note">{dueCount - sitting} more after these. Start with these. They've waited longest.</p>
          )}
        </>
      )}
      <ComingBack items={later} />
    </div>
  );
}

export function ReviewPanel({ onChanged }: { onChanged?: () => void }) {
  /* Read without `useAuth`, as the Next sessions panel does: a page drawn
     with nobody signed in has no panel. */
  const username = useContext(AuthContext)?.username ?? null;
  const shared = useContext(UserDataContext);
  const [queue, setQueue] = useState<ReviewQueue | null>(null);
  const [steps, setSteps] = useState<SuggestedSession[]>([]);
  const [available, setAvailable] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [asking, setAsking] = useState(false);
  /** The step being planned or ticked off. */
  const [busy, setBusy] = useState('');
  const [all, setAll] = useState(false);
  const working = asking || all || busy !== '';
  const [error, setError] = useState('');

  useEffect(() => {
    if (!username) return undefined;
    let live = true;
    setLoading(true);
    void Promise.all([reviewSessions(), reviewQueue()]).then(([sessions, due]) => {
      if (!live) return;
      setLoading(false);
      if (sessions.success) {
        setSteps(sessions.steps);
        setAvailable(sessions.available);
      } else {
        setError(sessions.message || "Couldn't load your review sessions.");
      }
      if (due.success) setQueue(due);
    });
    return () => {
      live = false;
    };
  }, [username]);

  /* A link to /recommendations#review lands here once it has drawn: the
     router doesn't scroll to a hash, and the panel isn't there on the first
     paint anyway. */
  useEffect(() => {
    if (!loading && window.location.hash === '#review') {
      document.getElementById('review')?.scrollIntoView({ block: 'start' });
    }
  }, [loading]);

  const status = useMemo(
    () => new Map(steps.map((step) => [step.id, { state: step.state, task: step.task }])),
    [steps],
  );
  const open = steps.filter((step) => step.state === 'open');

  const suggest = async () => {
    setAsking(true);
    setError('');
    const result = await suggestReviewSessions();
    setAsking(false);
    if (!result.success) {
      setError(result.message || "Couldn't suggest review sessions. Try again.");
      return;
    }
    setSteps(result.steps);
  };

  /** Book one. Returns whether it was booked, for "Plan all". */
  const plan = useCallback(
    async (step: NextStep): Promise<boolean> => {
      const made = await planSession(step.id, '');
      if (!made.success) {
        setError(made.message || "Couldn't plan that session. Try again.");
        return false;
      }
      setSteps((was) => was.map((row) => (row.id === step.id ? { ...row, state: 'planned', task: made.task } : row)));
      shared?.mutate((current) => withPlannedTask(current, made.task, step.title, made.task.subject ?? ''));
      return true;
    },
    [shared],
  );

  const planOne = async (step: NextStep) => {
    if (working) return;
    setBusy(step.id);
    setError('');
    if (await plan(step)) announceStatsChanged();
    setBusy('');
  };

  /* One after another: each booking takes the next free slot, and the server
     only sees a slot as taken once the one before it is written. */
  const planAll = async () => {
    setAll(true);
    setError('');
    let booked = 0;
    for (const step of open) {
      setBusy(step.id);
      if (!(await plan(step))) break;
      booked += 1;
    }
    if (booked) announceStatsChanged();
    setBusy('');
    setAll(false);
  };

  const didIt = async (step: NextStep) => {
    if (working) return;
    setBusy(step.id);
    const result = await takeRecommendation(step.id);
    setBusy('');
    if (result.success) {
      setSteps((was) => was.map((row) => (row.id === step.id ? { ...row, state: 'done', task: null } : row)));
    }
  };

  if (!username) return null;

  return (
    <section className="ax-section" id="review">
      <div className="ns-panel ns-on-analytics rv-panel" role="region" aria-label="Review sessions">
        <header className="ns-head">
          <div className="ns-title">
            <h2>Review sessions</h2>
            <p>
              Three ways to go back over your work: what you missed, what went badly, and what you did 1 to 30
              days ago. Each one says what to redo, how hard it is and how long it takes. Add one to your
              calendar, or all three.
            </p>
          </div>
        </header>

        {available === false ? (
          <p className="ns-note">
            Suggestions need an AI key. Add a free GROQ_API_KEY or an ANTHROPIC_API_KEY to .env and restart the server.
          </p>
        ) : (
          <div className="ns-actions">
            <button type="button" className="ns-btn is-primary" onClick={() => void suggest()} disabled={working || loading}>
              {asking
                ? 'Loading…'
                : steps.length
                  ? `Suggest ${BATCH} different ones`
                  : `Suggest ${BATCH} review sessions`}
            </button>
            {open.length > 0 && (
              <button type="button" className="ns-btn" onClick={() => void planAll()} disabled={working}>
                {all ? 'Adding…' : open.length === BATCH ? `Plan all ${BATCH}` : `Plan the other ${open.length}`}
              </button>
            )}
          </div>
        )}

        {error && (
          <p className="ns-error" role="alert">
            {error}
          </p>
        )}

        {loading ? (
          <p className="ns-note">Loading review sessions…</p>
        ) : steps.length > 0 ? (
          <NextSteps
            steps={steps}
            status={status}
            busy={busy}
            onPlan={(step) => void planOne(step)}
            onDidIt={(step) => void didIt(step)}
            firstOpen={false}
          />
        ) : (
          available !== false && (
            <p className="ns-note">
              Nothing suggested yet. Press Suggest {BATCH} review sessions and you'll get three: a quick redo, a
              drill on what keeps going wrong, and a mixed recall session.
            </p>
          )
        )}

        {queue && <DueMisses queue={queue} onAnswered={() => onChanged?.()} />}

        <PanelNote label="How review works">
          <ul className="ax-tips">
            <li><b>Back on a schedule:</b> Anything you miss comes back the next day, then 3, 7 and 14 days after each time you get it right.</li>
            <li><b>Miss it again:</b> It starts over from the next day.</li>
            <li><b>Done for good:</b> Get it right four times in a row and it's cleared.</li>
            <li><b>Recall first:</b> The sessions ask you to try from memory, then check. That's what makes it stick.</li>
            <li><b>Where it comes from:</b> Skill tree problems you mark Missed it, tasks you score below full, sessions you rate 1 or 2, and work from 1 to 30 days ago.</li>
          </ul>
        </PanelNote>
      </div>
    </section>
  );
}
