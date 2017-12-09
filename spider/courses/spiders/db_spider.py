import scrapy
import asyncio
import pymongo
import re


class DBSpider(scrapy.Spider):
    name = 'db'

    def parse(self, response):
        for a in response.xpath('//ul/li/a'):
            yield response.follow(a, callback=self.parse_snapshot)

    def parse_snapshot(self, response):
        for a in response.xpath('//div[@class="depts"]/a'):
            yield response.follow(a, callback=self.parse_dept)

    def parse_dept(self, response):
        courses = response.xpath('//div[@class="course"]')
        tasks = [
            asyncio.ensure_future(self.parse_course(course))
            for course in courses
        ]
        return await asyncio.gather(*tasks)

    async def parse_course(self, el):
        # TODO 2: add semester and recordTime
        course = {}
        header = el.xpath('.//h2/text()').extract_first()
        m = re.search('(.*?)\s-\s(.*?)\s\((\d+)\s*unit[s]\)', header)
        course['code'] = m.group(1)
        course['title'] = m.group(2)
        course['credit'] = m.group(3)
        for tr in el.xpath('.//div[contains(@class, "courseattr")]//table//tr'):
            key = self.fix_case(tr.xpath('.//th/text()').extract_first())
            value = tr.xpath('.//td/text()').extract()
            if key != 'attributes' and len(value) == 1:
                value = value[0]
            course[key] = value
        sections = []
        prev_sect = None
        for tr in el.xpath('.//table[@class="sections"]')[0][1:]:
            class_name = tr.xpath('./@class').extract_first()
            if 'newsect' not in class_name:
                offering = {
                    # index starts from 1
                    # TODO: split dateAndTime to daysOfWeek and time
                    'dateAndTime': tr.xpath('./td[1]/text()').extract_first(),
                    'room': tr.xpath('./td[2]/text()').extract_first(),
                    'instructors': tr.xpath('./td[3]/text()').extract()
                }
                prev_sect['offerings'].append(offering)
            else:
                section = {
                    'section': tr.xpath('./td[1]/text()').extract_first(),
                    'offerings': [
                        'dateAndTime': tr.xpath('./td[2]/text()').extract_first(),
                        'room': tr.xpath('./td[3]/text()').extract_first(),
                        'instructors': tr.xpath('./td[4]/text()').extract()
                    ],
                    'quota': tr.xpath('./td[5]/text()').extract_first(),
                    'enrol': tr.xpath('./td[6]/text()').extract_first(),
                    'wait': tr.xpath('./td[8]/text()').extract_first()
                }
                remark = tr.xpath('./td[9]/text()').extract_first()
                if remark.strip() != '':
                    section['remark'] = remark
                sections.append(section)
                prev_sect = section
        course['sections'] = sections
        await insert(course)

    async def insert(self, course):
        pass

    def fix_case(self, s):
        res = s.replace('-', '').title().replace(' ', '')
        return res[0].tolower + res[1]
