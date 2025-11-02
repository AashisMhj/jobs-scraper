import scrapy
from slugify import slugify


class KumarijobSpider(scrapy.Spider):
    name = "kumarijob"
    allowed_domains = ["kumarijob.com"]
    start_urls = ["https://www.kumarijob.com/job-listing"]

    def parse(self, response):
        categories = response.css('.nav-link.static_category_name')
        yield from response.follow_all(categories, self.parseCategoryPage)

    def parseCategoryPage(self, response):
        posts = response.css('.job-card-body h2 a')
        yield from response.follow_all(posts, self.parseDetail)

    
    def parseDetail(self, response):

        def getRowValueByLabel(label):
            rows = response.css('.job-detail-box li.row')
            for row in rows:
                if row.css('.basic-item__left::text').get() == label:
                    return row.css('.basic-item__right::text').get().replace(",", "|")                
            return None
        yield {
            'company-name': response.css('.company-name::text').get(),
            'location': getRowValueByLabel('Location'),
            'company-image': response.css('.company-logo img::attr(src)').get(),
            'company-website': None,
            'job-title': response.css('h1.d-flex span::text').get(),
            'position': None,
            'level': getRowValueByLabel('Job Level'),
            'experience': getRowValueByLabel('Experience'),
            'total-position': getRowValueByLabel('No. of Openings'),
            'job-type': getRowValueByLabel('Category'),
            'salary': getRowValueByLabel('Salary'),
            'education': getRowValueByLabel('Eduction Level'),
            'desired-gender': getRowValueByLabel('Desired Candidate'),
            'skills': getRowValueByLabel('Skills'),
            'type': getRowValueByLabel('Job Type'),
            'preferred-shift': None,
            'deadline':getRowValueByLabel('Expiry date'),
            'description': response.css('.job-description-wrap').get(),
            'job-specification': None,
            'url': response.url,
            'slug': slugify(response.css('h1.d-flex span::text').get()),
            'posted-at': None,
            'view-count': None,
            'category': getRowValueByLabel('Category'),
            'expired': getRowValueByLabel('Expiry Date')
        }
