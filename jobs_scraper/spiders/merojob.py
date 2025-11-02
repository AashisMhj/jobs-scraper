import scrapy
from slugify import slugify


class MerojobComSpider(scrapy.Spider):
    name = "merojob"
    allowed_domains = ["merojob.com"]
    start_urls = ["https://merojob.com/services/top-job/"]

    def parse(self, response):
        posts = response.css('div.card-body h1 a')
        yield from response.follow_all(posts, self.parseDetail)
        
        next_page = response.css('.pagination-next.page-link::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)


    def parseDetail(self, response):
        def getRowValueByLabel(label):
            rows = response.css('table.table tr')
            for row in rows:
                table_data = row.css('td')
                if table_data[0].css('::text').get() == label:
                    return " ".join(table_data[2].css('*::text').getall())
            return None
        yield {
            'company-name': response.css('div#short-description strong::text').get(),
            # 'location': response.css('div.card-body table tr')[4].css('td span::text').get() if len(response.css('div.card-body table tr')) >=5 else '' ,
            'location': getRowValueByLabel('Job Location'),
            'company-image': response.css('div.media img::attr(src)').get(),
            'company-website': None,
            'job-title': response.css('div.card-header h1::text').get(),
            'position': None,
            'level': getRowValueByLabel('Job Level'),
            'experience': getRowValueByLabel('Experience Required'),
            'total-position': getRowValueByLabel('No. of Vacancy/s'),
            'job-type': getRowValueByLabel('Employment Type'),
            'salary': getRowValueByLabel('Offered Salary'),
            'education': getRowValueByLabel('Education Level'),
            'desired-gender': None,
            'skills': getRowValueByLabel('Professional Skill Required'),
            'type': getRowValueByLabel('Employment Type'),
            'preferred-shift': None,
            'deadline':getRowValueByLabel('Apply Before(Deadline)'),
            'description': response.css('div[itemprop=description]').get(),
            'job-specification': None,
            'url': response.url,
            'slug': slugify(response.css('div.card-header h1::text').get()),
            'posted-at': None,
            'view-count': None,
            'category': getRowValueByLabel('Job Category'),
            'expired': None
        }
