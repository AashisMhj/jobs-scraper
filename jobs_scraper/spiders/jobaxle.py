import scrapy
from datetime import datetime, timezone
from slugify import slugify
from urllib.parse import quote

API = "https://jobaxle.com/api"
PAGE_SIZE = 100


def clean(value):
    """Return a stripped string, or None for the API's empty strings and nulls."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def title_of(node):
    """Read the 'title' of a lookup object that the API sometimes returns as null."""
    return clean(node.get('title')) if isinstance(node, dict) else None


def join(values, separator=" | "):
    cleaned = [clean(value) for value in values or []]
    cleaned = [value for value in cleaned if value]
    return separator.join(cleaned) or None


class JobaxleSpider(scrapy.Spider):
    name = "jobaxle"
    allowed_domains = ["jobaxle.com"]
    start_urls = [f"{API}/search?page=1&limit={PAGE_SIZE}"]

    def parse(self, response):
        data = response.json()['data']

        for row in data['rows']:
            slug = clean(row.get('slug'))
            if not slug:
                continue
            yield response.follow(
                f"{API}/jobdetails/{slug}",
                self.parseDetail,
                # posted-at is only on the search row, not on the detail response.
                meta={'posted-at': row.get('createdAt')},
            )

        page = data.get('currentPage') or 1
        if page < (data.get('totalPages') or 1):
            yield response.follow(f"{API}/search?page={page + 1}&limit={PAGE_SIZE}", self.parse)

    def parseDetail(self, response):
        data = response.json()['data']['jobDetail']
        title = clean(data.get('jobTitle'))

        yield {
            'company-name': clean(data.get('member', {}).get('fullName')),
            'location': join(data.get('locationTitles')),
            'company-image': self.companyImage(data),
            'company-website': None,
            'job-title': title,
            'position': None,
            'level': title_of(data.get('joblevel')),
            'experience': self.experience(data),
            'total-position': data.get('noOfVacancy'),
            'job-type': title_of(data.get('jobtype')),
            'salary': self.salary(data),
            'education': title_of(data.get('educationlevel')),
            'desired-gender': clean(data.get('gender')),
            'skills': join(data.get('skillTitles')),
            'type': clean(data.get('workNature')),
            'preferred-shift': None,
            'deadline': clean(data.get('deadlineEndDate')),
            'description': clean(data.get('jobDescription')),
            'job-specification': clean(data.get('jobSpecification')),
            'url': response.url,
            'slug': slugify(title) if title else None,
            'posted-at': clean(response.meta.get('posted-at')),
            'view-count': data.get('views'),
            'category': title_of(data.get('jobcategory')),
            'expired': self.expired(data),
        }

    def companyImage(self, data):
        """Logo filenames can contain spaces, so they have to be encoded into the path."""
        filename = clean(data.get('member', {}).get('profileImage'))
        if not filename:
            return None
        return f"{API}/image/company_logo/{quote(filename)}"

    def experience(self, data):
        years = join([data.get('minExperience'), data.get('maxExperience')], " - ")
        # Jobs open to freshers carry no numbers, only the experienceType flag.
        return years or clean(data.get('experienceType'))

    def salary(self, data):
        salaryType = clean(data.get('salaryType'))
        amount = join([data.get('minSalary'), data.get('maxSalary')], " - ")
        if not amount:
            return salaryType
        parts = [clean(data.get('currency')), amount, clean(data.get('salaryUnit')), salaryType]
        return " ".join(part for part in parts if part)

    def expired(self, data):
        if clean(data.get('status')) not in (None, 'Live'):
            return True
        deadline = clean(data.get('deadlineEndDate'))
        if not deadline:
            return None
        try:
            end = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        except ValueError:
            return None
        return end < datetime.now(timezone.utc)
