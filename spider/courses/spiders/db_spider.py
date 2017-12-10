import scrapy
import asyncio
import pymongo
import re
from datetime import datetime
import pytz
import logging

class DBSpider(scrapy.Spider):
    name = 'db'
    start_urls = ['http://comp4332.gitlab.io']
    client = pymongo.MongoClient('mongodb://localhost:27017')
    db = client['courses_db']

    def __init__(self, *args, **kwargs):
        super(DBSpider, self).__init__(*args, **kwargs)
        docs = self.db['courses'].aggregate([
            {
                '$group': {
                    '_id': '$code',
                    'semesters': { '$push': '$semester' }
                }
            },
            {
                '$project': {
                    '_id': 0,
                    'code': '$_id',
                    'semesters': 1
                }
            }
        ])
        self.code_semesters = {
            doc['code']: doc['semesters']
            for doc in docs
        }
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
        m = re.search(r'(.*) \w+: Snapshot taken at (.*)', title)
        semester = m.group(1)
        record_time = datetime.strptime(m.group(2), '%Y-%m-%d %H:%M')
        #record_time = pytz.timezone('Hongkong').localize(record_time, is_dst=None)
        courses = response.xpath('//div[@class="course"]')
        for course in courses:
            yield self.parse_course(course, semester, record_time)

    def parse_course(self, el, semester, record_time):
        course = { 'semester': semester }
        header = el.xpath('.//h2/text()').extract_first()
        m = re.search(r'(.*?)\s-\s(.*?)\s\(([\d\.]+)\s*unit[s]?\)', header)
        course['code'] = m.group(1).replace(' ', '')
        logging.debug('Parsing course: ' + course['code'])
        course['title'] = m.group(2).strip()
        # credits may not be integer
        # example: 2017-18 Fall EMBA5590
        course['credits'] = float(m.group(3))
        for tr in el.xpath('.//div[contains(@class, "courseattr")]/div/table/tr'):
            key = self.fix_case(' '.join(tr.xpath('.//th//text()').extract()))
            value = ' '.join([
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
                            # most complicated case: 2016-17 Summer MGMT5230 L1
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
                remarks = '\n'.join([
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
        self.insert(course)

    def insert(self, course):
        logging.debug('Inserting to database')
        code = course['code']
        semester = course['semester']
        if code not in self.code_semesters:
            self.db['course_codes'].insert_one({'code': code})
            self.code_semesters[code] = []
        if semester not in self.code_semesters[code]:
            self.db['courses'].insert_one(course)
            self.code_semesters[code].append(semester)
        else:
            self.db['courses'].update_one(
                {'code': code, 'semester': semester},
                {'$push': {
                        'sections': {
                            '$each': course['sections']
                        }
                    }
                }
            )

    def fix_case(self, s):
        res = s.replace('-', '').title().replace(' ', '')
        return res[0].lower() + res[1:]
