2025-12-06T11:49:31.612378

- Added uv support: `pymysql` dependency, CLI script `percona-cluster-check`.
- README now documents `uv sync` and `uv run` usage for the cluster checker.
- CHANGELOG entry added for the uv migration.
2025-12-06T12:07:06.438667

- Added python-dotenv and .env support (DB_USER, DB_PASSWORD, DB_HOSTS, DB_PORT).
- CLI defaults now read from .env; README documents usage.
- Tests added for env loading/override; .gitignore updated to exclude .env.
2025-12-06T12:08:38.593000

- Fixed uv config: `[tool.uv]` now uses `package = true` (removed invalid `cache`).
2025-12-06T12:11:11.906143

- `.gitignore` extended to skip `.venv/` so virtualenv artifacts are not committed.

