import scrapy
from slugify import slugify


class JobaxleSpider(scrapy.Spider):
    name = "jobaxle"
    allowed_domains = ["jobaxle.com"]
    start_urls = ["https://jobaxle.com/api/search?page=1&limit=2"]

    def parse(self, response):
        resJson = response.json()
        data = resJson['data']['rows']
        detailApis = map(lambda x: f"https://jobaxle.com/api/jobdetails/{x['slug']}", data) 
        yield from response.follow_all(detailApis, self.parseDetail)

    def parseDetail(self, response):
        resJson = response.json()
        data = resJson['data']['jobDetail']
        yield {
            'company-name': data['member']['fullName'],
            'location': data['member']['employerDetail'][0]['companyLocation']['title'] ,
            'company-image': f"https://jobaxle.com/api/image/company_logo/{data['member']['profileImage']}",
            'company-website': None,
            'job-title': data['jobTitle'],
            'position': None,
            'level': data['joblevel']['title'],
            'experience': data['minExperience'],
            'total-position': data['noOfVacancy'],
            'job-type': data['jobtype']['title'],
            'salary': f"{data['salaryType']} {data['minSalary']}",
            'education': data['educationlevel']['title'],
            'desired-gender': data['gender'],
            'skills': " | ".join(data['skillTitles']),
            'type': data['workNature'],
            'preferred-shift': None,
            'deadline':data['deadlineEndDate'],
            'description': data['jobSpecification'],
            'job-specification': data['jobSpecification'],
            'url': response.url,
            'slug': slugify(data['jobTitle']),
            'posted-at': None,
            'view-count': data.get('views'),
            'category': None,
            'expired': None
        }


