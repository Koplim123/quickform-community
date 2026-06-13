# AGENTS.md

This file provides guidance to the AI agent when working with code in this repository.

## Running the app

```bash
pip install -r src/requirements.txt
python src/run.py          # debug mode, port 5001
```

No test suite or linting setup exists. Do not add tests or CI unless asked.

## Configuration (two layers)

- `config.json` (project root) — general settings (APP_NAME, DEBUG, HOST, PORT, LOG_LEVEL, ALLOWED_EXTENSIONS)
- `src/.env` — secrets (SECRET_KEY, DATABASE_URL). `.env` overrides `config.json` via `readEnv()`.
- All config is loaded in `src/quickform/config.py`. Do not add config reads elsewhere.

## Architecture

- Flask app factory: `create_app()` in `src/quickform/__init__.py`
- Routes are blueprints registered in `src/quickform/routes/__init__.py`. New blueprints must be added there.
- Database: SQLAlchemy with raw engine + `SessionLocal` (not Flask-SQLAlchemy). Models in `models.py` auto-create tables on import via `Base.metadata.create_all(engine)`.
- Templates: `src/templates/` (Jinja2). Static: `src/static/`.
- AI service calls (`ai_service.py`) support OpenAI, Anthropic, and Gemini API formats.

## Commit style

Conventional Commits: `feat(scope): message`, `refactor!: message`, `chore: message`. Follow this pattern.

## Language

Code comments and docstrings are in Chinese. Keep this convention when adding comments.
