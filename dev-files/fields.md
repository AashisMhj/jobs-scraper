**scraped fields details**

- company-name: name of the company
- location: location of the company or job
- company-image: image of the company
- company-site: company website
- job-title: Title of the job
- position: Job Position (Field Engineer, Software Developer, UI/UX Developer), usually contained in title and there for empty
- level: Job Level (Beginner, Expert etc)
- experience: Required job experience
- total-position: No of open vacancy
- job-type: Full Time, Part Time, Contract
- salary:
- education
- desired-gender:
- skills:
- type: Remote, Hybrid, On-site
- deadline: deadline to submit application
- description: job description and specification
- job-specification: similar to description but contains responsibilities of job
- url: scraped url
- slug: generated slug from title

```python
yield {
    'company-name': '',
    'location': '',
    'company-image': '',
    'company-website': '',
    'job-title': '',
    'position': '',
    'level': '',
    'experience': '',
    'total-position': '',
    'job-type': '',
    'salary': '',
    'education': '',
    'desired-gender': '',
    'skills': '',
    'type': '',
    'preferred-shift': '',
    'deadline':'',
    'description': '',
    'job-specification': '',
    'url': response.url,
    'slug': '',
    'posted-at': '',
    'view-count': '',
    'category': None,
    'expired': False,
}
```

<!-- fields to add -->

- company-industry
- no-of-applied
- shift
- working-days