# Substack Scraper

A robust Python tool to archive Substack newsletters you are subscribed to. It downloads posts as offline-viewable HTML files, handling authentication, rate limiting, and custom domains.

## Features

- **Full Archive Access**: Scrapes all posts from a newsletter archive.
- **Paid Content Support**: Handles authentication to download subscriber-only posts.
- **Custom Domain Support**: Includes a login helper to bypass bot protection on custom domains (e.g., `lennysnewsletter.com`).
- **Podcast Skipping**: Option to skip podcast/audio episodes (`--skip-podcasts`).
- **HTML Export**: Saves clean, readable HTML files with images embedded (or linked).
- **Rate Limiting**: Polite scraping with built-in delays.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/substack-scraper.git
    cd substack-scraper
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright browsers:**
    (Required for the login helper)
    ```bash
    playwright install chromium
    ```

## Authentication

Substack uses complex "bot protection" for some domains. This tool provides a **Login Helper** (`login.py`) to make authentication easy.

### Method A: Standard Substacks (e.g., `name.substack.com`)
For most newsletters, you only need to log in once.

1.  Run:
    ```bash
    python login.py
    ```
2.  A Chrome window will open. Log in to `substack.com`.
3.  Press **Enter** in your terminal.
4.  This creates `substack_session.json`, which works for **all** standard Substack newsletters.

### Method B: Custom Domains (e.g., `robkhenderson.com`, `lennysnewsletter.com`)
Newsletters with their own domains are isolated "islands" and require their own login.

1.  Run the helper with the URL:
    ```bash
    python login.py https://www.lennysnewsletter.com
    ```
2.  Log in to that specific site in the popup window.
3.  Press **Enter**.
4.  This saves a domain-specific session (e.g., `substack_session_www.lennysnewsletter.com.json`) which the scraper will automatically detect and use.

## Usage

**Basic Scrape:**
```bash
python scraper.py --url https://read.substack.com
```

**Skip Podcasts:**
```bash
python scraper.py --url https://newsletter.pragmaticengineer.com --skip-podcasts
```

**Limit Number of Posts:**
```bash
# Download only the 5 most recent posts
python scraper.py --url https://www.robkhenderson.com --limit 5
```

## Output

Downloaded posts are saved in the `archive/` directory, organized by domain:

```
archive/
├── read.substack.com/
│   ├── 2023-10-01_some-post-title.html
│   └── ...
└── www.robkhenderson.com/
    ├── 2025-11-27_scarcity-and-gratitude.html
    └── ...
```

## Disclaimer

This tool is for personal archiving purposes only. Please respect the copyright of the authors and do not undistribute paid content.
