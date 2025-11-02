import scrapy
from slugify import slugify
from urllib.parse import urlparse, parse_qs


class JobssniperSpider(scrapy.Spider):
    name = "jobssniper"
    allowed_domains = ["www.jobssniper.com"]
    start_urls = ["https://www.jobssniper.com/api/search?page=1"]

    def parse(self, response):
        resJson = response.json()
        posts = resJson['results']
        self.logger.info(posts)
        for post in posts:
            yield response.follow(f"https://www.jobssniper.com/jobs/{post.get('slug')}", self.parseDetail,meta=post )
        nextUrl = resJson.get('next')
        if nextUrl:
            parsed = urlparse(nextUrl)
            params = parse_qs(parsed.query)
            page = params.get('page')[0]
            yield response.follow(f"https://www.jobssniper.com/api/search?page={page}", self.parse)

    def parseDetail(self, response):
        def getValueByLabel(label):
            items = response.css('div[data-baseweb="flex-grid-item"]')
            for item in items:
                itemLabel = item.css('div[data-baseweb="typo-labelsmall"].ca').get()
                if itemLabel == label:
                    return item.css('div[data-baseweb="typo-labelxsmall"].gx').get
                
            return None
        
        yield {
            'company-name': response.meta.get('organization_name')[0].get('organization_name'),
            'location': response.meta.get('job_location'),
            'company-image': response.meta.get('logo'),
            'company-website': None,
            'job-title': response.meta.get('title_of_job'),
            'position': None,
            'level': response.meta.get('job_level'),
            'experience': response.meta.get('experience_required'),
            'total-position': response.meta.get('required_number_of_employee'),
            'job-type': response.meta.get('kind_of_jobs'),
            # 'salary': getValueByLabel('Offered Salary'),
            'salary': f"{response.meta.get('salary_type')} {response.meta.get('initial_salary') if response.meta.get('initial_salary') else ''} {response.meta.get('maximum_salary') if response.meta.get('maximum_salary') else ''}",
            'education': response.meta.get('preferred_education'),
            'desired-gender': response.meta.get('gender'),
            'skills': None,
            'type': None,
            'preferred-shift': None,
            'deadline':response.meta.get('deadline'),
            'description': response.css('.jobdetail_detail__3-93y div.ae.bz')[0].get(),
            'job-specification': response.css('.jobdetail_detail__3-93y div.ae.bz')[1].get(),
            'url': response.url,
            'slug': slugify(response.meta.get('title_of_job')),
            'posted-at': response.meta.get('post_date'),
            'view-count': response.meta.get('views_count'),
            'category': getValueByLabel('Category'),
            'expired': response.meta.get('expired'),
        }
