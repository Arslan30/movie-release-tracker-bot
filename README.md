# Movie Release Tracker Bot

A Telegram bot that tracks upcoming movie releases, digital releases, Blu-ray releases, and TV episodes using TMDB.

Instead of manually checking release dates, users can search for movies or TV shows, track them, and receive notifications when new releases become available.

## Features

### Movie Tracking

* Search movies
* View posters and detailed information
* Track movies
* View upcoming releases
* Receive theatrical release notifications
* Receive digital release notifications
* Receive Blu-ray / physical release notifications

### TV Show Tracking

* Search TV shows
* View posters and detailed information
* Track TV shows
* View upcoming episodes
* Receive episode release notifications

### Additional Features

* Upcoming releases overview
* Upcoming TV episode overview
* One-click tracking from search results
* TMDB-powered metadata and posters

## Commands

| Command               | Description                  |
| --------------------- | ---------------------------- |
| `/search`             | Search for movies            |
| `/searchtv`           | Search for TV shows          |
| `/mymovies`           | View tracked movies          |
| `/myshows`            | View tracked TV shows        |
| `/comingsoon`         | View upcoming movie releases |
| `/upcomingshows`      | View upcoming TV episodes    |
| `/subscribe_movies`   | Enable movie notifications   |
| `/unsubscribe_movies` | Disable movie notifications  |
| `/subscribe_tv`       | Enable TV notifications      |
| `/unsubscribe_tv`     | Disable TV notifications     |
| `/start`              | Show help message            |

## Screenshots

Add screenshots here after publishing.

## Installation

### Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/movie-release-tracker-bot.git
cd movie-release-tracker-bot
```

### Create Virtual Environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file:

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
TMDB_API_KEY=YOUR_TMDB_API_KEY
```

### Run the Bot

```bash
python bot.py
```

### Run Daily Notifications

```bash
python daily_check.py
```

## Project Structure

```text
bot.py
database.py
tmdb_client.py
release_checker.py
tv_checker.py
daily_check.py

requirements.txt
README.md
.env.example
.gitignore
```

## Data Source

This project uses data provided by The Movie Database (TMDB).

https://www.themoviedb.org/

## License

MIT
