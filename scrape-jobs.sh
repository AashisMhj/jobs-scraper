#!/usr/bin/env bash
source .venv/bin/activate

log=$(mktemp)
trap 'rm -f "$log"' EXIT

for spider in jobaxle jobsnepal jobssniper kumarijob merojob rojgari vocalpanda; do
    scrapy crawl "$spider" --loglevel=WARNING 2>&1 | tee -a "$log"
done

# A spider whose site changed still exits cleanly, so the run is judged on what
# the health check pipeline reported rather than on scrapy's exit status.
if grep -q "HEALTH CHECK FAILED" "$log"; then
    echo
    echo "Some spiders stopped collecting:" >&2
    grep "HEALTH CHECK FAILED" "$log" >&2
    exit 1
fi
