import scrapy
from slugify import slugify


class JobaxleSpider(scrapy.Spider):
    name = "jobaxle"
    allowed_domains = ["jobaxle.com"]
    start_urls = ["https://jobaxle.com/api/search?page=1&limit=500"]

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
            'website': '',
            'job-title': data['jobTitle'],
            'position': '',
            'level': data['joblevel']['title'],
            'experience': data['minExperience'],
            'total-position': data['noOfVacancy'],
            'job-type': data['jobtype']['title'],
            'salary': f"{data['salaryType']} {data['minSalary']}",
            'education': data['educationlevel']['title'],
            'type': data['workNature'],
            'deadline':data['deadline'],
            'description': data['jobSpecification'],
            'url': response.url,
            'slug': slugify(data['jobTitle'])
        }


