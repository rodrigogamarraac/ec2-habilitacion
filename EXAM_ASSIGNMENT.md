# Final Exam — Backend

**Estimated Time:** 8 hours 
**Submission:** single Git repository, with two branches. main and dev. one PR where all the changes are. 
**Deadline**: Friday May 22 at 15:00.

## 1. Scenario

You are joining a small startup that has been asked to build the backend for a **platform**. The previous developer left after producing only a one-page sketch. Your job is to deliver a working backend that the frontend team can start integrating against on Friday.

The product owner wrote the following in Slack and then went on vacation:

> Hey — we need the admin panel for our ops team to manage events, venues and other types. Then a public API for the web app to list events and buy tickets. Use python stack but it has to run with one `docker compose up`. Make it fast — people complain when the listings page is slow. Oh and the same Postgres should be fine for everything, no need for a separate search thing.

That is the entire brief you have. Everything else is your decision — document your decisions in the README.

## 2. Domain — only ONE of these three

You **must implement exactly one** of the following domains. Do not mix them. Do not invent a fourth one.

### Option A — Concert / Event Ticketing
- **Entities:** `Venue`, `Event`, `TicketType` (e.g. General Admission, VIP, Early Bird), `Order`, `Ticket`.
- **Relationships:** one Venue has many Events; one Event has many TicketTypes; one Order has many Tickets; each Ticket belongs to one TicketType.

### Option B — Conference Sessions & Registrations
- **Entities:** `Conference`, `Track`, `Session`, `Speaker`, `Registration`.
- **Relationships:** one Conference has many Tracks; one Track has many Sessions; Sessions and Speakers are many-to-many; one Registration belongs to one User and one Session.

### Option C — Restaurant Reservations
- **Entities:** `Restaurant`, `TableType`, `MenuItem`, `Reservation`, `ReservationGuest`.
- **Relationships:** one Restaurant has many TableTypes and many MenuItems; one Reservation belongs to one Restaurant and one TableType; one Reservation has many Guests.

> Whichever you pick, the rest of this document refers generically to "the main resource" (Event / Session / Reservation) and "the child resource" (Ticket / Registration / Guest).

## 3. Functional Requirements

### 3.1 Django Admin Service

- Use Django 4.2 or 5.x. The Django app must expose **only the admin panel** — no public API endpoints.
- The Postgres schema for the domain tables must live in a `content` schema (not `public`). All models should be in that schema.
- Use UUID primary keys for all domain tables.
- All tables must have `created` and `modified` timestamp fields.
- The admin must support search, filtering, and inline editing of child resources.
- A superuser must be created automatically on first start, with credentials from environment variables.

### 3.2 FastAPI Public API

- Read-only endpoints (`GET`) over the same Postgres database used by Django.
- Must expose at least:
  - `GET /api/v1/<resource>/` — paginated list with optional filtering.
  - `GET /api/v1/<resource>/{id}` — single item with all related child data.
  - `GET /api/v1/<resource>/search/?query=...` — text search across the main fields.
- All responses must be JSON. Use Pydantic models for response schemas.
- The FastAPI service must NOT depend on the Django service at runtime (only on Postgres + Redis).

### 3.3 Caching

- Use Redis to cache list and detail responses.
- Cache invalidation strategy is your choice — explain it in the README.
- Cache misses must not bring down the API — if Redis is unreachable, the API must still serve responses from Postgres (graceful degradation).

### 3.4 Business Logic — MANDATORY

You must implement **at least one** non-trivial piece of business logic from the list below. Pick one that fits your domain choice. The logic must be exercised by the FastAPI service, not only by the admin.

1. **Inventory / capacity enforcement.** When the API returns availability for the main resource. The computation must be correct under concurrent reads (you do not need to handle concurrent writes — those go through admin).
2. **Time-window filtering.** Provide an endpoint that returns only items whose start time falls within a configurable window (e.g. "next 7 days", "this weekend"). The window definition must respect a timezone passed as a query parameter, defaulting to UTC.
3. **Pricing rules.** Each main resource has one or more pricing tiers with optional start/end validity dates. The API must return the *currently active* price for each item, considering the request time and any overlapping tiers (you decide the tie-breaking rule and document it).

