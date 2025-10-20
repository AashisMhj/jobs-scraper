import scrapy
import json
from slugify import slugify


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
            "page_size": 1,
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
        postUrls = map(lambda x: f"https://www.vocalpanda.com/{slugify(x['job_title'])}-{x['job_id']}", posts)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        for url in postUrls:
            yield scrapy.Request(url, meta={"playwright": True}, callback=self.parseDetail, headers=headers)


    async def parseDetail(self, response):
        page = response.meta["playwright_page"]
        await page.wait_for_selector(".header_logo_title_section")
        yield {
            'id': 1
        }
