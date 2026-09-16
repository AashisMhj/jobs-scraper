# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


from collections import Counter

from itemadapter import ItemAdapter
from scrapy import signals

# A spider whose site has been redesigned still finishes cleanly, so a run is
# only trusted when it also collects a plausible number of items. These floors
# sit well under the volumes seen on 2026-09-16 (16, 154, 73, 428, 216, 204, 38)
# so that ordinary fluctuation in job counts does not trip the check.
MINIMUM_ITEMS = {
    'jobaxle': 5,
    'jobsnepal': 50,
    'jobssniper': 25,
    'kumarijob': 150,
    'merojob': 75,
    'rojgari': 75,
    'vocalpanda': 10,
}

# When selectors stop matching, items keep being produced but their fields come
# back empty, so the fields no job can be useful without are checked too.
REQUIRED_FIELDS = ('job-title', 'url')
REQUIRED_FILL = 0.8

FAILURE = "HEALTH CHECK FAILED"


class JobsScraperPipeline:
    def process_item(self, item, spider):
        return item


class HealthCheckPipeline:
    """Report spiders that finish without error but stop collecting.

    Every portal here has changed its markup or its backend at some point,
    which empties a spider silently: Scrapy still exits successfully and the
    feed is simply empty or full of nulls.
    """

    def __init__(self):
        self.scraped = 0
        self.filled = Counter()

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spiderClosed, signal=signals.spider_closed)
        return pipeline

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        self.scraped += 1
        for field in REQUIRED_FIELDS:
            if adapter.get(field) not in (None, ''):
                self.filled[field] += 1
        return item

    def spiderClosed(self, spider):
        for problem in self.problems(spider.name):
            spider.logger.error("%s [%s]: %s", FAILURE, spider.name, problem)

    def problems(self, name):
        minimum = MINIMUM_ITEMS.get(name, 1)
        if self.scraped < minimum:
            yield f"scraped {self.scraped} items, expected at least {minimum}"

        if not self.scraped:
            # Without items the fill ratios say nothing the count has not.
            return

        for field in REQUIRED_FIELDS:
            filled = self.filled[field]
            if filled / self.scraped < REQUIRED_FILL:
                yield (
                    f"only {filled} of {self.scraped} items have a "
                    f"'{field}', so its selector has likely stopped matching"
                )
