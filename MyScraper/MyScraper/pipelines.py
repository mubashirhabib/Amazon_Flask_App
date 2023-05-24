# -*- coding: utf-8 -*-
from flask import jsonify


# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


class MyscraperPipeline(object):
    scraped_data = []

    def process_item(self, item, spider):
        # Process each scraped item and store it in the scraped_data list
        self.scraped_data.append(item)
        return item

    def get_scraped_data(self):
        # Return the scraped data as a JSON response
        return self.scraped_data
