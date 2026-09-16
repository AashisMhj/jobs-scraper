import json
import re
import scrapy
from datetime import datetime
from slugify import slugify

SITE = "https://www.kumarijob.com"
LISTING = f"{SITE}/job-listing"
SITEMAP = f"{SITE}/sitemap-jobs.xml"
WHITESPACE = re.compile(r'\s+')
JSON_LD = re.compile(
    r'<script[^>]*type=[\'"]application/ld\+json[\'"][^>]*>(.*?)</script>', re.S
)
# Salary cells keep their currency and pay period even when no figure is set.
SALARY_FILLER = re.compile(
    r'\b(?:Nrs|NPR|Rs)\.?|\b(?:Hourly|Daily|Weekly|Monthly|Yearly|Annually)\b', re.I
)


def squash(value):
    """Collapse the markup's newlines and padding into single spaces."""
    if value is None:
        return None
    return WHITESPACE.sub(' ', value).strip() or None


def text_of(nodes):
    return squash(' '.join(nodes.css('*::text').getall())) if nodes else None


def join(values, separator=" | "):
    cleaned = [squash(value) for value in values or []]
    cleaned = [value for value in cleaned if value]
    return separator.join(cleaned) or None


class KumarijobSpider(scrapy.Spider):
    name = "kumarijob"
    allowed_domains = ["kumarijob.com"]

    async def start(self):
        # The category pages and the sitemap each list jobs the other omits,
        # so both are crawled and the dupe filter merges them.
        yield scrapy.Request(LISTING, self.parseCategories)
        yield scrapy.Request(SITEMAP, self.parseSitemap)

    def parseCategories(self, response):
        categories = response.css('.nav-link.static_category_name')
        yield from response.follow_all(categories, self.parseCategoryPage)

    def parseCategoryPage(self, response):
        posts = response.css('.job-card-body h2 a')
        yield from response.follow_all(posts, self.parseDetail)

        next_page = response.css('[rel=next]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parseCategoryPage)

    def parseSitemap(self, response):
        selector = response.selector
        selector.remove_namespaces()
        for url in selector.css('loc::text').getall():
            yield response.follow(squash(url), self.parseDetail)

    def parseDetail(self, response):
        overview = self.overview(response)
        posting = self.posting(response)
        # Banner style listings keep the title in a child element of the h1.
        title = text_of(response.css('h1'))
        deadline = squash(posting.get('validThrough'))

        yield {
            'company-name': squash(response.css('.company-name::text').get()),
            'location': self.location(posting),
            'company-image': self.companyImage(response),
            'company-website': None,
            'job-title': title,
            'position': None,
            'level': overview.get('Job Level'),
            'experience': overview.get('Experience') or squash(posting.get('experienceRequirements')),
            'total-position': overview.get('Openings'),
            'job-type': overview.get('Job Type') or squash(posting.get('employmentType')),
            'salary': self.salary(overview.get('Salary')),
            'education': overview.get('Education'),
            'desired-gender': overview.get('Gender'),
            'skills': join(response.css('.skill-pill-tag::text').getall()),
            'type': None,
            'preferred-shift': overview.get('Job Shift'),
            'deadline': deadline,
            'description': self.section(response, 'Job Description'),
            'job-specification': self.section(response, 'Job Specification'),
            'url': response.url,
            'slug': slugify(title) if title else None,
            'posted-at': squash(posting.get('datePosted')),
            'view-count': None,
            'category': overview.get('Category'),
            'expired': self.expired(deadline),
        }

    def overview(self, response):
        """Read the label/value cards once, rather than per field."""
        rows = {}
        for card in response.css('.overview-item-card'):
            label = squash(card.css('.overview-label::text').get())
            value = squash(card.css('.overview-value::text').get())
            if label:
                rows[label] = value
        return rows

    def posting(self, response):
        """Read the schema.org JobPosting the page embeds for search engines."""
        for block in JSON_LD.findall(response.text):
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                return data
        return {}

    def location(self, posting):
        address = (posting.get('jobLocation') or {}).get('address') or {}
        parts = [squash(address.get('streetAddress')), squash(address.get('addressLocality'))]
        # The street line is the area and the locality the city; keep both.
        return ", ".join(dict.fromkeys(part for part in parts if part)) or None

    def companyImage(self, response):
        return (
            response.css('.company-logo-square img::attr(src)').get()
            or response.css('.job-detail-banner-img-holder img::attr(src)').get()
        )

    def section(self, response, heading):
        """Body sections are keyed only by their visible heading text."""
        node = response.xpath(
            f'//h5[normalize-space(text())="{heading}"]'
            '/following-sibling::div[contains(@class,"rich-text-content")][1]'
        )
        return node.get() if node else None

    def salary(self, value):
        text = squash(value)
        if not text or any(char.isdigit() for char in text):
            return text
        # No figure was given, so drop the leftover currency and period words.
        remainder = squash(SALARY_FILLER.sub(' ', text))
        return squash(remainder.strip('()')) if remainder else None

    def expired(self, deadline):
        if not deadline:
            return None
        try:
            end = datetime.strptime(deadline[:10], '%Y-%m-%d').date()
        except ValueError:
            return None
        return end < datetime.now().date()