> You may implement more than one, but only if the first one is solid.

### 3.5 Reverse Proxy

- All HTTP traffic from the outside must go through Nginx on port 80.
- Nginx must:
  - Route `/admin/`, `/static/` and any Django paths to the Django service.
  - Route `/api/` to the FastAPI service.
  - Serve Django static files directly (do not proxy static asset requests to Django/uWSGI).
  - Hide the Nginx version from response headers.
  - Set reasonable timeouts.
  - Route `/` serve the frontend 
  - Handle 404 responses using a generic html 

### 3.6 Application Server

- Django must run behind a production-grade server. uWSGI or Gunicorn — your choice.
- FastAPI must run behind Uvicorn workers (you may use Gunicorn as a process manager if you prefer).
- The Django dev server (`runserver`) and `uvicorn --reload` are **not acceptable** for the final submission.

### 3.7 Docker Compose

A single `docker compose up` from the repository root must bring up the entire stack: Postgres, Redis, Django, FastAPI, Nginx. After roughly 30 seconds the following must work from the host:

- `http://localhost/admin/` — Django admin login.
- `http://localhost/api/v1/<resource>/` — FastAPI listing.
- `http://localhost/api/openapi.json` — FastAPI OpenAPI schema.
- `http://localhost/` — Frontend
- `http://localhost/apiaaaaaa` — 404 html page
- A `/healthz` endpoint on each service that checks its dependencies and returns 200/503.

Healthchecks are required.

## 4. Non-functional Requirements

- **Configuration via environment variables.** No hard-coded credentials, ports, or hostnames in code. Provide a `.env.example`.
- **Migrations.** Django migrations must run automatically at container start. Do not commit a SQL dump.
- **Logging.** Both services must log to stdout in a parseable format.
- **Tests.** At least 5 meaningful tests per service. Use `pytest`.
- **README.** Must include: how to run, how to test, your design decisions, the trade-offs you made, and at least one thing you would do differently with more time. Add diagrams for the systems. How the modules interact with each other. 

## 4. Code Quality — SOLID Principles (MANDATORY)

Every layer of your code — Django models/admin, FastAPI routers/services/repositories, business logic, cache layer — must be designed following the **SOLID principles** and **Design patterns**. We will look for evidence of all five during code review.

**Concretely**, the reviewer expects to find, at minimum:

- At least one abstract base class or `Protocol` per concern (cache, repository, search). Concrete classes implement it.
- Constructor injection (or FastAPI `Depends`) instead of imports inside function bodies.
- No business logic inside Django views or FastAPI route handlers — push it down to a service layer.
- No SQL string concatenation inside service classes — repositories own that.

A submission that "works" but is one 800-line `views.py` file will be capped at **60%** regardless of feature completeness. Or code that is just there but there this code doesn't add any value to the implementation. Always ask why do we need this piece of code?

## 4. Database Design — UML / ER Diagram (MANDATORY)

Before you write a single migration, design the schema. Submit it in the repository as either:

- An **ER diagram**
- A **UML class diagram** showing classes, attributes, types, multiplicities, and relationships.
- ddl document for the DB

The diagram must include:

