# Usefulness audit: Analytics, session planning, notifications

Written 2026-10-15. Read-only: no code was changed.

## How this was checked

- Alpha's record (the user's account, 665K XP, 18,459 finished tasks), on a scratch copy of `data/summit.db` taken Oct 9, served by an alt API on :5051 and Vite on :5091.
- Pages read in full: Recommendations, Overview, Insights, Subjects, Growth (with the Skill Growth section and the report card), the Mathematics subject page, Goals, the Dashboard, and the analytics notifications the sweep wrote.
- Code read: `backend/tracking/next_actions.py`, `next_sessions.py`, `session_plan.py`, `planner.py`, `notify.py`.
- Every item gets one question: what would a student do differently tomorrow because of it? If nothing, or if the advice would be the same for anyone, it's noise.

Two caveats. The copy stops on Oct 8, so the last week reads as a gap. That's useful, because it shows what a student sees after a week off. Also, most of Alpha's record looks seeded (2,042 open tasks dated into 2027, routines like "Ice bath" rated Brutal/Excellent), so some odd patterns come from the seed. The verdicts are about what the pages do with the data, not about the data.

## The four suspicions, tested

| Suspicion | Verdict | What the pages showed |
|---|---|---|
| It describes the past instead of saying what to do next | **True** | 94 items across the surfaces below. About 10 tell the student to do something specific. Most of the rest are totals, grades and charts of the past. |
| The inputs are thin | **True, and worse than thought** | The "what went wrong" reason field is filled on 0 of 18,459 finished tasks. `skill_attempts` (right/wrong answers) has 0 rows. Completion reads 99 to 100% in every subject because tasks get logged once they're done. Difficulty and execution are self-rated, so "quality" is the student grading themselves. |
| Too many overlapping surfaces | **True, and they contradict each other** | See the list below the table. The same fact comes out different on different tabs. |
| Plans read as generic because of Groq | **Mostly false** | The subject page's AI steps are specific ("Stewart Calculus Ch. 7 #1-6, 12 min each", "Putnam 2025 A1-A5, 15 min each"). The generic output comes from the Goals planner, and that's because its brief only has the goal's title, why, target and date. It never sees the student's record. The model isn't the bottleneck. The brief is. |

### Contradictions a student would notice

