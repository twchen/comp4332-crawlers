import scrapy
import asyncio
import pymongo
import re
from datetime import datetime
import pytz
import logging

class MongoSpider(scrapy.Spider):
    name = 'mongo'
    start_urls = ['http://localhost/snapshots.html']

    custom_settings = {
        'ITEM_PIPELINES': {
            'courses.pipelines.CoursePipeline': 700,
            'courses.pipelines.SectionPipeline': 800,
            'courses.pipelines.CompletePipeline': 900
        }
    }

    def __init__(self, *args, **kwargs):
        super(MongoSpider, self).__init__(*args, **kwargs)
        logging.debug('Initialized')

    def parse(self, response):
        for a in response.xpath('//ul/li/a'):
            logging.debug('Following snapshot: ' + a.extract())
            yield response.follow(a, callback=self.parse_snapshot)

    def parse_snapshot(self, response):
        for a in response.xpath('//div[@class="depts"]/a'):
            logging.debug('Following dept: ' + a.extract())
            yield response.follow(a, callback=self.parse_dept)

    def parse_dept(self, response):
        title = response.xpath('//title/text()').extract_first()
        i = title.find(': Snapshot taken at ')
        semester = title[:i-5] # each dept has a length of 4
        record_time = datetime.strptime(title[i + len(': Snapshot taken at '):], '%Y-%m-%d %H:%M')
        # simpler method using regular expression
        # m = re.search(r'(.*) \w+: Snapshot taken at (.*)', title)
        # semester = m.group(1)
        # record_time = datetime.strptime(m.group(2), '%Y-%m-%d %H:%M')
        record_time = pytz.timezone('Hongkong').localize(record_time, is_dst=None)
        courses = response.xpath('//div[@class="course"]')
        for course in courses:
            header = course.xpath('.//h2/text()').extract_first()
            item = {
                'code': header.split('-', maxsplit=1)[0].replace(' ', ''),
                'semester': semester,
                'record_time': record_time,
                'selector': course
            }
            yield item
