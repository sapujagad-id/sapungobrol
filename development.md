# Development Guidelines

## Prerequisites

- Python >= 3.11
- Docker
- Atlas

### More on Atlas

Atlas is a language-agnostic database migration tool. To install Atlas, check out the [Getting Started](https://atlasgo.io/getting-started/) page here.

## Installation

1. Create a python virtual environment

```
python -m venv env
```

2. Activate the virtual environment

```bash
# on macOS or linux:
source env/bin/activate

# on windows cmd:
.\env\Scripts\activate.bat

# on windows powershell:
.\env\Scripts\Activate.ps1
```

3. Install dependencies

```
pip install -r requirements.txt
```

4. Start PostgreSQL database with `dev.docker-compose.yml`

```
docker compose -f dev.docker-compose.yml up
```

5. Configure `.env` based on `.env.example`

6. Run all migrations

```
atlas migrate apply --url postgres://postgres:postgres@localhost:5433
```

7. Start server locally

```
python main.py
```

## Development

### API Documentation

FastAPI has a built-in, auto-generated Swagger UI at `/docs`. It can also be used for testing requests while developing locally.

### Creating migrations

To make changes to the current schema, modify the `schema.sql` file as needed. Run the command below to generate the migration file for the schema change.

```bash
atlas migrate diff <name_of_the_migration> --dev-url docker://postgres/16/dev --to file://schema.sql
```

A new migration file will be generated under the `migrations` directory. Sometimes, the generated migration file doesn't contain the migration that we want (e.g. accidentally adding a new value to an enum instead of renaming it). You can edit the generated migration file manually in this case.

If you edited the migration file manually, run the following to tell Atlas of the change and update its hash on `migrations/atlas.sum`.

```bash
atlas migrate hash
```

### Applying migrations

To apply your migrations to your local database, run the command below.

```bash
atlas migrate apply --url postgres://postgres:postgres@localhost:5433
```

Or this if you face ssl errors

```bash
atlas migrate apply --url postgres://postgres:postgres@localhost:5433?sslmode=disable
```

### Accessing Centralized Logs

We use VictoriaLogs and Promtail to extract our logs (assume that the main server is running on a Docker container).
To access it, visit `{HOST_URL}:9428/select/vmui`. This browser request goes through the `vmauth` container acting as a proxy
for `victorialogs` container. The credentials are the environment variables `VMAUTH_USERNAME` and `VMAUTH_PASSWORD` (see `.env.example`).

### Fixing team_id not found
```sql
INSERT INTO workspace_data (id, team_id, access_token)
VALUES (gen_random_uuid(), '<team_id>', 'xoxb-<your-token>');
```