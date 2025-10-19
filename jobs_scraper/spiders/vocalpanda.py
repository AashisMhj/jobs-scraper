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
            "page_size": 1000,
            "salary_type": None
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }

        yield scrapy.Request(
            url=url,
            method="POST",
            headers=headers,
            body=json.dumps(payload),
            callback=self.parse
        )

    def parse(self, response):
        resJson = response.json()
        posts = resJson['response']['job_list']
        postUrls = map(lambda x: f"https://www.vocalpanda.com/{slugify(x['job_title'])}-{x['job_id']}", posts)
        yield from response.follow_all(postUrls, self.parseDetail)

    def parseDetail(self, response):

        yield {
            'id': 1
        }
