# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
import logging

class CoursesPipeline(object):
    def process_item(self, item, spider):
        return item

class MongoPipeline(object):

    def __init__(self, mongo_uri):
        self.mongo_uri = mongo_uri

    @classmethod
    def from_crawler(cls, crawler):
        return cls(mongo_uri=crawler.settings.get('MONGO_URI'))

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client['courses_db']
        docs = self.db['courses'].aggregate([
            {
                '$group': {
                    '_id': '$code',
                    'semesters': { '$push': '$semester' }
                }
            }
        ])
        self.code_semesters = {
            doc['_id']: doc['semesters']
            for doc in docs
        }

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        code = item['code']
        semester = item['semester']
        if code not in self.code_semesters:
            self.db['course_codes'].insert_one({'code': code})
            self.code_semesters[code] = []
        if semester not in self.code_semesters[code]:
            self.db['courses'].insert_one(item)
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

class CompletePipeline(object):
    def close_spider(self, spider):
        print('Crawling complete')