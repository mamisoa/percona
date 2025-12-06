## [2025-12-06T12:07:06.438667]

### Added

- Environment variable support (.env) via `python-dotenv`.
- CLI defaults sourced from DB_USER, DB_PASSWORD, DB_HOSTS, DB_PORT.
- Tests for env loading and CLI override in `tests/test_env_loading.py`.
- `.gitignore` entry to keep `.env` out of VCS.

### Changed

- README now documents .env usage and uv run examples with env defaults.

## [2025-12-06T12:08:38.593000]

### Changed

- Updated `[tool.uv]` configuration to use `package = true` (removed invalid `cache` key).

## [2025-12-06T12:11:11.906143]

### Changed

- Extended `.gitignore` to exclude local `.venv/` to avoid committing virtualenv artifacts.

## [2025-12-06T11:49:31.612378]

### Added

- uv configuration and CLI entry point `percona-cluster-check` in `pyproject.toml`.
- README guidance for running the checker via `uv run`.

### Changed

- Switched dependency management to uv with explicit `pymysql` requirement.

