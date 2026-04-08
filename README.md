# Phase 1 Django Course Project

This repository contains the Phase 1 Django starter for Worndly. It includes a working app for subfeature 1.1, SQLite storage, Django admin, and the supporting documentation required for submission.

## Tech stack

- Python 3.9+
- Django 4.2
- SQLite
- Server-rendered Django templates

## Setup

1. Create the virtual environment:

```bash
python3 -m venv venv
```

2. Activate it:

```bash
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Apply migrations:

```bash
cd src
python manage.py migrate
```

5. Create an admin account:

```bash
python manage.py createsuperuser
```

6. Start the development server:

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the app and `http://127.0.0.1:8000/admin/` for Django admin.

## Current Phase 1 baseline

- Landing page with navigation and project summary
- Subfeature 1.1 implemented as player profile creation
- Django `User` stores username, email, and password
- `PlayerProfile` stores the optional player name
- Profile create, list, and detail views
- Django admin integration for stored player profiles

## Suggested team next steps

1. Add the remaining selected Phase 1 features in separate views, models, or apps as needed.
2. Decide whether later phases need login, profile editing, or stricter validation rules.
3. Capture screenshots from the running app for the report PDF.
4. Fill in `CONTRIBUTIONS.md` with each teammate's concrete work before submission.
5. Use the report outline in `src/reports/phase1_report_outline.md` to produce the required PDF.

## Running tests

From `src/`:

```bash
python manage.py test
```
