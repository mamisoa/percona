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
2025-12-06T20:08:47.277720

- Added future annotations import to fix NameError on `EnvDefaults` forward reference.
2025-12-06T20:10:16.330930

- Added `cryptography` dependency for MySQL auth plugins; README updated with guidance.
2025-12-06T20:14:32.965789

- Added db connectivity probe script (`tests/db_connection_check.py`) and documented usage in README.
2025-12-06T20:24:01.266216

- Cluster report now prefixes each node with a sequence number (Node #n).
2025-12-06T20:27:39.979915

- Added `wsrep_last_applied` and `wsrep_last_committed` to the node report output.

2025-12-06T20:42:58.880590

- Implemented Rich-based console rendering highlighting wsrep readiness, local state, last applied/committed, and node health, plus colored cluster summary.
- Added `rich` dependency to `pyproject.toml` for enhanced console output.

2025-12-06T20:51:34.886255

- Added warning reporting for wsrep replication lag (applied vs committed) and cross-node drift >3% vs max committed, surfaced in Rich panels without failing cluster health.

2025-12-06T20:57:07.175320

- Refactored monolithic `main.py` into modular `percona` package (env, models, wsrep logic, rendering, CLI).
- CLI entry now points to `percona.cli:main`; `main.py` kept as a shim for compatibility.
- Tests updated to import from new module paths.