# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
from .myspider import AmazonSpider


def create_spider(keyword=''):
    return AmazonSpider(keyword=keyword)
