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
        yield {
            'company_name': response.css('div#short-description strong::text').get(),
            'location': response.css('div.card-body table tr')[4].css('td span::text').get() if len(response.css('div.card-body table tr')) >=5 else '' ,
            'image': response.css('div.media img::attr(src)').get(),
            'website': '',
            'job-title': response.css('div.card-header h1::text').get(),
            'position': '',
            'level': response.css('div.card-body table tr')[1].css('td a::text').get() if len(response.css('div.card-body table tr')) >= 2 else '',
            'experience': response.css('div.card-body table tr')[8].css('td span::text').get() if len(response.css('div.card-body table tr')) >=8 else '',
            'total-position': response.css('div.card-body table tr')[2].css('strong::text').get() if len(response.css('div.card-body table tr')) >= 3 else '',
            'job-type': response.css('div.card-body table tr')[3].css('td::text').getall()[2] if len(response.css('div.card-body table tr')) >= 4 else '',
            'salary': response.css('div.card-body table tr')[5].css('td::text').getall()[2] if len(response.css('div.card-body table tr')) >= 6 else '',
            'education': response.css('div.card-body table tr')[7].css('span::text').get() if len(response.css('div.card-body table tr')) >= 8 else '',
            'type': '',
            'deadline':response.css('div.card-body table tr')[6].css('td::text').getall()[2] if len(response.css('div.card-body table tr')) else '',
            'description': response.css('div[itemprop=description]').get(),
            'url': response.url,
            'slug': slugify(response.css('div.card-header h1::text').get())
        }
