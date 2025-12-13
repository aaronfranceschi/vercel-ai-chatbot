# MET OpenAccess Image Harvester — Example Project

An extensible Python project for large-scale harvesting of public-domain images referenced in the MET OpenAccess dataset. This repository contains a starter implementation with concurrency, retries, optional per-host rate-limiting, and CSV reporting.

Disclaimer
-- This repository is provided as an example implementation that is similar to requirements some organizations may request, but it is not a client-specific deliverable. Customize and extend it to match your project's policies and operational requirements.

Key features
- Read CSV input from local path or remote URL
- Filter rows by the `Public Domain` column
- Visit object pages (from `Link Resource`) and extract image URLs (prefers `og:image`)
- Concurrent downloads with retries and resumable temporary files
- Optional per-host throttling to avoid overwhelming servers
- CSV reporting of successes and failures

Requirements
- Python 3.8+
- See `requirements.txt`

Quick start

1. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the harvester (example downloading first 100 public-domain items):

```bash
python main.py --csv https://github.com/metmuseum/openaccess/raw/master/MetObjects.csv --out images --workers 12 --max 100 --delay 0.5 --report report.csv
```

Advanced notes
- Use `--delay` to configure a per-host minimum delay between requests (seconds).
- For very large runs, enable smaller worker counts and larger `--delay` to be polite to origin servers.
- Respect `robots.txt` and the dataset license — this tool is intended for public-domain assets only.

Repository files
- [downloader.py](downloader.py): core logic for CSV parsing, HTML scraping and downloading
- [main.py](main.py): CLI wrapper and argument parsing
- [rate_limiter.py](rate_limiter.py): simple per-host delay implementation
- [reporter.py](reporter.py): CSV reporting helper
- [requirements.txt](requirements.txt): Python deps

If you'd like further enhancements I can add: robust per-host queueing, S3 upload support, more resilient HTML parsing rules, or a web dashboard for monitoring large harvests.
