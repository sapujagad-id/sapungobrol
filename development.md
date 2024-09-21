# development.md

## Installation

1. Create a python virtual environment

```
python -m venv env
```

2. Activate the virtual environment

```
// on macOS or linux:
source env/bin/activate

// on windows:
.\venv\Scripts\activate.bat
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

6. Run all Alembic migrations

```
alembic upgrade head
```

7. Start server locally

```
fastapi dev
```

## Development

#### /docs

FastAPI has a built-in, auto-generated Swagger UI at `/docs`

#### Creating Migrations

To use Alembic to create a new migration, run `alembic revision -m "<migration message>"`

Read more: https://alembic.sqlalchemy.org/en/latest/tutorial.html

#### Downgrading Migrations

Run `alembic downgrade <migration>` where <migration> is the migration name, or `base` to down-migrate everything.