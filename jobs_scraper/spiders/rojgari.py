import scrapy
from slugify import slugify

API = "https://api.rojgari.com/api/v1/job/search"
PAGE_SIZE = 1000


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


def humanize(value):
    """Turn the API's enum slugs ('senior_level') into labels ('Senior Level')."""
    text = clean(value)
    return text.replace('_', ' ').title() if text else None


class RojgariSpider(scrapy.Spider):
    name = "rojgari"
    allowed_domains = ["rojgari.com"]
    start_urls = [f"{API}/?limit={PAGE_SIZE}"]

    def parse(self, response):
        data = response.json()

        for post in data.get('results') or []:
            slug = clean(post.get('slug'))
            if not slug:
                continue
            # The trailing slash matters; without it every request is a 301.
            yield response.follow(f"{API}/{slug}/", self.parseDetail)

        if data.get('next'):
            yield response.follow(data['next'], self.parse)

    def parseDetail(self, response):
        data = response.json()
        title = clean(data.get('job_title'))
        organization = data.get('organization') or {}
        setting = data.get('setting') or {}

        yield {
            'company-name': clean(organization.get('name')),
            'location': join(
                location.get('full_address') for location in data.get('job_locations') or []
            ),
            'company-image': clean(organization.get('logo')),
            'company-website': None,
            'job-title': title,
            'position': None,
            'level': humanize(data.get('job_level')),
            'experience': self.experience(setting),
            'total-position': data.get('vacancies'),
            'job-type': join(humanize(kind) for kind in data.get('available_for') or []),
            'salary': clean(data.get('offered_salary')),
            'education': clean(data.get('education_level')),
            # gender is present but null whenever the job is not gender specific.
            'desired-gender': clean(setting.get('gender')) or 'Both',
            'skills': join(data.get('skills')),
            'type': None,
            'preferred-shift': clean(data.get('preferred_shift')),
            'deadline': clean(data.get('deadline')),
            'description': clean(data.get('description')),
            'job-specification': clean(data.get('specification')),
            'url': response.url,
            'slug': slugify(title) if title else None,
            'posted-at': clean(data.get('posted_at')),
            'view-count': data.get('hit_count'),
            'category': join(
                category.get('name') for category in data.get('categories') or []
            ),
            'expired': data.get('is_expired'),
        }

    def experience(self, setting):
        """Experience arrives as a month count, which reads poorly on its own."""
        months = setting.get('min_experience_months')
        if not months:
            return None
        if months % 12:
            return f"{months} months"
        years = months // 12
        return f"{years} year" if years == 1 else f"{years} years"
