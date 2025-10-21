import scrapy
import json
from slugify import slugify
from scrapy_playwright.page import PageMethod
from urllib.parse import urlparse, parse_qs, unquote


class VocalpandaSpider(scrapy.Spider):
    name = "vocalpanda"
    allowed_domains = ["www.vocalpanda.com", "vocalpanda-prod-gvshg-a006ddd577b0.herokuapp.com"]

    def start_requests(self):
        url = "https://vocalpanda-prod-gvshg-a006ddd577b0.herokuapp.com/api/getFindAJobMultipleSearchCriteria"

        payload = {
            "slug": None,
            "id": 0,
            "address_lat": 27.6894,
            "address_lng": 85.3227,
            "work_mode": "",
            "job_type": "",
            "experience": 0,
            "job_location_lat_set": "",
            "job_location_lng_set": "",
            "job_category": "",
            "job_title_set": "",
            "education_degree_set": "",
            "salary_from": 0,
            "salary_to": 0,
            "page_number": 1,
            "page_size": 1000,
            "salary_type": None
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://www.vocalpanda.com",
            "Referer": "https://www.vocalpanda.com/find-a-job",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        yield scrapy.Request(
            url=url,
            meta={"playwright": True},
            method="POST",
            headers=headers,
            body=json.dumps(payload),
            callback=self.parse
        )

    def parse(self, response):
        pre_text = response.css("pre::text").get()
        self.logger.info(pre_text)
        resJson = json.loads(pre_text)
        posts = resJson['response']['job_list']
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        for post in posts:
            yield scrapy.Request(f"https://www.vocalpanda.com/{slugify(post['job_title'])}-{post['job_id']}", 
                                 meta={"playwright": True, "playwright_page_methods": [PageMethod("wait_for_selector", ".header_logo_title_section"),], "post": post}, 
                                 callback=self.parseDetail, headers=headers)


    async def parseDetail(self, response):
        def getLabelValue(label):
            items = response.css('.bottomDetailRendererList')

            for item in items:
                itemLabel = item.css('div > span.Desktop_Body4_Regular::text').get()
                if label == itemLabel:
                    return item.css(':scope > span::text').get()
            return None
        
        
        def extract_real_image_url(next_image_url:str) -> str:
            parsed = urlparse(next_image_url)
            query = parse_qs(parsed.query)
            if 'url' in query:
                return unquote(unquote(query['url'][0]))
            
            return next_image_url

        skillsEl = response.css('.skillsCollection')
        skills = [skill.css('span::text').get() for skill in skillsEl]
        
        
        yield {
            'company-name': response.css('p.Desktop_Body1_Medium::text').get(),
            'location': response.css('.header_logo_title_section .Desktop_Small1_Regular::text').get(),
            'company-image': extract_real_image_url(response.css('.header_logo_title_section img.company_logo::attr(src)').get()),
            'company-website': None,
            'job-title': response.css('.header_logo_title_section .Desktop_H4_Bold::text').get(),
            'position': None,
            'level': getLabelValue('Job Level'),
            'experience': response.css('.topDetailRendererList span.Desktop_Body2_Medium')[0].css('::text').get(),
            'total-position': getLabelValue('No. of Vacancy'),
            'job-type': response.css('.topDetailRendererList span.Desktop_Body2_Medium')[2].css('::text').get(),
            'salary': response.css('.topDetailRendererList span.Desktop_Body2_Medium')[1].css('::text').get(),
            'education': getLabelValue('Education'),
            'desired-gender': None,
            'skills': " | ".join(skills),
            'type': getLabelValue('Workplace Type'),
            'preferred-shift': None,
            # 'deadline':response.css('expirationBottomSection .Desktop_Body2_Medium::text').get(),
            'deadline': response.meta.get('post').get('deadline'),
            'description': response.css('div.job_description').get(),
            'job-specification': None,
            'url': response.url,
            'slug': slugify(response.css('.header_logo_title_section .Desktop_H4_Bold::text').get()),
            'posted-at': response.meta.get('post').get('created_date'),
            'view-count': response.meta.get('post').get('count'),
            'category': None,
            'expired': False,
        }
