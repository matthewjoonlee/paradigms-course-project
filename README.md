# Worndly Django Course Project

This repository contains the Django implementation of Worndly, including user profile creation, login/logout, gameplay, dashboard history, and the Feature 4.1 purchase flow for buying extra game plays with Krato$Coin.

## Tech stack

- Python 3.9+
- Django 4.2
- SQLite
- Server-rendered Django templates

## Features implemented in Phase 1
- Feature 1.1: create player profile (username, email, password, optional name)
- Feature 1.2: log in with username and password
- Feature 1.3: log out
- Feature 2.1: gameplay (language selection, word guessing, color feedback, daily limit)
- Feature 3.1: Dashboard table of prior plays with time-range filtering (week/month/year/all)
- Feature 4.1: buy extra game plays using Krato$Coin through the external REST API

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

## Local .env setup for feature 4.1

Create a local `.env` file in the repository root with:

```env
KRATOS_ACCESS_TOKEN=your_access_token_here
KRATOS_GROUP_PATH=group20/group20
```

This file is git-ignored and must be created locally by anyone running the purchase feature.

For Feature 4.1 testing, use a Worndly account whose email is `mlee55@nd.edu`, since that email is the one currently funded in the external Krato$Coin API for this repository setup.

The purchase feature uses the external API email, not the username, so the email on the Django account must match the email registered in the external REST API admin.

## How to play
1. Create a user profile at `http://127.0.0.1:8000/profiles/new/`
2. Go to `http://127.0.0.1:8000/game/` to start game
3. Select language and enter 5-letter words in 6 attempts

## Current app baseline

- Landing page with navigation and project summary
- Feature 1.1 implemented as player profile creation
- Feature 1.2 implemented as username/password login
- Feature 1.3 implemented as logout
- Feature 4.1 purchase flow for buying extra game plays with Krato$Coin
- Django `User` stores username, email, and password
- `PlayerProfile` stores the optional player name and purchased extra plays
- Profile create, list, and detail views
- Django admin integration for stored player profiles
- Feature 3.1, 3.2


## Running tests

From `src/`:

```bash
python manage.py test
```
