import scrapy
from slugify import slugify

class JobsnepalSpider(scrapy.Spider):
    name = "jobsnepal"
    allowed_domains = ["www.jobsnepal.com"]
    start_urls = ["https://www.jobsnepal.com/jobs"]

    def parse(self, response):
        posts = response.css('div.card div.card-body > a')
        yield from response.follow_all(posts, self.parseDetail)

        next_page = response.css('[aria-label="Next &raquo;"]::attr(href)')
        if next_page:
            next_page_link = next_page.get()
            yield response.follow(next_page_link, self.parse)


    def parseDetail(self, response):
        jobDetail = response.css('div.job-details')
        jobOverview = response.css('div.job-overview-inner table tr')
        job_overview_length = len(jobOverview)

        def getOverviewItem(label:str):
            table_rows = jobOverview.css('tr')
            for row in table_rows:
                r = row.css('td')
                if r[0].css('::text').get().strip() == label:
                    return " ".join(r[1].css("*::text").getall())
            return None

        yield{
            'company-name': response.css('div.company-title::text').get(),
            'location': response.css('tr[itemprop=jobLocation] a span::text').get(),
            'company-image': response.css('div.company-logo img::attr(src)').get(),
            'company-website': None,
            'job-title': jobDetail.css('h1::text').get(),
            'position': None,
            'level': getOverviewItem('Level'),
            'experience': getOverviewItem('Experience'),
            'total-position': getOverviewItem('Openings'),
            'job-type': getOverviewItem('Position Type'),
            'salary': None,
            'education': getOverviewItem('Education'),
            'desired-gender': None,
            'skills': None,
            'type': None,
            'preferred-shift': None,
            'deadline': response.css('span.apply-deadline::text').get(),
            'description': response.css('span[itemprop=description]').get(),
            'job-specification': None,
            'url': response.url,
            'slug': slugify(jobDetail.css('h1::text').get()),
            'posted-at': getOverviewItem('Posted Date'),
            'view-count': None,
            'category': None,
            'expired': None
        }