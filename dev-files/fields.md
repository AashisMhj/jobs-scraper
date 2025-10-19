**scraped fields details**

- company-name: name of the company
- location: location of the company
- image: image of the company
- website: company website
- job-title: Title of the job
- position: Job Position (Field Engineer, Software Developer, UI/UX Developer), usually contained in title and there for empty
- level: Job Level (Beginner, Expert etc)
- experience: Required job experience
- total-position: No of open vacancy
- job-type: Full Time, Part Time
- salary:
- education
- desired-gender:
- skills:
- type: Remote, Hybrid, On-site
- deadline: deadline to submit application
- description: job description and specification
- url: scraped url
- slug: generated slug from title

```python
yield {
    'company-name': '',
    'location': ,
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
    'deadline':'',
    'description': '',
    'url': response.url,
    'slug': ''
}
```

<!-- fields to add -->
- desired-gender: (in all)
- skills: (in all)
- category: job category field (hotel, it, finance)
