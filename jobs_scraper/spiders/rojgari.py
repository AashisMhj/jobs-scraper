import scrapy
from slugify import slugify


class RojgariSpider(scrapy.Spider):
    name = "rojgari"
    allowed_domains = ["rojgari.com"]
    start_urls = ["https://api.rojgari.com/api/v1/job/search/?limit=1000"]

    def parse(self, response):
        resJson = response.json()
        posts = resJson['results']
        postUrls = map(lambda x: f"https://api.rojgari.com/api/v1/job/search/{x['slug']}", posts)
        yield from response.follow_all(postUrls, self.parseDetail)

    def parseDetail(self, response):
        data = response.json()
        yield {
            'company-name': data['organization']['name'],
            'location': data['job_locations'][0]['full_address'] if len(data.get('job_locations')) > 1 else None,
            'company-image': data['organization']['logo'],
            'company-website': None,
            'job-title': data['job_title'],
            'position': None,
            'level': data['job_level'],
            'experience': data['setting'].get('min_experience_months'),
            'total-position': data['vacancies'],
            'job-type': " | ".join(data['available_for']),
            'salary': data['offered_salary'],
            'education': data['education_level'],
            'desired-gender': data['setting'].get('gender', 'Both'),
            'skills': " | ".join(data['skills']),
            'type': None,
            'preferred-shift': data.get('preferred_shift'),
            'deadline':data['deadline'],
            'description': data['description'],
            'job-specification': None,
            'url': response.url,
            'slug': slugify(data['job_title']),
            'posted-at': data['posted_at'],
            'view-count': data['hit_count'],
            'category': " , ".join([x['name'] for x in data['categories']]),
            'expired': data['is_expired']
        }
