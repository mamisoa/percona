## [2025-12-06T20:51:34.886255]

### Added

- Warning surfacing for replication lag (`wsrep_last_applied` vs `wsrep_last_committed`) and cross-node drift >3% vs the max committed value, shown in Rich panels without failing cluster health.

### Changed

- Report renders per-node and cluster-level warnings in Rich output.

## [2025-12-06T20:42:58.880590]

### Added

- Rich-powered console rendering with highlighted `wsrep_ready`, `wsrep_local_state`, `wsrep_last_applied`/`wsrep_last_committed`, and local node health indicators.

### Changed

- Cluster report now uses Rich panels and tables for clearer emphasis on key wsrep fields and cluster summary.
- Declared `rich` dependency in `pyproject.toml` for enhanced console output.

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

## [2025-12-06T20:08:47.277720]

### Fixed

- Added `from __future__ import annotations` to resolve forward reference NameError for `EnvDefaults`.

## [2025-12-06T20:10:16.330930]

### Added

- Declared `cryptography` dependency to support sha256_password / caching_sha2_password auth paths.
- README now notes the requirement and how to fix missing-crypto errors.

## [2025-12-06T20:14:32.965789]

### Added

- Connectivity probe script `tests/db_connection_check.py` using .env values.
- README documents the quick connectivity test command.

## [2025-12-06T20:24:01.266216]

### Changed

- Cluster report now labels nodes with a sequence number (Node #1, Node #2, ...).

## [2025-12-06T20:27:39.979915]

### Added

- Report now includes `wsrep_last_applied` and `wsrep_last_committed` per node.

## [2025-12-06T11:49:31.612378]

### Added

- uv configuration and CLI entry point `percona-cluster-check` in `pyproject.toml`.
- README guidance for running the checker via `uv run`.

### Changed

- Switched dependency management to uv with explicit `pymysql` requirement.

