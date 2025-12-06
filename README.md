## Percona XtraDB Cluster checker

Script to audit wsrep/Galera synchronization across Percona XtraDB Cluster nodes.

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) installed (`pip install uv` or see uv docs)
- Network access to your cluster nodes

### Setup

1) Install dependencies with uv:
   ```
   uv sync
   ```

2) Run the checker (example):
   ```
   uv run percona-cluster-check \
     --user root \
     --password 'your_password' \
     --hosts 192.168.20.230,192.168.20.231,192.168.20.232 \
     --port 3306
   ```

You can also invoke the module directly:
```
uv run python main.py --user root --hosts 127.0.0.1 --port 3306
```

Exit code is `0` when the cluster is healthy, `1` otherwise.

### Environment variables (.env)

The script loads a `.env` file automatically (git-ignored). Supported keys:
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOSTS` (comma-separated)
- `DB_PORT`

Example `.env`:
```
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOSTS=192.168.20.230,192.168.20.231,192.168.20.232
DB_PORT=3306
```

Command-line flags override environment defaults.

