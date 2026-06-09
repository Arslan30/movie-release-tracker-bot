# Movie Release Tracker Bot

A Telegram bot that tracks upcoming movie releases, digital releases, Blu-ray releases, and TV episodes using TMDB.

Instead of manually checking release dates, users can search for movies or TV shows, track them, and receive notifications when new releases become available.

## Features

### Movie Tracking
- Search movies
- View posters and detailed information
- Track movies
- View upcoming releases
- Receive theatrical, digital, and Blu-ray release notifications

### TV Show Tracking
- Search TV shows
- View posters and detailed information
- Track TV shows
- View upcoming episodes
- Receive episode release notifications

### Additional Features
- Today's releases overview (`/today`)
- Releases on a specific date (`/date`)
- One-click tracking from search results
- TMDB-powered metadata and posters

## Commands

| Command               | Description                        |
| --------------------- | ---------------------------------- |
| `/search <title>`     | Search for movies                  |
| `/searchtv <title>`   | Search for TV shows                |
| `/mymovies`           | View tracked movies                |
| `/myshows`            | View tracked TV shows              |
| `/comingsoon`         | View upcoming movie releases       |
| `/upcomingshows`      | View upcoming TV episodes          |
| `/today`              | Movies releasing today             |
| `/date YYYY-MM-DD`    | Movies releasing on a given date   |
| `/subscribe_movies`   | Enable movie notifications         |
| `/unsubscribe_movies` | Disable movie notifications        |
| `/subscribe_tv`       | Enable TV notifications            |
| `/unsubscribe_tv`     | Disable TV notifications           |
| `/start`              | Show help message                  |
| `/ping`               | Health check                       |

## Installation

### Clone Repository

```bash
git clone https://github.com/Arslan30/movie-release-tracker-bot.git
cd movie-release-tracker-bot
```

### Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
TMDB_API_KEY=YOUR_TMDB_API_KEY
```

### Run the Bot

```bash
python bot.py
```

### Run Daily Notifications

Run manually:

```bash
python daily_check.py
```

Or schedule via cron (runs at 9:00 AM daily):

```cron
0 9 * * * /path/to/venv/bin/python /path/to/daily_check.py
```

Or as a systemd timer — see the [Deployment](#deployment) section below.

## Project Structure

```
bot.py                  — Telegram bot (commands, callbacks)
config.py               — Environment variable loading
database.py             — SQLite data layer (WAL mode, context manager)
tmdb_client.py          — TMDB API client (session with retry)
release_checker.py      — Movie notification logic
tv_checker.py           — TV notification logic
daily_check.py          — Entry point for scheduled daily run

requirements.txt
README.md
.env.example
.gitignore
Tests/
  test_tmdb.py
  test_release_dates.py
```

## Deployment

### systemd (recommended for Linux servers)

Create `/etc/systemd/system/movie-bot.service`:

```ini
[Unit]
Description=Movie Release Tracker Bot
After=network.target

[Service]
User=youruser
WorkingDirectory=/path/to/movie-release-tracker-bot
ExecStart=/path/to/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/movie-bot-daily.service`:

```ini
[Unit]
Description=Movie Release Daily Check

[Service]
User=youruser
WorkingDirectory=/path/to/movie-release-tracker-bot
ExecStart=/path/to/venv/bin/python daily_check.py
```

Create `/etc/systemd/system/movie-bot-daily.timer`:

```ini
[Unit]
Description=Run Movie Release Daily Check at 9AM

[Timer]
OnCalendar=*-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:

```bash
systemctl enable --now movie-bot.service
systemctl enable --now movie-bot-daily.timer
```

## Data Source

This project uses data provided by [The Movie Database (TMDB)](https://www.themoviedb.org/).

## License

MIT
