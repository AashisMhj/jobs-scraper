import json
import re
import scrapy
from slugify import slugify
from urllib.parse import quote

SITE = "https://www.jobssniper.com"
NEXT_DATA = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.S
)


def clean(value):
    """Return a stripped string, or None for empty strings and nulls."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def join(values, separator=" | "):
    cleaned = [clean(value) for value in values or []]
    cleaned = [value for value in cleaned if value]
    return separator.join(cleaned) or None


def unwrap(entries, key):
    """Read a value the API wraps in a single-entry list of dicts."""
    for entry in entries or []:
        if isinstance(entry, dict) and clean(entry.get(key)):
            return clean(entry.get(key))
    return None


class JobssniperSpider(scrapy.Spider):
    name = "jobssniper"
    allowed_domains = ["www.jobssniper.com"]
    start_urls = [f"{SITE}/api/search?page=1"]

    def parse(self, response):
        data = response.json()
        results = data.get('results') or []

        for post in results:
            slug = clean(post.get('slug'))
            if not slug:
                continue
            yield response.follow(
                f"{SITE}/jobs/{slug}",
                self.parseDetail,
                # Nested under one key so post fields cannot collide with
                # Scrapy's own reserved meta keys.
                meta={'post': post},
            )

        # 'next' points at the upstream api.jobssniper.com host, which is outside
        # allowed_domains, so only its page number is reused.
        if results and data.get('next'):
            page = (data.get('current') or 0) + 1
            yield response.follow(f"{SITE}/api/search?page={page}", self.parse)

    def parseDetail(self, response):
        post = response.meta['post']
        # The search row carries fields the detail payload omits (notably
        # 'expired'), so the richer detail overlays it rather than replacing it.
        data = {**post, **(self.jobDetail(response) or {})}
        title = clean(data.get('title_of_job'))

        yield {
            'company-name': unwrap(data.get('organization_name'), 'organization_name'),
            'location': clean(data.get('job_location')),
            'company-image': self.companyImage(data),
            'company-website': None,
            'job-title': title,
            'position': None,
            'level': clean(data.get('job_level')),
            'experience': clean(data.get('experience_required')),
            'total-position': data.get('required_number_of_employee'),
            'job-type': clean(data.get('kind_of_jobs')),
            'salary': self.salary(data),
            'education': clean(data.get('preferred_education')),
            'desired-gender': clean(data.get('gender')),
            'skills': None,
            'type': None,
            'preferred-shift': None,
            'deadline': clean(data.get('deadline')),
            'description': clean(data.get('job_description')),
            'job-specification': clean(data.get('job_specification')),
            'url': response.url,
            'slug': slugify(title) if title else None,
            'posted-at': clean(data.get('post_date')),
            'view-count': data.get('views_count'),
            # job_category is only exposed as a numeric id with no public
            # endpoint mapping it to a name.
            'category': None,
            'expired': data.get('expired'),
        }

    def jobDetail(self, response):
        """Read the job out of the page's Next.js payload.

        The rendered markup only offers build-hashed class names, which change
        whenever the site is rebuilt.
        """
        match = NEXT_DATA.search(response.text)
        if not match:
            self.logger.warning("No __NEXT_DATA__ payload on %s", response.url)
            return None
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            self.logger.warning("Unreadable __NEXT_DATA__ payload on %s", response.url)
            return None
        return payload.get('props', {}).get('pageProps', {}).get('jobDetail')

    def companyImage(self, data):
        """Logo paths are relative and usually contain unescaped spaces."""
        path = clean(data.get('logo'))
        if not path:
            return None
        # safe='/%' keeps already-escaped paths from being escaped twice.
        return f"{SITE}{quote(path, safe='/%')}"

    def salary(self, data):
        salaryType = clean(data.get('salary_type'))
        amount = join([data.get('initial_salary'), data.get('maximum_salary')], " - ")
        amount = amount or clean(data.get('salary_amount'))
        if not amount:
            return salaryType
        parts = [
            clean(data.get('salary_currency')),
            amount,
            clean(data.get('salary_basis')),
            salaryType,
        ]
        return " ".join(part for part in parts if part)
