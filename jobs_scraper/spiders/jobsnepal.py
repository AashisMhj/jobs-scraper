import re
import scrapy
from datetime import datetime
from slugify import slugify

WHITESPACE = re.compile(r'\s+')
# Salary cells fall back to bare currency and separators when no figure is set.
EMPTY_SALARY = re.compile(r'^[\s./-]*(?:Rs\.?)?[\s./-]*$', re.I)
DANGLING_DASH = re.compile(r'(Rs\.?)\s*-\s*', re.I)


def squash(value):
    """Collapse the markup's newlines and padding into single spaces."""
    if value is None:
        return None
    text = WHITESPACE.sub(' ', value).strip()
    # The table renders multi-value fields as 'A , B , C'.
    return text.replace(' , ', ' | ') or None


class JobsnepalSpider(scrapy.Spider):
    name = "jobsnepal"
    allowed_domains = ["www.jobsnepal.com"]
    start_urls = ["https://www.jobsnepal.com/jobs"]

    def parse(self, response):
        posts = response.css('div.card div.card-body > a')
        yield from response.follow_all(posts, self.parseDetail)

        next_page = response.css('[aria-label="Next &raquo;"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parseDetail(self, response):
        overview = self.overview(response)
        title = squash(response.css('div.job-details h1::text').get())
        # validThrough is a sortable timestamp; the visible text reads
        # 'Apply before 27 Sep, 2026'.
        deadline = self.microdata(response, 'validThrough')

        yield {
            'company-name': squash(response.css('div.company-title::text').get()),
            'location': squash(response.css('tr[itemprop=jobLocation] a span::text').get()),
            'company-image': response.css('div.company-logo img::attr(src)').get(),
            'company-website': None,
            'job-title': title,
            'position': None,
            'level': overview.get('Position Level'),
            'experience': overview.get('Experience'),
            'total-position': overview.get('Openings'),
            'job-type': overview.get('Position Type') or self.microdata(response, 'employmentType'),
            'salary': self.salary(overview.get('Salary')),
            'education': overview.get('Education'),
            'desired-gender': None,
            'skills': None,
            'type': None,
            'preferred-shift': None,
            'deadline': deadline,
            'description': response.css('span[itemprop=description]').get(),
            'job-specification': None,
            'url': response.url,
            'slug': slugify(title) if title else None,
            'posted-at': self.microdata(response, 'datePosted') or overview.get('Posted Date'),
            'view-count': None,
            'category': overview.get('Category'),
            'expired': self.expired(deadline),
        }

    def overview(self, response):
        """Read the whole label/value table once, rather than per field."""
        rows = {}
        for row in response.css('div.job-overview-inner table tr'):
            cells = row.css('td')
            if len(cells) < 2:
                continue
            label = squash(cells[0].css('::text').get())
            value = squash(' '.join(cells[1].css('*::text').getall()))
            if label:
                rows[label] = value
        return rows

    def microdata(self, response, name):
        """Read a schema.org property, preferring its machine readable content."""
        node = response.css(f'[itemprop={name}]')
        if not node:
            return None
        return squash(node.attrib.get('content') or ' '.join(node.css('*::text').getall()))

    def salary(self, value):
        text = squash(value)
        if not text or EMPTY_SALARY.match(text):
            return None
        return DANGLING_DASH.sub(r'\1 ', text)

    def expired(self, deadline):
        if not deadline:
            return None
        try:
            end = datetime.strptime(deadline[:10], '%Y-%m-%d').date()
        except ValueError:
            return None
        return end < datetime.now().date()
