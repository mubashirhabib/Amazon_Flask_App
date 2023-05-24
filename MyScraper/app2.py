from MyScraper.spiders import AmazonSpider
from flask import Flask, jsonify
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from multiprocessing import Process, Manager
from MyScraper.pipelines import MyscraperPipeline


app = Flask(__name__)


def start_crawler(keyword, data_list):
    with app.app_context():
        process = CrawlerProcess(get_project_settings())
        spider_cls = AmazonSpider

        # Use a custom pipeline to capture the scraped data
        custom_pipeline = MyscraperPipeline()
        process.settings.set('ITEM_PIPELINES', {'MyScraper.pipelines.MyscraperPipeline': 300})
        # process.settings.set('DOWNLOAD_DELAY', 3)
        process.crawl(spider_cls, keyword=keyword)
        # Start the crawler
        process.start()
        scraped_data = custom_pipeline.get_scraped_data()  # Get the scraped data from the custom pipeline
        data_list.append(scraped_data)


@app.route('/<keyword>')
def scrape_data(keyword):
    manager = Manager()
    list_of_data = manager.list()
    crawler_process = Process(target=start_crawler, args=(keyword, list_of_data))
    crawler_process.start()
    crawler_process.join()

    print(f"data is :{list_of_data}")
    flat_list = sum(list_of_data, [])
    return jsonify(flat_list)


@app.route('/favicon.ico')
def favicon():
    return jsonify([])


if __name__ == '__main__':
    app.run()
