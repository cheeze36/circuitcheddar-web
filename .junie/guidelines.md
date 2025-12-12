### CircuitCheddar — Developer Guidelines

#### Build and Configuration

- Runtime: Flask application using the application-factory pattern (`app.create_app`). SQLite database stored under the Flask `instance` folder.
- Entry points:
  - Development server via Flask CLI: `flask --app app:create_app run`
  - Alternative runner: `python circuitcheddar.py` (instantiates the app and calls `run()` directly).
- Instance path and DB:
  - Config key `DATABASE` points to `<instance>/circuitcheddar.sqlite` (set in `app/__init__.py`).
  - The `instance` folder is created automatically if missing.
  - DB schema lives at `app/resources/db/schema.sql` and is loaded by the `init-db` CLI command.
- Required packages (minimal):
  - Flask (includes Jinja2 and Click). On a new environment: `pip install Flask`
  - No other project-specific requirements are declared in-repo; if you hit missing deps, install them ad hoc.

Environment setup (Windows PowerShell examples):
- Optional virtualenv (recommended):
  - `python -m venv .venv`
  - `./.venv/Scripts/Activate.ps1`
- Run via Flask CLI without global env vars by passing `--app` explicitly:
  - `flask --app app:create_app run --debug`
- Or set env vars once per session:
  - `$env:FLASK_APP = 'app:create_app'`
  - `$env:FLASK_ENV = 'development'` (optional)
  - `flask run`

Database initialization/reset:
- The app registers a Click command `init-db` in `app/db.py`.
- Initialize or reset the DB:
  - `flask --app app:create_app init-db`
- This executes the SQL in `app/resources/db/schema.sql` against the configured SQLite file.

#### Project Topology

- App factory: `app/__init__.py` sets base config and registers blueprints:
  - `auth`, `home`, `projects`, `admin`, `articles`.
- Templates: Jinja2 under `app/templates/**`; `base.html` provides the layout; pages extend it.
- Static: `app/static/**` contains CSS (`styles.css`) and JS utilities.
- DB access: `app/db.py` exposes `get_db()` with `sqlite3.Row` row factory and teardown.

#### Running and Debugging

- Quick health check endpoint: `GET /hello` returns `"Hello, World!"` (declared inside `create_app`).
- For ad-hoc shell with app context:
  - `flask --app app:create_app shell`
  - Then: `from app.db import get_db; db = get_db()` etc.

#### Testing

Test framework: Python `unittest` is sufficient for current codebase. Use Flask’s test client from an app instance created in testing mode.

Run tests (unittest discovery):
- `python -m unittest discover -s tests -p "test_*.py" -v`

Adding a new test (working example):
- Create `tests/test_smoke.py` with the following content:
```
import unittest
from app import create_app

class SmokeTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()

    def test_hello_endpoint(self):
        resp = self.client.get('/hello')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Hello, World!', resp.data)

if __name__ == '__main__':
    unittest.main()
```

Verified: The above test passes locally with `python -m unittest discover -s tests -p "test_*.py" -v`.

Notes for writing tests:
- Prefer constructing the app via `create_app({'TESTING': True, ...})` to avoid depending on external config files.
- For DB-bound tests, use a temporary SQLite path by overriding `DATABASE` in the mapping and run schema via `with app.app_context(): init_db()` if needed.
- Avoid hitting the real `instance` DB in tests.

#### Code Style and Conventions

- Follow the existing style in each module; the repository does not enforce a linter or formatter.
- Blueprints: keep routes grouped by domain (mirroring `auth`, `home`, `projects`, `admin`, `articles`).
- Templates extend `templates/base.html`; keep shared layout and styles centralized there. Use Jinja idioms already present in templates.
- Static assets: prefer `url_for('static', filename='...')` in templates for cache-busting.
- Database layer: use `get_db()` from `app.db`; rows are dict-like via `sqlite3.Row`.

#### Troubleshooting

- If `flask` CLI fails to locate the app, pass `--app app:create_app` explicitly or set `$env:FLASK_APP`.
- If the DB file is missing/corrupt, re-run `flask --app app:create_app init-db`.
- Windows path issues: prefer PowerShell with `--app` argument to avoid environment var quirks.
