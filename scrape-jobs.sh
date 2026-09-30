#!/bin/bash
set -euo pipefail

# Resolve the directory this script lives in, regardless of where it's called from
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"

VENV_DIR="$SCRIPT_DIR/.venv"
SPIDER_DIR="$SCRIPT_DIR/jobs_scraper"


cd "$SPIDER_DIR"

for spider in jobaxle jobsnepal jobssniper kumarijob merojob rojgari vocalpanda; do
    "$VENV_DIR/bin/scrapy" crawl "$spider" --loglevel=WARNING 2>&1 | tee -a "$log"
done

# A spider whose site changed still exits cleanly, so the run is judged on what
# the health check pipeline reported rather than on scrapy's exit status.
if grep -q "HEALTH CHECK FAILED" "$log"; then
    echo
    echo "Some spiders stopped collecting:" >&2
    grep "HEALTH CHECK FAILED" "$log" >&2
    exit 1
fi
