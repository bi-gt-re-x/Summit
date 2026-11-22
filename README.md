# Summit

**A productivity app for students and lifelong learners that turns the work you
do into a record you can learn from.**

Summit is a task list, a calendar, a goal tracker and a study tool in one place.
Finishing work earns XP, keeps a streak alive and moves your goals forward, and
everything you log feeds an analytics side that tries to answer one question:
*what should you do differently tomorrow?*

---

## Contents

- [What's inside](#whats-inside)
- [Getting started](#getting-started)
- [Configuration](#configuration)
- [Accounts and sign-in](#accounts-and-sign-in)
- [Tests and checks](#tests-and-checks)
- [Tech stack](#tech-stack)
- [Project layout](#project-layout)
- [Design philosophy](#design-philosophy)
- [Roadmap](#roadmap)

---

## What's inside

### Dashboard
The home screen for the day: today's tasks, XP and level, the streak, a focus
timer that runs on a task, and quick links into the rest of the app. One broken
card can't blank the page.

### Tasks
Create, edit and complete tasks with priorities, subjects, due dates, time
estimates and descriptions. Bulk-complete a day's work in one go. Every finished
task pays out XP and lands in the record that Analytics reads.

### Calendar
Day, Week and Month views on a calm paper look. Tasks with a time sit on the
calendar as blocks; recurring routine blocks are kept separate from real
commitments so they don't count against you.

### Goals
Goals with steps, checkpoints and deadlines. Progress is read from the work you
actually log rather than typed in by hand, each goal gets a health read and a
plan, and finishing one asks first, then celebrates. Mango, the guide, walks a
new account through setting its first real goal.

### Analytics
One page, several tabs, built to agree with itself:

| Tab | What it's for |
| --- | --- |
| **Recommendations** | What to do next, ranked by priority, capacity and how far each goal has to go |
| **Overview** | Tasks finished, focus time, XP, streak and completion rate for a chosen period |
| **Insights** | Patterns in when and how you work, including the Behavior read |
| **Subjects** | Where your time goes by subject, with a full page per subject |
| **Growth** | The growth chart and the five-metric report card |
| **Review** | A weekly review, and experiments that test a change against your own work |

Each figure says what kind of claim it is making (counted exactly, estimated,
or still preliminary), so a new account isn't shown confident numbers it
hasn't earned.

### Skill Trees
Subject trees for mathematics, science, programming, computer science, AI/ML,
music, writing, chess, fitness, productivity and more. Each node has practice
problems with strict answer marking, and nodes you already know can be skipped.

### Spaces
Personal and team pages built from blocks: text, tables, countdowns, real tasks,
and live panels from the rest of the app (analytics, goals, records, the timer,
the log). Pages can be filed into folders and come with undo, version history
and templates.

### Log
A running journal of what you did. Pin entries, mark milestones, and search the
whole thing.

### Achievements
XP, levels, streaks (with one forgiven day a month once a run is a week old),
badges and personal records.

### Search
The magnifier in the top bar searches your **tasks** and the **components** the
app is made of: every page, every Analytics and Calendar tab, and every section
of Settings. It moves to the closest match as you type, so typing "dark mode"
lands on Settings → Appearance without pressing Enter.

| Key | Does |
| --- | --- |
| Down / Up | next and previous match |
| Enter | close; you are already there |
| Escape | close, and go back to where you were |

### Notifications
The bell reads your own record when you open the app and says what's true:
overdue and upcoming tasks, today's calendar, a weekly summary, goals near their
date, a streak at risk, and progress worth marking. There are six kinds, each
with its own switch in Settings. A deleted notification stays deleted until
something new happens.

### Themes
Light and dark themes, a warm paper look, and per-account preferences set in
Settings.

---

## Getting started

You need **Python 3** (developed on 3.13) and **Node.js 20.19+**. Everything
runs from the repo root.

```bash
git clone -b summit-v1.2.3 https://github.com/bi-gt-re-x/Summit-v1.2.2.git Summit
cd Summit

# Backend
python3 -m venv .venv-fastapi
.venv-fastapi/bin/python -m pip install -r requirements.txt

# Frontend
npm install

# Optional: copy the env template and fill in only what you want
cp .env.example .env
```

Run the two servers in separate terminals:

```bash
.venv-fastapi/bin/python run.py   # API on http://127.0.0.1:5050
npm run dev                       # the app on http://127.0.0.1:5090
```

**Open port 5090 while developing.** The Vite dev server proxies `/api`,
`/static`, `/auth` and `/verify` to the backend, so the whole app works on that
one origin with hot reload.

With no `DATABASE_URL` set, Summit builds a local SQLite database at
`data/summit.db` from the schema in `data/sql/` on first start. Point it at a
throwaway copy with `SUMMIT_DB=/path/to/copy.db` for anything experimental.

Port 5050 is used instead of 5000 because macOS reserves 5000 for AirPlay
Receiver. Set `PORT` to override it.

Interactive API docs are served at `/docs` while the backend is running.

---

## Configuration

Every setting is optional; the app runs without a `.env`. See
[`.env.example`](.env.example) for the full list with comments. The main ones:

| Variable | What it turns on |
| --- | --- |
| `SECRET_KEY` | Session signing. Unset, a per-machine key is generated into a git-ignored file. **Set it for any deployment.** |
| `DATABASE_URL` | PostgreSQL instead of SQLite. Tables are created on first start. |
| `MAIL_USERNAME`, `MAIL_PASSWORD` | Real verification e-mail over SMTP. |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | The "Continue with Google" button. |
| `HF_TOKEN`, `ANTHROPIC_API_KEY`, `XAI_API_KEY` | Model-written goal checkpoints, plans and suggestions. Without them those parts use built-in rules or stay hidden. |

To move an existing SQLite database into Postgres, run
`scripts/migrate_to_postgres.py`.

---

## Accounts and sign-in

Pages with personal data need an account. A signed-out visitor who opens one is
sent to the home page with the sign-in popup open, and lands on the page they
wanted once they're through.

```
                       ┌──────────── Welcome ────────────┐
                    Log In                         Create Account
                       │                                 │
                       │                     Name · E-mail · Password
                       │                                 │
                       │                       verification e-mail
                       └────────────────┬────────────────┘
                                Complete Profile
                     (username optional · theme · daily goal)
                                        │
                                    Dashboard
```

**Verification e-mail.** Without mail credentials the app runs in dev mode: the
verification link is printed to the server console and shown in the popup, so
the whole flow works on a laptop. With `MAIL_USERNAME` and `MAIL_PASSWORD` set
it sends over SMTP instead. For Gmail, use an
[App Password](https://myaccount.google.com/apppasswords) (2-Step Verification
must be on).

**Sign in with Google.** The button only appears once `GOOGLE_CLIENT_ID` and
`GOOGLE_CLIENT_SECRET` are set.

1. In the [Google Cloud Console](https://console.cloud.google.com/), make or pick a project.
2. APIs & Services → OAuth consent screen → External → add yourself under Test users.
3. Credentials → Create credentials → OAuth client ID → Web application.
4. Add `http://127.0.0.1:5050/auth/google/callback` as an authorised redirect URI.
5. Copy the client ID and secret into `.env` and restart.

Google has already verified the address, so Google sign-in skips the
verification e-mail and goes straight to Complete Profile.

---

## Tests and checks

```bash
.venv-fastapi/bin/python -m pytest   # backend
npm test                             # frontend (Vitest)
npm run build                        # typecheck + repo checks + production build
```

`npm run build` runs a set of repo checks before Vite builds: the TypeScript
typecheck, the skill-tree and step validators, a CSS check, and a docs check
that fails if a comment points at a file that no longer exists.

To run the backend suite against Postgres instead of SQLite:

```bash
SUMMIT_TEST_DATABASE_URL=postgresql://localhost/summit_test .venv-fastapi/bin/python -m pytest
```

---

## Tech stack

| Layer | Tools |
| --- | --- |
| Frontend | React 19, TypeScript, Vite, React Router, KaTeX, Lucide icons |
| Backend | Python, FastAPI, Uvicorn |
| Storage | SQLite by default, PostgreSQL when `DATABASE_URL` is set |
| Engine | A small C++ library that searches candidate schedules (`engine/`, built with `engine/build.sh`) |
| Tests | pytest, Vitest, Testing Library |

---

## Project layout

```
run.py              entry point (API on :5050)
backend/            FastAPI app: routes, tracking (the rules), database, config
frontend/src/       the React app: pages, components, services, styles
frontend/html, js/  the original server-rendered pages, still live for a few routes
shared/             rules and test cases both halves read
engine/             C++ engine source
data/sql/           database schema and seed
scripts/            repo checks, seeding and migration tools
tests/              backend test suite
docs/               architecture, API, database, roadmap and changelog
```

More detail:

- [docs/architecture.md](docs/architecture.md): how the pieces fit together
- [docs/api.md](docs/api.md): the API
- [docs/database.md](docs/database.md): the datastore and the move to Postgres
- [docs/roadmap.md](docs/roadmap.md): what's built and what's next
- [docs/changelog.md](docs/changelog.md): what changed and why

---

## Design philosophy

**Consistency over intensity.** Long-term habits matter more than occasional
bursts, so streaks forgive a day and the growth ratings reward steady work over
big workloads.

**Progress should be measurable.** You should be able to see how you've
improved over weeks, months and years.

**Say something useful or say nothing.** A figure earns its place only if it
changes what you'd do tomorrow. A quiet week means a quiet notification bell.

**Productivity should feel rewarding.** XP, levels, badges and records are
there to bring you back each day.

**Simplicity first.** Clarity and usability without losing depth.

---

## Roadmap

Summit is under active development. Next up:

- Scheduled reminders (they need a job runner; today's notifications are read
  when you open the app)
- Cloud sync and cross-device support
- Data export
- Fuller team workspaces
- Habit tracking as a feature of its own

See [docs/roadmap.md](docs/roadmap.md) for the engineering view.
