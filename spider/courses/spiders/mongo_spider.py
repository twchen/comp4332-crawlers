import scrapy
import asyncio
import pymongo
import re
from datetime import datetime
import pytz
import logging

class MongoSpider(scrapy.Spider):
    name = 'mongo'
    start_urls = ['http://comp4332.gitlab.io']

    custom_settings = {
        'ITEM_PIPELINES': {
            'courses.pipelines.MongoPipeline': 800,
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
        #record_time = pytz.timezone('Hongkong').localize(record_time, is_dst=None)
        courses = response.xpath('//div[@class="course"]')
        for course in courses:
            yield self.parse_course(course, semester, record_time)

    def parse_course(self, el, semester, record_time):
        course = { 'semester': semester }
        header = el.xpath('.//h2/text()').extract_first()
        i = header.find('-')
        j = header.rfind('(')
        k = header.rfind('unit')
        course['code'] = header[:i].replace(' ', '')
        course['title'] = header[i+1:j].strip()
        # credits may not be integer
        # example: 2017-18 Fall EMBA5590
        course['credits'] = float(header[j+1:k])
        # simpler method using regular expression
        # m = re.search(r'(.*?)\s-\s(.*?)\s\(([\d\.]+)\s*unit[s]?\)', header)
        # course['code'] = m.group(1).replace(' ', '')
        # course['title'] = m.group(2).strip()
        # course['credits'] = float(m.group(3))
        logging.debug('Parsing course: ' + course['code'])
        for tr in el.xpath('.//div[contains(@class, "courseattr")]/div/table/tr'):
            key = self.fix_case(' '.join(tr.xpath('.//th//text()').extract()))
            value = '\t'.join([
                x.strip()
                for x in tr.xpath('.//td//text()').extract()
            ])
            course[key] = value
        sections = []
        prev_sect = None
        for tr in el.xpath('.//table[@class="sections"]//tr')[1:]:
            class_name = tr.xpath('./@class').extract_first()
            if 'newsect' in class_name:
                section = {
                    'section': tr.xpath('./td[1]/text()').extract_first(),
                    'offerings': [
                        {
                            # most complicated case: 2016-17 Summer MGMT5410
                            'dateAndTime': ' '.join(tr.xpath('./td[2]/text()').extract()),
                            'room': tr.xpath('./td[3]/text()').extract_first(),
                            'instructors': tr.xpath('./td[4]/text()').extract()
                        }
                    ],
                    # the text may be inside its children
                    # example: 2016-17 Spring ACCT5140 L1
                    'quota': int(tr.xpath('./td[5]//text()').extract_first()),
                    'enrol': int(tr.xpath('./td[6]//text()').extract_first()),
                    # if avail is 0, it is enclosed by <strong>
                    #'avail': int(tr.xpath('./td[7]//text()').extract_first()),
                    'wait': int(tr.xpath('./td[8]//text()').extract_first())
                }
                remarks = '\t'.join([
                    text.strip()
                    for text in tr.xpath('./td[9]//text()').extract()
                    if text.strip() != ''
                ])
                if remarks != '':
                    section['remarks'] = remarks
                sections.append(section)
                prev_sect = section
            else:
                offering = {
                    # index starts from 1
                    # TODO: split dateAndTime to daysOfWeek and time
                    'dateAndTime': ' '.join(tr.xpath('./td[1]/text()').extract()),
                    'room': tr.xpath('./td[2]/text()').extract_first(),
                    'instructors': tr.xpath('./td[3]/text()').extract()
                }
                prev_sect['offerings'].append(offering)
        course['sections'] = sections
        return course

    def fix_case(self, key):
        # remove characters '(', ')' and '-'
        s = key.translate({ord(c): '' for c in '()-'})
        # using regular expression
        #s = re.sub(r'[()-]', '', key)
        res = s.title().replace(' ', '')
        return res[0].lower() + res[1:]