- "Only 0% of your finished tasks are rated" (Recommendations) vs "Rated 14,718 of 16,763 finished (88%)" (Overview).
- "You do 100% less on weekends" (Recommendations) vs "Weekends and weekdays are within 7% of each other" (Insights).
- Growth score 8.1 (Overview) vs 8.7 (Growth report card). Productivity is S 10/10 on one and B 80 on the other.
- Tasks finished: 17,070 (Overview tile), 16,763 (Quality), 18,451 (Pace), 18,459 (Growth).
- 3+ day breaks: 1 (Recommendations card), 3 (Insights). Two-plus-day breaks: 2.
- "Turning up is not your problem" (coach's read) sits under the #1 change, "Fill the three-day gaps".
- "Running: 270 weeks in a row" while the same card says 0 this week, last done a week ago.
- Focus goal: "60 min a day" (Insights) vs "Daily Goal: 4.0 hrs" (Dashboard).
- Every subject has two levels with two scales: Math is "88.84 Overlord" and "75 Advanced".

## 1. Every item, with a verdict

Keep = useful as is. Sharpen = the right idea, but it needs better inputs or a narrower claim. Cut = no decision changes because of it.

### Recommendations tab

| Item | Verdict | Reason |
|---|---|---|
| Headline "5 changes are worth making here" | Cut | Just repeats the list below it. |
| "Reading this through: Throughput" goal lens | Cut | Says itself that it only reorders panels. |
| Total XP earned 665,450, down 79% | Cut | An XP total changes nothing. The 79% is one quiet week. |
| What to do next (time budget plan) | Sharpen | The right shape, but at 45 min it dropped all 43 overdue tasks and the USACO goal (47 days left, and the rule only looks 45 days out). Then it suggested "Practice Planning: redo Evening review, slower". |
| Streak row: "Close Evening review" | Cut | "Keep your streak" is the same for everyone. |
| How this is chosen | Keep | Honest and short. |
| Mixed signals: long gaps, Sunday, first day back | Cut | Generic consistency advice. "First day back averaged 0 XP" counts a gap that hasn't ended yet. |
| Change 1: Fill the three-day gaps, +29K XP a year | Cut | Takes one break and turns it into a yearly XP number. XP isn't something a student is trying to learn. |
| Change 2: Claim one weekend day, "100% less on weekends" | Cut | Comes from a two-week window and contradicts Insights. |
| Change 3: No Lectures for 1133 days | Sharpen | The card says "none in the last three weeks" about a subject left three years ago. Just offer to archive it. |
| Change 4: Rate what you finish, "Only 0% rated" | Cut | Wrong. 88% are rated. |
| Change 5: Restart Planning | Cut | Names 12 subjects joined by "and". Nobody can act on it. |
| Five years, both ways (projection chart, table, milestones, where the extra comes from) | Cut | A five-year XP forecast doesn't help with this week. |
| Next sessions (3 AI sessions, all subjects) | Sharpen | Two of the three were a coffee with a friend and a long run. Planning across "all subjects" mixes life with study. Limit it to subjects that have a dated goal. |
| Coach's read: Record | Cut | Contradicts change 1. |
| Coach's read: Workload ("cut the next list to three, hardest first") | Keep | Specific and true: 9.9 tasks a working day, and 50 on today's list. |
| Coach's read: Subjects ("nothing owns your time") | Sharpen | Should name the nearest deadline and how much of the month went to it. |

### Overview tab and report card

| Item | Verdict | Reason |
|---|---|---|
| Grade B, growth score 8.1/10, five letter grades | Cut | Disagrees with the Growth tab's 8.7. A grade changes no plan. |
| "Down from 8.3, 6 days ago" | Cut | Noise. |
| "10 of your 13 goals are behind" | Sharpen | Name the one with the nearest date and what it needs this week. |
| Tiles: 352 XP/day, 98% consistency, 13.5/25 quality, 17,070 tasks, 6,311.9h | Cut | All-time totals with nothing to compare against. The task count disagrees with three other numbers. |
| Productivity, consistency and quality over time chart | Cut | A weekly XP line going back five years. |
| What your work says so far (hard tasks, due dates, pace) | Cut | Descriptive only. |
| What your work says so far: goals, "8 of 36 steps ticked" | Sharpen | Useful if it names the next unticked step on the nearest goal. |
| Against your baseline (days a week, sitting length) | Sharpen | A target the student set is good. But hitting 278% means the target is stale, so prompt them to raise it. |
| Quality panel (13.5/25, hard done well 77%, "right difficulty") | Cut | Self-ratings scored against themselves. Contradicts the subject page's "easy work is holding you back". |
| Difficulty against execution grid | Cut | Same self-ratings drawn a second way. |
| Consistency heatmap | Cut | Also on Growth. |

### Insights tab

| Item | Verdict | Reason |
|---|---|---|
| Headline "8 habits found" | Cut | Counts, no action. |
| Getting stronger: difficulty 3.6 to 4.0 | Cut | Based on 34 self-rated tasks. |
| Emerging problem: long gaps | Cut | Repeats Recommendations word for word. |
| Getting stronger: "Running, 270 weeks in a row" | Cut | False this week. |
| Emerging problem: 43 tasks past their date | Keep | Actionable. Better if it said they're a week of routine tasks that piled up since Oct 8 and offered to clear them. |
| Emerging problem: XP per focus hour 190 to 160 | Cut | XP is self-set, so the ratio means nothing. |
| Habit cards (8 cards, all "Strong 100%") | Cut | Morning routines, every one marked strong while untouched for a week. |
| Patterns ("Morning meditation happens in the morning, 99%") | Cut | Says what the name already says. |
| Best and worst rated work | Cut | "Ice bath, Brutal, Excellent, 25/25". |
| Why XP fell 79%: days worked 27 to 10 | Sharpen | The only honest explanation on the page. Belongs in the weekly notification as one line. |
| "Doing less on weekends, 7% vs 28%" | Cut | Contradicts the weekday chart on the same tab. |
| "Days less consistent, variation 0.60 to 0.99" | Cut | A statistic, not advice. |
| "You work best in 1-202 minute sessions" | Cut | A broken range, and "XP per minute" just rewards short tasks. |
| "Most done between 3 PM and 11 PM" | Sharpen | Only says when boxes get ticked. Cross it with ratings ("hard tasks go better before 6 PM") and it could steer a schedule. |
| "Breaks are costing you momentum" | Cut | Third count of breaks, different again. |
| What moves with what ("Tasks finished, then XP earned, r = 0.86") | Cut | XP comes from tasks, so of course they correlate. |
| Which habits are stable / behavioral history | Cut | All 8 "holding". Weekly rates nobody acts on. |
| Clock by hour, XP by weekday | Cut | Repeats the 3 to 11 PM line. |
| Focus 100/S, "60 min against a 60 min day" | Cut | Contradicts the Dashboard's 4 hour goal. |
| Follow-through 74% and planned vs completed, 8 weeks | Sharpen | Planned vs done is the one execution number that matters. Turn it into "you plan 50, you finish about 10". |
| Stability 84, focus depth, recovery rate, full/solid/light/rest days | Cut | Four more scores with no action. |

### Subjects tab

| Item | Verdict | Reason |
|---|---|---|
| Account level 115, XP levels per subject with titles (Overlord, Legend) | Cut from analytics | It's the game layer. Belongs on the profile or Achievements. |
| "Moving fastest: Planning, 0%" | Cut | Nothing moved. |
| Subject cards: % change, "8d ago", "1133d quiet" | Sharpen | "Days since" is the useful part for review timing. The percentages are noise. |
| Mathematics: "coming back less often, every 6 days, was every day" | Keep | Concrete, and it would change a week's plan. |
| Math: down 45% on last month, XP an hour here vs elsewhere | Cut | XP arithmetic. |
| Math growth chart, balance radar, mastery track ("Level 91 in 410 days") | Cut | Game progress, no decision. |
| Moving and waiting (+0%, -100%) | Cut | Says nothing moved. |
| Goal limiter ("CS is about 100% of the work that went badly") | Cut | A one-subject goal always gets 100%. |
| Subject growth XP donut | Cut | Where XP went, years ago. |
| How far into each tree ("168,607 / 34,900 XP, 100%") | Cut | Broken: the numerator is bigger than the total. |
| What each subject opens (links to trees) | Keep | Navigation. |
| Skill level by subject (Meditation 77, Advanced) | Sharpen | A second level system next to the XP level. Pick one. |

### Growth tab (Skill Growth and report card)

| Item | Verdict | Reason |
|---|---|---|
| Skill Growth cards: overall +8%, 25 of 32 improved, closest to mastery, new bands, biggest growth | Cut | Long-run summaries made from self-ratings. |
| Skill Growth card: Needs attention ("Programming slipped 75 to 64, nothing for 39 days") | Keep | Names a subject and why. Would change a week. |
| Growth over time chart | Cut | Five-year lines. |
| Subject-by-subject cards (completion, execution, on time, challenge, tree, goals) | Sharpen | Completion is always about 100% and should go. Keep on-time for subjects with due dates and the goal "Behind" line. |
| Skills by level (from right/wrong answers) | Keep | Empty for Alpha, but it's the right measure. This is the data the rest of the app lacks. |
| Time, and what it bought (6,312h for +215 points) | Cut | "0.3 points per 10 hours" isn't a lever. |
| Report card: overall B 8.7, five grades | Cut | A second grade that disagrees with Overview. |
| The shape of a skill (six-part breakdown) | Cut | Weights nobody tunes. |
| Growth timeline, then and now, biggest improvement, needs attention, what changed underneath | Cut | Mostly says "nothing to compare against". |
| Growth by period ("last 7 days -100%") | Cut | Punishes a week off with no advice. |
| Milestones ("Reached A", "Reached B") | Cut | The dates are out of order and nothing follows from them. |
| When you work, consistency heatmap | Cut | Repeats of Insights and Overview. |
| The work, year by year (execution and difficulty table) | Cut | History. |
| Where this month sits ("above 0% of 1,862 stretches") | Cut | Demoralizing after a week off, and no advice. |

### Subject page (Mathematics)

| Item | Verdict | Reason |
|---|---|---|
| Grade D 60, "Brutal work is solid, easy work is holding you back" | Sharpen | From self-ratings. Easy tasks get rated lower because they're rushed or dull, not because the student can't do them. |
| Focus area: "Inconsistent execution on easier material" | Sharpen | Same source. Needs right/wrong to mean anything. |
| AI Recommendations (6 steps with material, pace, source) | Sharpen | The best thing in analytics: named books, problem ranges, time per problem. But "Easy Putnam-style problems" contradicts itself, and the success test ("execution above 55") is the student's own rating again. |
| Plan my next session (`session_plan.py`) | Keep | Books a real slot with sane minutes and XP. Mechanical and correct. |
| Read the record: key insights | Cut | Six findings, three pairs saying the same thing. |
| Aim this subject at a goal | Keep | Connects work to a goal. (Reach AIME is filed under Computer Science, though.) |

### Goals page and planner (`planner.py`)

| Item | Verdict | Reason |
|---|---|---|
| Suggest checkpoints, Suggest steps, Draft a goal | Sharpen | The brief has the goal's text and date but none of the record. So "Codeforces 2000" from 442 gets the same steps as from 1,900. Output reads like "Write unit tests for auth endpoints". |
| Current checkpoint with on track / behind | Keep | Clear state, tied to a date. |
| Distance to target (AIME 12 of 15, Codeforces 442 of 2,000) | Keep | A real target with a real gap. The best input the app has. |
| Goal card chart: difficulty against execution | Cut | The same self-rating grid, a fourth time. |
| Goal card chart: 12-week consistency | Cut | Which days had work. No action. |
| Footer "Your goals. Your system. Your future." | Cut | Slogan. |

### Dashboard

| Item | Verdict | Reason |
|---|---|---|
| Your next sessions | Cut | Same block as Recommendations. Keep one. |
| Goal tile: "Focus for 2,000 hours, 414,697 / 7,200,000, 26,212 days behind" | Sharpen | A units bug (seconds shown against hours). |
| Goal tile: "Earn 250,000 XP, 479 days behind" | Sharpen | Due in 8 months but "479 days behind". Say what a week needs instead. |
| Weekly overview vs same days last week | Keep | Short and fair. |

### Analytics notifications (`notify.py`)

| Item | Verdict | Reason |
|---|---|---|
| "Your last seven days" digest | Sharpen | It's actually week to date, so on a Monday it reads near zero. Just counts. Should carry the one line that matters (days worked 10, was 27) and the nearest deadline. |
| "Nothing recorded since 8 October" | Sharpen | Kind tone, but the reason it gives is the consistency score. It should name one short task on the nearest goal. Its date is one day off from the Recommendations tab. |
| "Best day you have had" | Keep | Rare, true, costs nothing. |

**Tally:** 94 items. Keep 13, sharpen 21, cut 60.

## 2. What the app could tell a student that would change what they do

1. **"47 days to the USACO December contest. You're on Silver DP with no steps yet. You worked on CS on 2 days in the last two weeks. Book 3 Silver DP sessions this week."**
   Data it already has: goal target date, current checkpoint, linked subject, finished tasks by subject. `session_plan.py` can already book the sessions. Today `next_actions.py` only looks at goals within 45 days of their date, so it skips this one by two days.

2. **"You have 50 things on today's list. You finish about 10 on a day you work. 43 are routines left over from last week. Clear those and keep these 3."**
   Data it already has: open tasks, due dates, recurring titles, tasks finished per working day. Planned vs done (74%) is already worked out on Insights.

3. **"Before the AIME date: Algebra is 14 days cold and Programming is 39. Do 20 minutes of each this week."**
   Data it already has: last finished task per subject, the subject each goal is filed under, the decay that Skill Growth already reports. Limit it to subjects tied to a dated goal so it doesn't nag about Laundry.

4. **"You missed 7 of your last 20 problems, and 5 of the 7 were DP. Next session: 5 DP problems from USACO Silver 2023, 15 min each."**
   Needs right/wrong answers. `skill_attempts` exists with Got it / Missed it buttons but has 0 rows, because it only lives in the skill tree. Cheap to collect: when a task title has a problem range ("#1-10"), ask "how many did you get?" on completion. One number.

5. **"4 of your last 6 bad Math sessions were 'unclear'. Start the next one with a worked example."**
   Needs the reason. The six struggle reasons are in `shared/rules.json` and the `tasks.reason` column exists, but it's empty on every task. Ask for it only when execution is rated 1 or 2, as one tap.

The common thread: the useful lines all hang off a **date** (exam or goal deadline) or a **miss** (wrong answer, stuck reason). The app has the dates and isn't using them. It doesn't collect the misses.

## 3. Smallest first change

**Make the deadline the first line of the plan.**

In `backend/tracking/next_actions.py`, change the goal rule so it always considers the active goal with the nearest target date (drop the 45-day cap, or raise it to 120). Write its line as: days left, the current checkpoint, sessions in its subject over the last 14 days, and how many to book this week. Give the row a "Book these" button that calls the existing `session_plan.py` booking. That row then becomes `plan.top`, so the Dashboard and the Recommendations tab both lead with it with no new UI.

It's one rule in one file and reuses data and booking code that already work. It turns the most valuable fact the app holds (a contest date) into the first thing the student sees.

Next after that, in order: cut the Five-year projection and the "Changes worth making" cards (they're built on XP and contradict other tabs), then add the "how many did you get?" field on completion so item 4 has data.
