# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
import logging
import re

class CoursePipeline(object):

    def __init__(self, mongo_uri):
        self.mongo_uri = mongo_uri
        self.course_set = set()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(mongo_uri=crawler.settings.get('MONGO_URI'))

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri,
            username='comp4332',
            password='bigdata',
            authSource='courses_db'
        )
        self.db = self.client['courses_db']

    def close_spider(self, spider):
        self.client.close()

    def fix_case(self, key):
        # remove characters '(', ')' and '-'
        s = key.translate({ord(c): '' for c in '()-'})
        # using regular expression
        #s = re.sub(r'[()-]', '', key)
        res = s.title().replace(' ', '')
        return res[0].lower() + res[1:]

    def process_item(self, item, spider):
        code = item['code']
        semester = item['semester']
        selector = item['selector']
        if (code, semester) not in self.course_set:
            course = {
                'code': code,
                'semester': semester
            }
            header = selector.xpath('.//h2/text()').extract_first()
            i = header.find('-')
            j = header.rfind('(')
            k = header.rfind('unit')
            course['title'] = header[i+1:j].strip()
            # credits may not be integer
            # example: 2017-18 Fall EMBA5590
            course['credits'] = float(header[j+1:k])
            for tr in selector.xpath('.//div[contains(@class, "courseattr")]/div/table/tr'):
                key = self.fix_case(' '.join(tr.xpath('.//th//text()').extract()))
                value = '\t'.join([
                    x.strip()
                    for x in tr.xpath('.//td//text()').extract()
                ])
                course[key] = value
            self.course_set.add((code, semester))
            self.db.courses.insert_one(course)
        item['selector'] = selector.xpath('.//table[@class="sections"]//tr')[1:]
        return item

class SectionPipeline(object):

    def __init__(self, mongo_uri):
        self.mongo_uri = mongo_uri
        self.section_set = set()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(mongo_uri=crawler.settings.get('MONGO_URI'))

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri,
            username='comp4332',
            password='bigdata',
            authSource='courses_db'
        )
        self.db = self.client['courses_db']

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        code = item['code']
        semester = item['semester']
        selector = item['selector']
        record_time = item['record_time']
        sections = []
        prev_sect = None
        for tr in selector:
            class_name = tr.xpath('./@class').extract_first()
            if 'newsect' in class_name:
                sectionId = tr.xpath('./td[1]/text()').extract_first().split('(', 1)[0].strip()
                m = re.match(r'\w+\d+', sectionId)
                if m == None:
                    print(code, sectionId)
                section = {
                    'sectionId': sectionId,
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
        for section in sections:
            sectionId = section['sectionId']
            if (code, semester, sectionId) not in self.section_set:
                self.section_set.add((code, semester, sectionId))
                section_data = {
                    'sectionId': sectionId,
                    'offerings': section['offerings']
                }
                if 'remarks' in section:
                    section_data['remarks'] = section['remarks']
                self.db.courses.update_one(
                    { 'code': code, 'semester': semester },
                    { '$push': {
                            'sections': section_data
                        }
                    }
                )
            self.db.courses.update_one(
                { 'code': code, 'semester': semester, 'sections.sectionId': sectionId },
                { '$push': {
                        'sections.$.snapshots': {
                            'recordTime': record_time,
                            'quota': section['quota'],
                            'enrol': section['enrol'],
                            'wait': section['wait']
                        }
                    }

                }
            )
        return item

class CompletePipeline(object):
    def close_spider(self, spider):
        print('Crawling complete')