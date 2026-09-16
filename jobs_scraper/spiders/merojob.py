import scrapy
from datetime import datetime, timezone
from slugify import slugify

SITE = "https://merojob.com"
API = "https://api.merojob.com/api/v1/jobs"


def clean(value):
    """Return a stripped string, or None for empty strings and nulls."""
    if value is None:
        return None
    text = str(value).strip()
    # The API writes the literal string "None" into some free text fields.
    return text if text and text != 'None' else None


def join(values, separator=" | "):
    cleaned = [clean(value) for value in values or []]
    cleaned = [value for value in cleaned if value]
    return separator.join(cleaned) or None


def amount(value):
    """Salary figures arrive as floats, so 45000.0 would render with a .0."""
    if value in (None, ''):
        return None
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)


class MerojobComSpider(scrapy.Spider):
    name = "merojob"
    allowed_domains = ["merojob.com"]
    start_urls = [f"{API}/"]

    def parse(self, response):
        data = response.json()

        for post in data.get('results') or []:
            if post.get('id') is None:
                continue
            yield response.follow(f"{API}/{post['id']}/", self.parseDetail)

        if data.get('next'):
            yield response.follow(data['next'], self.parse)

    def parseDetail(self, response):
        data = response.json()
        title = clean(data.get('title'))
        client = data.get('client') or {}
        slug = clean(data.get('slug'))

        yield {
            'company-name': clean(client.get('client_name')) or clean(client.get('org_name')),
            'location': join(
                location.get('address') for location in data.get('job_locations') or []
            ),
            'company-image': self.media(data.get('logo') or {}),
            'company-website': clean(client.get('website')),
            'job-title': title,
            'position': None,
            'level': clean(data.get('job_level')),
            'experience': clean(data.get('experience_required')),
            'total-position': data.get('vacancies'),
            'job-type': join(data.get('available_for')),
            'salary': self.salary(data),
            'education': clean(data.get('education_level')),
            'desired-gender': None,
            'skills': join(data.get('skills')),
            'type': None,
            'preferred-shift': None,
            'deadline': clean(data.get('deadline')),
            'description': clean(data.get('description')),
            'job-specification': clean(data.get('specification')),
            # The public job page rather than the API endpoint it was read from.
            'url': f"{SITE}/{slug}/" if slug else response.url,
            'slug': slugify(title) if title else None,
            'posted-at': clean(data.get('posted_at')),
            'view-count': data.get('hit_count'),
            'category': join(data.get('categories')),
            'expired': self.expired(data),
        }

    def media(self, media):
        """Logo paths are relative and served from the API host."""
        url = clean(media.get('url'))
        return f"https://api.merojob.com{url}" if url else None

    def salary(self, data):
        # Employers can mark a salary private, and the site then hides it.
        if data.get('hide_salary'):
            return None
        offered = data.get('offered_salary') or {}
        figures = join([amount(offered.get('minimum')), amount(offered.get('maximum'))], " - ")
        if figures in (None, '0'):
            return None
        operator = clean(offered.get('operator'))
        parts = [
            operator if operator and operator != 'Equals' else None,
            clean(offered.get('currency')),
            figures,
            clean(offered.get('unit')),
        ]
        return " ".join(part for part in parts if part)

    def expired(self, data):
        if not data.get('is_published') or clean(data.get('status')) not in (None, 'Published'):
            return True
        deadline = clean(data.get('deadline'))
        if not deadline:
            return None
        try:
            end = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        except ValueError:
            return None
        return end < datetime.now(timezone.utc)