- All domain entities (not Django's built-in `auth_user` table).
- Primary keys and foreign keys explicitly marked.
- Cardinality on every relationship (1:1, 1:N, M:N).
- Non-trivial attributes with their data types (UUID, timestamp with timezone, decimal(p,s), etc.).
- Any junction tables for many-to-many relationships.

## 5. What we will check

The reviewer will:

1. Clone your repo on a fresh machine.
2. Copy `.env.example` to `.env` (and maybe edit one or two values).
3. Run `docker compose up`.
4. Hit the endpoints listed.
5. Log in to the admin and create a few records.
6. Verify those records appear in the FastAPI responses.
7. Stop Redis and verify the API still responds.
8. Read your tests and your README.
9. Run `pytest` from the repo root.
10. C4 diagrams for the system and its interactions 
11. review the PR. There must be a PR otherwise the code will not be graded.

**If any step above requires the reviewer to debug your setup, points will be deducted.**

## 6. Grading

| Area                                                                      | Weight  |
| ------------------------------------------------------------------------- | ------- |
| Docker Compose works end-to-end                                           | 5%      |
| Django admin (models, schema, admin UX)                                   | 5%      |
| FastAPI endpoints (correctness, schema, errors)                           | 5%      |
| Business logic implementation                                             | 10%     |
| Caching strategy and graceful degradation                                 | 5%      |
| Nginx configuration                                                       | 5%      |
| **SOLID / code structure / Design Patterns**                              | **10%** |
| **ER / UML diagram (matches code)**                                       | **5%**  |
| Tests                                                                     | 5%      |
| New Live business logic implementation and answers to code implementation | 40%     |
| README & decision documentation                                           | 5%      |

- A submission that does not run with `docker compose up` will be capped at 40%.
- A submission with no diagram, or a diagram that does not match the code, will be capped at 50%.
- A submission with everything in one file and no abstractions will be capped at 50%.
- The student should defend their submission. If the student cant defend the code then the score will be capped at 0%.


## 6. Reference Frontend

A simple static HTML/CSS/JS frontend is provided for **each of the three domain options** in the `frontends/` folder of this assignment. You do **not** need to modify the frontend, but:

- Your API must serve the endpoints the frontend calls (see the `fetch(...)` calls in each `app.js`).
- You may use the frontend during development to sanity-check your API.
- You must serve the frontend through Nginx at `/` - required, not graded.
- The frontend is plain HTML/CSS/vanilla JS, no build step, no framework. Do not introduce React, Vue, or a bundler "to make it nicer." Out of scope.

!Important: If your API does not match the contract the frontend expects, the frontend is the source of truth — adjust your API, not the frontend.

## 7. Hints, gotchas, and things we are NOT going to tell you

The following are intentionally left for you to figure out — exactly as you would on a real job. **There is no Slack to ping; make a decision, document it, and move on.**

- The product owner said "no separate search thing." Does that mean Postgres full-text search, `ILIKE`, trigram, or something else? Your call — but `search/` must return relevant results, not just any rows.
- Pagination format is not specified. Pick one (offset/limit, page-number, cursor). Be consistent.
- The brief says "make it fast." There is no SLA. Define a reasonable target in the README and explain how your design meets it.
- Django and FastAPI both touching the same database is a known source of bugs. Think about what happens when Django creates a record and the FastAPI cache still holds the old list.
- Nothing says the FastAPI service should be authenticated. Nothing says it should not be. Decide.
- The example domains have natural soft-delete cases (cancelled events, archived restaurants). Soft-delete is *not* required, but if you implement it, it must be respected by both services.
- Several fields in the domains above are ambiguous on purpose (e.g. "TicketType price" — is it stored on the type or per Order line? "Session capacity" — at the Session or the Track level?). Pick a sensible normalization and document it.
- The example you were shown in class used Elasticsearch. **Do not use Elasticsearch in this exam.** If you do, you will be asked to remove it during review.
- Sample data: you must seed at least 300 main resources and 500 child resources per main resource, automatically, on first start. A management command or a SQL fixture is fine. Do not require the reviewer to click through the admin to create test data.
- Timezone handling will be checked. At least one query parameter or one response field must demonstrate that your code is timezone-aware (and not silently in the server's local time).
- The Nginx config you copy from Stack Overflow probably does not hide the version header by default. Verify it with `curl -I`.
- One of the three business logic options above has a subtle race condition if implemented naively. Pick whichever you want — but if you pick that one, your README must explain how you handled it.

## 8. Extra credit (optional)

Up to +5% on top of the base grade, capped at 100%:
- Rate limiting on the FastAPI public endpoints (per IP, configurable).

## 9. What to submit
1. Git repository URL (must be reachable).
2. Create a pull request and the link to the PR should be shared.
3. One paragraph (in the README or a `SUBMISSION.md`) describing the single thing in your submission you are proudest of, and the single thing you are least happy about.
