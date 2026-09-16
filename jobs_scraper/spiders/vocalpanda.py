import json
import scrapy
from datetime import datetime
from slugify import slugify
from urllib.parse import quote

SITE = "https://www.vocalpanda.com"
API = "https://prod.vocalpanda.com/api/getFindAJobMultipleSearchCriteria"
LOGOS = "https://jobportal-prod-bucket.s3.amazonaws.com/uploads/portal/"
PAGE_SIZE = 1000

# The site ships this lookup in its own bundle; the API only returns the key.
JOB_LEVELS = {
    '1': "Entry Level",
    '2': "Intern",
    '3': "Junior",
    '4': "Associate",
    '5': "Mid Level",
    '6': "Senior",
}

EXPERIENCE = {
    'eq': "{years}",
    'gte': "{years}+",
    'gt': "more than {years}",
    'lte': "up to {years}",
    'lt': "less than {years}",
}


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


class VocalpandaSpider(scrapy.Spider):
    name = "vocalpanda"
    allowed_domains = ["vocalpanda.com"]

    def searchRequest(self, page):
        payload = {
            "slug": None,
            "id": 0,
            "address_lat": 27.6894,
            "address_lng": 85.3227,
            "work_mode": "",
            "job_type": "",
            "experience": 0,
            "job_location_lat_set": "",
            "job_location_lng_set": "",
            "job_category": "",
            "job_title_set": "",
            "education_degree_set": "",
            "salary_from": 0,
            "salary_to": 0,
            "page_number": page,
            "page_size": PAGE_SIZE,
            "salary_type": None,
        }
        return scrapy.Request(
            url=API,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Origin": SITE,
                "Referer": f"{SITE}/find-a-job",
            },
            body=json.dumps(payload),
            callback=self.parse,
            cb_kwargs={'page': page},
        )

    async def start(self):
        yield self.searchRequest(1)

    def parse(self, response, page):
        data = response.json().get('response') or {}
        posts = data.get('job_list') or []
        for post in posts:
            yield self.job(post)

        if posts and page * PAGE_SIZE < (data.get('count') or 0):
            yield self.searchRequest(page + 1)

    def job(self, post):
        title = clean(post.get('job_title'))
        logo = clean(post.get('logo'))

        return {
            'company-name': clean(post.get('first_name')),
            'location': clean(post.get('job_location')),
            'company-image': f"{LOGOS}{quote(logo)}" if logo else None,
            'company-website': None,
            'job-title': title,
            'position': None,
            'level': JOB_LEVELS.get(clean(post.get('job_level'))),
            'experience': self.experience(post),
            'total-position': post.get('req_no_of_employes'),
            'job-type': clean(post.get('job_type_name')),
            'salary': self.salary(post),
            'education': clean(post.get('education')),
            'desired-gender': None,
            'skills': None,
            'type': "Remote" if post.get('is_remote') else "On-site",
            'preferred-shift': None,
            'deadline': clean(post.get('deadline')),
            'description': clean(post.get('job_description')),
            'job-specification': None,
            'url': self.jobUrl(post, title),
            'slug': slugify(title) if title else None,
            'posted-at': clean(post.get('created_date')),
            'view-count': post.get('count'),
            # job_category is only returned as a numeric key, and the site
            # exposes no lookup that names it.
            'category': None,
            'expired': self.expired(post.get('deadline')),
        }

    def jobUrl(self, post, title):
        jobId = clean(post.get('job_id'))
        if not jobId:
            return SITE
        return f"{SITE}/{slugify(title)}-{jobId}" if title else f"{SITE}/{jobId}"

    def experience(self, post):
        years = clean(post.get('experience'))
        # A zero year requirement leaves the comparison operator meaningless.
        if years is None or not float(years):
            return None
        unit = "year" if years == '1' else "years"
        template = EXPERIENCE.get(clean(post.get('experience_type')), "{years}")
        return f"{template.format(years=years)} {unit}"

    def salary(self, post):
        figures = join([post.get('salary_from'), post.get('salary_to')], " - ")
        # Without figures the API only states how the salary is set.
        return figures or clean(post.get('offered_salary'))

    def expired(self, deadline):
        deadline = clean(deadline)
        if not deadline:
            return None
        try:
            end = datetime.strptime(deadline[:10], '%Y-%m-%d').date()
        except ValueError:
            return None
        return end < datetime.now().date()
