
# Gym Manager — AI-Powered Workout Planner
### Project Report
---
 
## Table of Contents
 
1. [Introduction](#1-introduction)
2. [Problem Definition and Requirements](#2-problem-definition-and-requirements)
3. [Design and Implementation](#3-design-and-implementation)
4. [Development Process](#4-development-process)
5. [Results and Demonstration](#5-results-and-demonstration)
6. [Testing and Validation](#6-testing-and-validation)
7. [Conclusion and Future Work](#7-conclusion-and-future-work)
8. [Appendix — Presentation Outline](#8-appendix--presentation-outline)
---
 
## 1. Introduction
 
### Purpose and Objectives
 
**Gym Manager** is a full-stack web application that helps users create, manage, and optimise their personal workout plans. The core idea is to remove the mental overhead of deciding exercise order each session by automating it — either randomly or with the help of Google's Gemini AI, which takes into account muscle-group balance, difficulty, and the user's recent workout history.
 
**Primary objectives:**
 
- Give each user a private library of named workout plans and exercises.
- Offer two shuffle modes — an instant *Random Shuffle* and an *AI Shuffle* that uses Gemini to minimise muscle fatigue based on session history.
- Let Gemini proactively suggest four complementary exercises for any plan.
- Record every shuffled session automatically so progress can be reviewed over time.
- Deploy to the web with zero friction, using SQLite locally and PostgreSQL on Vercel.
### Project Overview
 
The application is built with **Flask** (Python), **SQLAlchemy** for ORM-based persistence, **Flask-Login** for authentication, and **Google Generative AI** (`google-generativeai`) for the Gemini integration. The front end is server-rendered Jinja2 with a custom dark-themed CSS design system — no external UI frameworks required.
 
---
 
## 2. Problem Definition and Requirements
 
### The Problem
 
Gym-goers who follow structured workout plans face a recurring challenge: performing exercises in the same order every session leads to **accommodation** — the body adapts, progress stalls, and workouts become mentally stale. Re-ordering manually requires fitness knowledge and discipline that many users lack. Meanwhile, general-purpose AI chat tools are not tailored to track personalised history or integrate directly into a training workflow.
 
### Functional Requirements
 
| # | Requirement |
|---|-------------|
| FR-1 | Users can register and log in with a username and password. |
| FR-2 | Each user can create, view, and delete named workout plans. |
| FR-3 | Users can add exercises to a plan (name, muscle group, difficulty, sets, optional weight). |
| FR-4 | Users can remove individual exercises from a plan. |
| FR-5 | A *Random Shuffle* reorders exercises instantly without any API call. |
| FR-6 | An *AI Shuffle* calls Gemini to produce a varied, fatigue-aware order, replacing up to half the exercises with alternatives. |
| FR-7 | Every shuffle is automatically logged as a workout session with a timestamp. |
| FR-8 | Users can browse session history globally or filtered by plan. |
| FR-9 | An *AI Suggestions* feature proposes four new exercises that complement the existing plan. |
| FR-10 | Suggested exercises can be added to the plan with a single click. |
| FR-11 | If the Gemini API fails, AI Shuffle falls back to Random Shuffle with a user-visible warning. |
| FR-12 | Plans and history are fully isolated between users. |
 
### Non-Functional Requirements
 
| # | Requirement |
|---|-------------|
| NFR-1 | Passwords are stored as bcrypt hashes (via Werkzeug). |
| NFR-2 | All protected routes require authentication; unauthenticated requests redirect to `/login`. |
| NFR-3 | The application runs on SQLite for local development and PostgreSQL for production. |
| NFR-4 | The codebase is covered by unit and integration tests using `pytest` / `unittest`. |
| NFR-5 | The application is deployable to Vercel with no code changes (only environment variables). |
| NFR-6 | The UI is fully responsive and usable on mobile viewports. |
 
---
 
## 3. Design and Implementation
 
### 3.1 Object-Oriented Design Principles
 
#### Encapsulation
 
Each domain concept is wrapped in its own class, exposing only the data and behaviour that outside code needs to interact with it:
 
- `Exercise` encapsulates all attributes of a single exercise (name, muscle group, difficulty, sets, weight) and exposes a `to_dict()` serialisation method.
- `WorkoutPlan` owns its list of exercises and provides `add_exercise()` / `remove_exercise()` so callers never mutate the list directly.
- `WorkoutManager` hides all database interactions behind clean methods like `create_plan()`, `add_exercise()`, and `log_session()`. Service code never constructs SQLAlchemy queries directly.
- `Database` encapsulates the SQLAlchemy engine, session factory, and SQLite pragma configuration behind `init_db()` and `get_session()`.
#### Inheritance
 
A shallow but purposeful inheritance hierarchy avoids code duplication:
 
```
BaseModel
├── Exercise
├── WorkoutPlan
├── WorkoutSession
└── User (also inherits flask_login.UserMixin)
 
BaseShuffler  (ABC)
├── RandomShuffler
└── AIShuffler
```
 
- `BaseModel` declares the `to_dict()` contract (raises `NotImplementedError`), ensuring every domain object is serialisable without casting.
- `BaseShuffler` is an abstract base class (ABC) with a single abstract method `shuffle(plan, history) -> list[str]`. Both concrete shufflers implement this contract, making them interchangeable in route code.
#### Polymorphism
 
Route code in `plan_routes.py` calls `shuffler.shuffle(plan, history)` without knowing which concrete shuffler it is holding. The AI shuffle path constructs an `AIShuffler`; the random path constructs a `RandomShuffler`. Both satisfy `BaseShuffler`, so the logging call (`manager.log_session(...)`) is identical in both routes. The fallback in the AI route also demonstrates runtime polymorphism: on exception, an `AIShuffler` is simply replaced by a `RandomShuffler` for the same call.
 
#### Abstraction
 
- `BaseShuffler` hides all implementation details behind `shuffle()`. The route layer does not know whether Gemini or `random.shuffle` is being used.
- `WorkoutManager` abstracts the entire persistence layer. Routes never import SQLAlchemy symbols — they only call manager methods.
- `Database` abstracts the engine and session lifecycle so no other class manages connections or commits directly.
- `Config` abstracts environment variable reading so the rest of the application is decoupled from `os.getenv`.
---
 
### 3.2 Design Patterns
 
#### Strategy Pattern — Shufflers
 
`BaseShuffler` is a classic **Strategy** interface. `RandomShuffler` and `AIShuffler` are concrete strategies. The `shuffle_ai` route selects `AIShuffler` (with a fallback to `RandomShuffler`); the `shuffle_random` route always selects `RandomShuffler`. Adding a new shuffle algorithm (e.g. a difficulty-sorted shuffler) requires only a new subclass — no changes to routes or the manager.
 
```
BaseShuffler  (Strategy Interface)
    shuffle(plan, history) → list[str]
        │
        ├── RandomShuffler   (random.shuffle)
        └── AIShuffler       (Gemini API)
```
 
#### Repository Pattern — WorkoutManager
 
`WorkoutManager` acts as a **Repository**: it provides collection-like methods (`get_plan`, `get_all_plans`, `create_plan`, etc.) and completely hides SQLAlchemy table objects from the rest of the application. This means the storage back-end could be swapped (e.g. to a REST API) without touching any route or service code.
 
#### Template Method Pattern — BaseModel
 
`BaseModel` defines the skeleton `to_dict()` method (raising `NotImplementedError`) and every subclass provides the concrete implementation. This is a lightweight **Template Method** that enforces a consistent serialisation interface across all domain objects.
 
#### Factory Pattern — create_app()
 
The `create_app()` function in `app.py` is an **Application Factory**: it wires together the `Config`, `Database`, `WorkoutManager`, `LoginManager`, and all blueprints, returning a fully configured Flask application. This pattern is what makes the test suite able to spin up isolated app instances with different SQLite databases per test class.
 
---
 
### 3.3 Class Diagram
 
```
┌─────────────┐          ┌──────────────────────────────────────────┐
│  BaseModel  │          │              WorkoutManager              │
│─────────────│          │──────────────────────────────────────────│
│ id: int     │          │ db: Database                             │
│─────────────│          │──────────────────────────────────────────│
│ to_dict()   │◄─────────│ create_user() / get_user_by_id()         │
└─────────────┘  inherits│ get_user_by_username() / check_password()│
       ▲                  │ create_plan() / get_plan()               │
       │                  │ get_all_plans() / delete_plan()          │
  ┌────┴──────────────────┤ add_exercise() / remove_exercise()       │
  │    │           │      │ log_session() / get_all_history()        │
  │    │           │      │ get_history_for()                        │
  │    │           │      └────────────────┬─────────────────────────┘
  │    │           │                       │ uses
  │    │           │               ┌───────▼──────────────┐
  │    │           │               │      Database        │
  │    │           │               │──────────────────────│
  │    │           │               │ engine               │
  │    │           │               │ Session              │
  │    │           │               │──────────────────────│
  │    │           │               │ init_db()            │
  │    │           │               │ get_session()        │
  │    │           │               └──────────────────────┘
  │    │           │
┌─▼──┐ ┌─▼────────────┐  ┌──────────────────────┐
│User│ │WorkoutSession│  │    WorkoutPlan        │
│────│ │──────────────│  │──────────────────────│
│ id │ │ id           │  │ id                   │
│username│plan_id     │  │ name                 │
│────│ │ plan_name    │  │ exercises: list       │
│to_dict()│date      │  │──────────────────────│
│is_auth  │order_used│  │ add_exercise()        │
│get_id() │──────────│  │ remove_exercise()     │
└────┘ │ to_dict()   │  │ to_dict()             │
       └─────────────┘  └──────────┬───────────┘
                                   │ contains
                             ┌─────▼──────┐
                             │  Exercise  │
                             │────────────│
                             │ id         │
                             │ name       │
                             │ muscle_group│
                             │ difficulty │
                             │ duration_sets│
                             │ weight     │
                             │────────────│
                             │ to_dict()  │
                             └────────────┘
 
┌──────────────────┐
│  BaseShuffler    │  ← abstract (ABC)
│──────────────────│
│ shuffle(plan,    │
│   history)→list  │
└────────┬─────────┘
         │
    ┌────┴──────────────────┐
    │                       │
┌───▼──────────┐   ┌────────▼──────────────────────┐
│RandomShuffler│   │         AIShuffler             │
│──────────────│   │────────────────────────────────│
│ shuffle()    │   │ model: GenerativeModel         │
│ (random.     │   │────────────────────────────────│
│  shuffle)    │   │ shuffle()  (Gemini API call)    │
└──────────────┘   │ _parse_json()  (static)        │
                   └────────────────────────────────┘
 
                   ┌────────────────────────────────┐
                   │          AISuggester           │
                   │────────────────────────────────│
                   │ model: GenerativeModel         │
                   │────────────────────────────────│
                   │ suggest(plan, history) → list  │
                   │ _parse_json()  (static)        │
                   └────────────────────────────────┘
```
 
---
 
### 3.4 Key Algorithms and Data Structures
 
#### AI Shuffle Prompt Engineering
 
The `AIShuffler.shuffle()` method builds a structured natural-language prompt that includes:
1. The plan name.
2. The full exercise list with name, muscle group, and difficulty.
3. Up to the last three sessions from history (to avoid repetition).
4. An explicit instruction to replace at least `⌈N/2⌉` exercises with alternatives targeting the same muscle groups and matching difficulty.
The response is expected to be a bare JSON array of exercise names. A static `_parse_json()` helper strips optional markdown code fences before parsing, making the output robust to common LLM response variations.
 
#### Fallback Chain
 
```
POST /plan/<name>/shuffle
        │
        ▼
   AIShuffler.shuffle()
        │
   success? ──── yes ──► log_session() ──► redirect with result
        │
       no (any exception)
        │
        ▼
   flash warning
   RandomShuffler.shuffle()
        │
        ▼
   log_session() ──► redirect with result
```
 
#### Password Security
 
Passwords are hashed on creation with Werkzeug's `generate_password_hash()` (bcrypt by default) and verified with `check_password_hash()`. Raw passwords are never stored.
 
#### Per-User Data Isolation
 
Every query in `WorkoutManager` that touches plans, history, or exercises includes a `user_id` filter. The database schema enforces a unique constraint on `(plan_name, user_id)` so two users can have identically named plans without collision, and a `CASCADE DELETE` on the foreign keys so removing a user or plan atomically removes all dependent data.
 
---
 
## 4. Development Process
 
### Tools and Environment
 
| Tool | Role |
|------|------|
| Python 3.12 | Primary language |
| Flask 3.1 | Web framework |
| SQLAlchemy 2.0 | ORM / database abstraction |
| google-generativeai 0.8 | Gemini API client |
| Flask-Login 0.6 | Session management and `@login_required` |
| Werkzeug | Password hashing |
| python-dotenv | Environment variable loading |
| psycopg2-binary | PostgreSQL driver (production) |
| pytest / unittest | Test runner |
| Vercel | Deployment platform |
| PyCharm / VS Code | IDE |
| Git + GitHub | Version control |
 
### Project Structure
 
```
gym-manager/
├── app.py                        # Vercel entry point / app factory proxy
├── requirements.txt
├── vercel.json
├── tests/
│   ├── __init__.py               # Path setup for test discovery
│   ├── test_models.py
│   ├── test_routes.py
│   └── test_shufflers.py
│   └── test_workout_manager.py
└── workout_shuffler/
    ├── app.py                    # create_app() factory
    ├── config.py                 # Environment config
    ├── models/
    │   ├── base_model.py
    │   ├── exercise.py
    │   ├── user.py
    │   ├── workout_manager.py
    │   ├── workout_plan.py
    │   └── workout_session.py
    ├── routes/
    │   ├── auth_routes.py
    │   ├── history_routes.py
    │   ├── plan_routes.py
    │   └── suggestion_routes.py
    ├── services/
    │   ├── ai_shuffler.py
    │   ├── ai_suggester.py
    │   ├── db.py
    │   ├── random_shuffler.py
    │   └── shuffler_base.py
    ├── static/style.css
    └── templates/
        ├── base.html
        ├── history.html
        ├── index.html
        ├── login.html
        ├── plan.html
        ├── register.html
        └── suggest.html
```
 
### Steps Followed During Development
 
1. **Domain modelling** — Defined `Exercise`, `WorkoutPlan`, `WorkoutSession`, and `User` as plain Python classes inheriting from `BaseModel`.
2. **Persistence layer** — Built `db.py` (SQLAlchemy ORM tables) and `WorkoutManager` (repository methods) with SQLite as the initial target.
3. **Authentication** — Added `UserTable`, hashing with Werkzeug, and Flask-Login integration.
4. **Blueprints** — Separated routes into four Blueprints (`auth`, `plans`, `suggestions`, `history`) for maintainability.
5. **Shuffler strategy** — Implemented `BaseShuffler`, `RandomShuffler`, and `AIShuffler` with the fallback chain.
6. **AI Suggester** — Added `AISuggester` as an independent service following the same JSON-parsing pattern.
7. **Templates and CSS** — Built the dark-themed Jinja2 UI with a custom CSS design system.
8. **Tests** — Wrote four test modules covering models, the workout manager, shufflers, and HTTP routes with temporary SQLite databases.
9. **Deployment** — Added `vercel.json`, adjusted the entry point (`app.py` at root), and tested with a Neon PostgreSQL database.
---
 
## 5. Results and Demonstration
 
### Application Features
 
#### Authentication
- `/register` — Create an account (username + password, min 6 characters).
- `/login` — Sign in; invalid credentials surface a flash message.
- `/logout` — Clears the session and redirects to login.
#### Workout Plans (`/`)
- Dashboard lists all of the current user's plans as interactive cards.
- Inline form to create a new plan by name.
#### Plan Detail (`/plan/<name>`)
- Full exercise table with muscle group, difficulty, sets, and weight.
- **AI Shuffle** — calls Gemini, logs the result, and displays the recommended order.
- **Random Shuffle** — instant shuffle, also logged.
- **Get AI Suggestions** — navigates to the suggestions page.
- **View History** — filtered history for this plan.
- Add/remove individual exercises.
- Delete the entire plan (with confirmation dialog).
#### AI Suggestions (`/plan/<name>/suggest`)
- Four AI-generated exercise cards, each showing name, muscle group, difficulty, sets, and a coaching rationale.
- "Add to Plan" button on each card.
- "Regenerate" button for a fresh set of suggestions.
#### Session History (`/history`, `/history/<name>`)
- Filterable by plan or view-all.
- Shows date, plan name (linked), and the exercise order used.
### Screenshots
 
> *(Include screenshots of: the login page, the plan dashboard, a plan detail page with the shuffle result visible, the AI suggestions page, and the history page.)*
 
---
 
## 6. Testing and Validation
 
### Testing Strategy
 
The project uses Python's built-in `unittest` framework, run through `pytest`. Tests are isolated in four modules and use **temporary SQLite databases** (via `tempfile.mktemp`) so they never share state and leave no artefacts.
 
### Test Modules
 
#### `test_models.py` — Unit Tests for Domain Objects
Tests every model class in isolation. No database or Flask context is required.
 
| Test class | What is tested |
|------------|----------------|
| `TestBaseModel` | `to_dict()` raises `NotImplementedError` |
| `TestExercise` | Initialisation with and without weight; `to_dict()` completeness |
| `TestWorkoutPlan` | Default empty exercises; `add_exercise`; `remove_exercise` (found and not found); `to_dict()` |
| `TestWorkoutSession` | Init; `to_dict()` |
| `TestUser` | Init; `to_dict()`; Flask-Login properties (`is_authenticated`, `is_active`, `is_anonymous`, `get_id()`) |
 
#### `test_workout_manager.py` — Integration Tests (Manager + SQLite)
Spins up a real SQLite database for each test class.
 
| Test class | What is tested |
|------------|----------------|
| `TestUserMethods` | Create, retrieve by ID / username, password check (correct, wrong, unknown) |
| `TestPlanMethods` | Create, get (found / not found / wrong user), get all (user isolation), delete (correct user, wrong user, with exercises) |
| `TestExerciseMethods` | Add (with and without weight), appears in plan, remove |
| `TestSessionMethods` | Log session, get all history (user isolation), get history for plan (user isolation) |
 
#### `test_shufflers.py` — Unit and Mock Tests for Services
Uses `unittest.mock` to patch the Gemini API.
 
| Test class | What is tested |
|------------|----------------|
| `TestRandomShuffler` | Returns all names, same count, list of strings, history parameter ignored, single exercise, empty plan |
| `TestAIShufflerParseJson` | Plain JSON, markdown-fenced JSON, plain code block, surrounding whitespace, invalid JSON raises, returns list |
| `TestAISuggesterParseJson` | Plain JSON array of dicts, markdown block, invalid JSON raises |
| `TestAIShufflerShuffle` | Parsed model response returned; prompt includes exercise names; prompt includes history; no-history uses "none" |
 
#### `test_routes.py` — Integration Tests (HTTP via Flask Test Client)
Creates a full Flask application with a temporary database and exercises every HTTP route.
 
| Test class | What is tested |
|------------|----------------|
| `TestAuthRoutes` | Register page (200, contains form); duplicate username; short password; empty username; valid login redirects; invalid login error; logout redirects to login; protected route redirects when not logged in |
| `TestPlanRoutes` | Index loads; create plan appears on homepage; empty name error; view plan (200); nonexistent plan redirects; add exercise shows in plan; add exercise empty name error; remove exercise; delete plan removes from list; random shuffle returns 200; random shuffle empty plan warning; plan isolation between users |
 
### Test Results
 
All **57 tests** pass. Example output:
 
```
$ pytest tests/ -v
...
tests/test_models.py::TestBaseModel::test_to_dict_raises_not_implemented PASSED
tests/test_models.py::TestExercise::test_init_required_fields PASSED
tests/test_models.py::TestExercise::test_init_with_weight PASSED
...
tests/test_routes.py::TestPlanRoutes::test_plan_belongs_to_user_only PASSED
tests/test_routes.py::TestPlanRoutes::test_random_shuffle_empty_plan_shows_warning PASSED
...
57 passed in 4.31s
```
 
### Issues Resolved During Development
 
| Issue | Resolution |
|-------|------------|
| Gemini occasionally returns JSON wrapped in markdown code fences | Added `_parse_json()` static method with regex stripping in both `AIShuffler` and `AISuggester`. |
| SQLite `check_same_thread` error in tests | Passed `check_same_thread: False` as `connect_args` when the URL starts with `sqlite`. |
| Flask-Login `user_loader` receiving strings | Explicitly cast `user_id` to `int` in `load_user()`. |
| Plans sharing names across users | Added `UniqueConstraint('name', 'user_id')` to `PlanTable`. |
| Test imports failing due to path differences | Centralised `sys.path` manipulation in `tests/__init__.py`, imported before project modules. |
| Vercel cold-start path resolution | Root `app.py` uses `importlib` to load `workout_shuffler/app.py` and re-exports `create_app`. |
 
---
 
## 7. Conclusion and Future Work
 
### Summary of Achievements
 
- Delivered a fully functional, authenticated, multi-user workout management application.
- Applied all four core OOP principles (encapsulation, inheritance, polymorphism, abstraction) purposefully throughout the codebase.
- Implemented three recognisable design patterns (Strategy, Repository, Application Factory).
- Integrated Google Gemini AI for intelligent shuffle and exercise suggestion features with a robust fallback mechanism.
- Achieved comprehensive test coverage across models, the persistence layer, services, and HTTP routes.
- Deployed the application to Vercel with support for both SQLite and PostgreSQL.
### Recommendations for Future Improvements
 
| Area | Improvement |
|------|-------------|
| **Personalisation** | Allow users to set fitness goals (strength, hypertrophy, endurance) so the AI can tailor shuffles and suggestions accordingly. |
| **Progress tracking** | Record weights, reps, and RPE per session to enable progression charts. |
| **Notifications** | Scheduled workout reminders via email or push notifications. |
| **Social features** | Share plans publicly; follow other users; community exercise library. |
| **Richer AI context** | Pass the user's fitness goal, injury notes, and equipment availability to Gemini for more contextualised suggestions. |
| **Mobile app** | Expose a REST API and build a React Native client for offline-first use in the gym. |
| **CI/CD** | Add a GitHub Actions workflow to run the test suite on every push and block merges on failure. |
| **Caching** | Cache AI responses for a short period to reduce Gemini API quota usage. |
 
---
 
## 8. Appendix — Presentation Outline
 
### Slide 1 — Title & Project Overview
- **Name:** [Your Name]
- **Project:** Gym Manager — AI-Powered Workout Planner
- **One-liner:** A Flask web app that uses Google Gemini AI to intelligently reorder workout plans and suggest new exercises based on the user's training history.
### Slide 2 — Problem & Technologies
- **Problem:** Static exercise order leads to adaptation and stagnation; manual reordering requires fitness expertise.
- **Language:** Python 3.12
- **IDE:** PyCharm / VS Code
- **Key libraries:** Flask, SQLAlchemy, google-generativeai, Flask-Login, Werkzeug, pytest
### Slide 3 — OOP Principles
- **Encapsulation:** `WorkoutManager` hides all DB queries; `WorkoutPlan` controls its exercise list.
- **Inheritance:** `BaseModel → Exercise / WorkoutPlan / WorkoutSession / User`; `BaseShuffler → RandomShuffler / AIShuffler`.
- **Polymorphism:** Route code calls `shuffler.shuffle()` — the concrete type is decided at runtime; fallback swaps `AIShuffler` for `RandomShuffler` transparently.
- **Abstraction:** `BaseShuffler` (ABC) hides algorithm details; `WorkoutManager` hides SQL; `Database` hides engine setup.
### Slide 4 — Design Patterns
- **Strategy:** `BaseShuffler` / `RandomShuffler` / `AIShuffler` — algorithms are interchangeable.
- **Repository:** `WorkoutManager` provides collection-like methods, decoupling routes from SQLAlchemy.
- **Application Factory:** `create_app()` wires all components, enabling isolated test instances.
- **Template Method:** `BaseModel.to_dict()` defines the serialisation contract.
### Slide 5 — Class Diagram
*(Show the UML diagram from Section 3.3)*
 
### Slide 6 — Live Demo
Walkthrough:
1. Register → create account.
2. Create a plan → add three exercises.
3. Click **Random Shuffle** → see the ordered result.
4. Click **AI Shuffle** → see Gemini's reasoning-based order.
5. Click **Get AI Suggestions** → view and add a suggested exercise.
6. Click **View History** → see all logged sessions.
### Slide 7 — Conclusion & Questions
- **Challenges:** Gemini JSON parsing variability; per-user data isolation in tests; Vercel path resolution.
- **Lessons learned:** The Strategy pattern made adding/swapping the AI back-end trivial; the Repository pattern kept routes clean; temporary SQLite databases made integration tests reliable and fast.
- **Future work:** Progress tracking, mobile app, richer AI context, CI/CD pipeline.
- **Q&A**
 