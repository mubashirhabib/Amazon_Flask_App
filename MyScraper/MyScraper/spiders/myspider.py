from __future__ import unicode_literals

from scrapy import Spider, Request
from urllib.parse import unquote
import json
from bs4 import BeautifulSoup


class AmazonSpider(Spider):
    name = 'amazon'
    base_url = 'https://www.amazon.in/'
    # Proxy
    zyte_key = '0965d59df65d4b7c94140e555f1c03b4'
    custom_settings = {
        "ZYTE_SMARTPROXY_ENABLED": True,
        'ZYTE_SMARTPROXY_APIKEY': f'{zyte_key}',
        'ZYTE_SMARTPROXY_PRESERVE_DELAY': True,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_zyte_smartproxy.ZyteSmartProxyMiddleware': 610,
        },
    }
    total_pages = -1
    current_page = 1
    cookie = ''
    keyword = ''

    def __init__(self, *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        print(f"lower{kwargs}")
        if 'keyword' in kwargs:
            self.keyword = kwargs['keyword']

    def start_requests(self):
        yield Request(url=self.base_url, callback=self.parse_data)

    def parse_data(self, response):
        print("-------------------- AMAZON CRAWLER --------------------")
        # keyword = input("Input Search Keyword :")
        self.keyword = self.keyword.replace(" ", "+")
        print(f"SHOWING RESULT FOR :{self.keyword}")
        url = f"https://www.amazon.in/s/ref=nb_sb_noss_1?url=search-alias%3Daps&field-keywords={self.keyword}&crid=2H9F22BB8QJ8P&sprefix={self.keyword}%2Caps%2C475"
        payload = ''
        headers = {
            'authority': 'www.amazon.in',
            'referer': 'https://www.amazon.in/ref=nav_logo',
            'rtt': '100',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
            'viewport-width': '1536'
        }
        yield Request(url=url, callback=self.parse_total_pages, headers=headers, body=payload, method='GET')

    def parse_total_pages(self, response):
        self.total_pages = int(response.css('.s-pagination-item.s-pagination-disabled::text').extract()[-1])
        print(f"----------------------------- TOTAL Pages ARE : {self.total_pages} -----------------------------")
        for page_no in range(1, self.total_pages+1):
            url = response.url.split("&crid")[0] + f"&page={page_no}&crid" + response.url.split("&crid")[1]
            payload = ''
            headers = {
                'authority': 'www.amazon.in',
                'referer': 'https://www.amazon.in/ref=nav_logo',
                'rtt': '100',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
                'viewport-width': '1536'
            }
            yield Request(url=url, callback=self.parse_data_link, headers=headers, body=payload, method='GET')

    def parse_data_link(self, response):
        links = []
        raw_links = response.css('.a-section.a-spacing-none.puis-padding-right-small.s-title-instructions-style h2 a.s-link-style::attr(href)').extract()
        for link in raw_links:
            if "/sspa/click" in link:
                links.append(f"https://www.amazon.in{unquote(link).split('url=')[1]}")
            else:
                links.append(f"https://www.amazon.in{unquote(link)}")

        print(f"----------------------------- TOTAL LINKS ARE : {len(links)} -----------------------------")
        self.cookie = f"{response.headers.getlist('Set-Cookie')[0].decode('utf-8').split(';')[0]};"
        for lk in links:
            payload = ""
            headers = {
                'authority': 'www.amazon.in',
                'cache-control': 'max-age=0',
                'cookie': f"{self.cookie};",
                'referer': lk,
                'rtt': '200',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
                'viewport-width': '1536'
            }
            yield Request(url=lk, callback=self.parse_inner_details, headers=headers, body=payload, method='GET')

    def parse_inner_details(self, response):
        meta_data = {}
        meta_data["status"] = response.status
        meta_data["number_of_data"] = self.total_pages
        meta_data["source_main_domain"] = "amazon.in"
        data = {}
        data['ASIN'] = response.url.split("dp/")[1].split("/")[0]
        data['Web_Page_URL'] = response.url
        # strip bellow
        if response.css('#productTitle::text').get() is not None:
            data['Title'] = response.css('#productTitle::text').get().strip()
        else:
            data['Title'] = None

        print("**************************** Inner details ****************************")
        list_of_lazy_responses = response.css(".json-content::text").extract()
        if list_of_lazy_responses:
            data["lazy_response"] = list_of_lazy_responses[-1]
        else:
            data["lazy_response"] = ""

        data['Brand'] = response.css('.po-brand .po-break-word::text').get()
        data['Star_Rating'] = response.css('span.a-icon-alt::text').get()
        data['Number_of_Reviews'] = response.css('#acrCustomerReviewText::text').get()
        data['Review_Page_URL'] = f"https://www.amazon.in{response.css('.a-link-emphasis.a-text-bold::attr(href)').get()} "
        if response.css('#askATFLink span::text').get() is not None:
            data['Number_of_Answered_Questions'] = response.css('#askATFLink span::text').get().strip()
        else:
            data['Number_of_Answered_Questions'] = None

        data[
            'Answered_Questions_Page_URL'] = f"https://www.amazon.in/ask/questions/asin/{data['ASIN']}/ref=ask_dp_dpmw_ql_hza?isAnswered=true"
        data['Price'] = response.css('.a-offscreen::text').get()
        data['MRP'] = response.css('.a-text-price span::text').get()

        if response.css('.postpurchase-included-components-list-item span::text').get() is not None:
            data['Inventory'] = response.css('.postpurchase-included-components-list-item span::text').get().strip()
        else:
            data['Inventory'] = None

        data['Seller'] = response.css('.a-link-normal:nth-child(2) span::text').get()
        data['Bullet_Points'] = response.css('#feature-bullets .a-list-item::text').extract()
        information_keys = response.css('#poExpander .a-text-bold::text').extract()
        information_pairs = response.css('.a-span9 span::text').extract()
        information = {information_keys[i]: information_pairs[i] for i in range(len(information_keys))}
        case_check = False
        data['Product_Information'] = information
        key_list = response.css('.prodDetSectionEntry::text').extract()
        cleaned_key_list = []
        for key in key_list:
            cleaned_key_list.append(key.strip())

        pair_list = response.css('#prodDetails td::text').extract()
        if not bool(key_list):
            case_check = True

        if case_check:
            key_list = response.css('strong::text').extract()
            pair_list = response.css('td+ td p::text').extract()

            if len(key_list) == len(pair_list):
                details = {key_list[i]: pair_list[i] for i in range(len(key_list))}
            else:
                details = {}
        else:
            cleaned_pair_list = []
            for pl in pair_list:
                str1 = pl.strip()
                str2 = str1.encode('ascii', 'ignore')
                str3 = str2.decode("utf-8")
                if str3 == "":
                    continue
                else:
                    cleaned_pair_list.append(str3)

            if "Best Sellers Rank" in cleaned_key_list:
                index_best_seller = cleaned_key_list.index("Best Sellers Rank")
                rank_value1 = response.css('#productDetails_detailBullets_sections1 span::text').extract()
                rank_value_with_hash = [x[0:-1] for x in rank_value1 if "#" in x]
                rank_value2 = response.css('#productDetails_detailBullets_sections1 span a::text').extract()[-1]
                final_rank_value = ' '.join([str(elem) for elem in rank_value_with_hash]) + f" {rank_value2}"
                cleaned_pair_list.insert(index_best_seller, final_rank_value)

            if len(cleaned_key_list) == len(cleaned_pair_list):
                details = {cleaned_key_list[i]: cleaned_pair_list[i] for i in range(len(key_list))}
            else:
                details = {}

        data['Product_Description'] = response.css('#productDescription span::text').extract()
        data['Product_Details'] = details
        data['Item_Model_Number'] = ""
        data['Item_Weight'] = ""
        data['Shipping_Weight'] = ""
        data['Product_Dimensions'] = ""
        data['Best_Sellers_Rank'] = ""
        data['Date_First_Available'] = ""
        for x, y in details.items():
            if "Item model number" == x:
                data['Item_Model_Number'] = y
            if "Item Weight" == x:
                data['Item_Weight'] = y
            if "Item Dimensions LxWxH" == x:
                data['Product_Dimensions'] = y
            if "Best Sellers Rank" == x:
                data['Best_Sellers_Rank'] = y
            if "Date First Available" == x:
                data['Date_First_Available'] = y
            if "Best Sellers Rank" == x:
                data['Best_Sellers_Rank'] = y

        data['Shipping_Weight'] = data['Item_Weight']
        data['UPC'] = ""
        data['Style'] = ""
        # strip bellow
        if response.css('#inline-twister-expanded-dimension-text-size_name::text').get() is not None:
            data['Size'] = response.css('#inline-twister-expanded-dimension-text-size_name::text').get().strip()
        else:
            data['Size'] = None
        # strip bellow
        if response.css('#inline-twister-expanded-dimension-text-color_name::text').get() is not None:
            data['Color'] = response.css('#inline-twister-expanded-dimension-text-color_name::text').get().strip()
        else:
            data['Color'] = None

        image_urls_list = response.css(".a-spacing-small.item img::attr(src)").extract()
        image_urls = {f"Image_URL_{i+1}": image_urls_list[i] for i in range(len(image_urls_list))}
        data["Image_Urls"] = image_urls
        variations_asin_code = response.css(".page-load-link::attr(href)").extract()
        variations_asin_code = [x.split("dp/")[1].split("/")[0] for x in variations_asin_code]
        data["Variation Length"] = len(variations_asin_code)
        data["Variations"] = []
        meta_data["data"] = data
        #  *************************************** START 0 ZERO VARAITIONS *************************************
        if data["Variation Length"] == 0:
            for index in range(0, 1):
                new_url = response.url
                payload = ""
                headers = {
                    'authority': 'www.amazon.in',
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'accept-language': 'en-US,en;q=0.9',
                    'cache-control': 'max-age=0',
                    'cookie': f"{self.cookie};",
                    'rtt': '200',
                    'upgrade-insecure-requests': '1',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
                    'viewport-width': '1536'
                }
                yield Request(url=new_url, callback=self.parse_variation_data, headers=headers, body=payload,
                              method='GET',
                              meta=meta_data, dont_filter=True)
        #  *************************************** END 0 ZERO VARAITIONS *************************************
        for index in range(0, len(variations_asin_code)):
            new_url = response.url.replace(data['ASIN'], variations_asin_code[index])
            payload = ""
            headers = {
                'authority': 'www.amazon.in',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-US,en;q=0.9',
                'cache-control': 'max-age=0',
                'cookie': self.cookie,
                'rtt': '200',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
                'viewport-width': '1536'
            }
            yield Request(url=new_url, callback=self.parse_variation_data, headers=headers, body=payload, method='GET',
                          meta=meta_data, dont_filter=True)

    def parse_variation_data(self, response):
        var_data = {}
        if response.css('#productTitle::text').get() is not None:
            var_data["Title"] = response.css('#productTitle::text').get().strip()
        else:
            var_data["Title"] = None

        var_data['Price'] = response.css('.a-offscreen::text').get()
        var_data['MRP'] = response.css('.a-text-price span::text').get()
        if response.css('#inline-twister-expanded-dimension-text-color_name::text').get() is not None:
            color = response.css('#inline-twister-expanded-dimension-text-color_name::text').get().strip()
        else:
            color = None

        var_data['Variable'] = {
            "name": "Color",
            "value": color
        }
        image_urls_list = response.css(".a-spacing-small.item img::attr(src)").extract()
        image_urls = {f"Image_URL_{i+1}": image_urls_list[i] for i in range(len(image_urls_list))}
        var_data["Image_Urls"] = image_urls
        meta_data = response.meta
        print("**************************** Variations ****************************")
        meta_data["data"]["Variations"].append(var_data)
        if meta_data["data"]["Variation Length"] == 0:
            meta_data["data"]["Variations"] = []
        if len(meta_data["data"]["Variations"]) == meta_data["data"]["Variation Length"]:
            url = "https://www.amazon.in/dram/renderLazyLoaded"
            payload = meta_data["data"]["lazy_response"]
            if payload == "":
                url = ""
                yield Request(url="https://www.amazon.in/", callback=self.parse_suggestion_data_without_payload, meta=meta_data, dont_filter=True)

            headers = {
                'authority': 'www.amazon.in',
                'accept': 'application/json',
                'accept-language': 'en-US,en;q=0.9',
                'content-type': 'application/json',
                'cookie': self.cookie,
                'origin': 'https://www.amazon.in',
                'referer': response.url,
                'rtt': '250',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 OPR/97.0.0.0',
                'viewport-width': '1994',
                'x-requested-with': 'XMLHttpRequest'
            }
            yield Request(url=url, callback=self.parse_suggestion_data, headers=headers, body=payload, method='POST', meta=meta_data, dont_filter=True)

    def parse_suggestion_data_without_payload(self, response):
        meta_data = response.meta
        meta_data.pop("download_timeout", None)
        meta_data.pop("depth", None)
        meta_data.pop("download_slot", None)
        meta_data.pop("download_latency", None)
        meta_data.pop("redirect_times", None)
        meta_data.pop("redirect_ttl", None)
        meta_data.pop("redirect_urls", None)
        meta_data.pop("redirect_reasons", None)
        meta_data.pop("lazy_response", None)
        del meta_data['data']['lazy_response']
        meta_data["data"]["More_Buying_Choices"] = []
        yield meta_data

    def parse_suggestion_data(self, response):
        more_choices = []
        links = []
        titles = []
        images = []
        prices = []
        mrfs = []
        asins = []
        meta_data = response.meta
        meta_data.pop("download_timeout", None)
        meta_data.pop("depth", None)
        meta_data.pop("download_slot", None)
        meta_data.pop("download_latency", None)
        meta_data.pop("redirect_times", None)
        meta_data.pop("redirect_ttl", None)
        meta_data.pop("redirect_urls", None)
        meta_data.pop("redirect_reasons", None)
        meta_data.pop("lazy_response", None)
        raw_data = json.loads(response.text)
        data = raw_data["cards"][0]["content"]
        soup = BeautifulSoup(data)
        if soup.find("div", {"id": "sp_detail"}):
            list_asins = soup.find("div", {"id": "sp_detail"})["data-a-carousel-options"].split('{"initialSeenAsins":[')[1].split("]")[0].split(",")
        else:
            list_asins = []

        for asin in list_asins:
            asins.append(asin.replace('"', ''))
        for link in list_asins:
            gt = link.replace('"', '')
            links.append(f"https://www.amazon.in/dp/{gt}/ref=sspa_dk_detail_1?psc=1&pd_rd_i={gt}")

        image_data = soup.find_all("img")
        for image in image_data:
            images.append(image["src"])

        for title in soup.find_all("div", {"class": "sponsored-products-truncator-truncate"}):
            titles.append(title.get_text().strip())

        price_data = soup.find_all("span", {"class": "a-size-medium a-color-price"})
        for price in price_data:
            prices.append(price.get_text())

        for m in price_data:
            mrfs.append(0)

        for index in range(len(links)):
            data = {"ASIN": asins[index], "Web_Page_URL": links[index], "Title": titles[index], "Price": prices[index],
                    "MRP": mrfs[index], "Image_URL": images[index]}
            more_choices.append(data)
        print("**************************** sugeestions details ****************************")
        # pdb.set_trace()
        del meta_data['data']['lazy_response']
        if not more_choices:
            for title in soup.find_all("div", {"class": "p13n-sc-truncate-desktop-type2"}):
                titles.append(title.get_text().strip())

            for price in soup.find_all("span", {"class": "a-offscreen"})[1:]:
                prices.append(price.get_text().strip())

            # for mrf in soup.find_all("span", {"class": "aok-nowrap a-text-strike"}):
            #     mrfs.append(mrf.get_text().strip())

            for link in soup.find_all("a", {"class": "a-link-normal a-text-normal"}):
                if f"https://www.amazon.in/{link.get('href')}" in links:
                    continue
                if "dp/" in f"https://www.amazon.in/{link.get('href')}":
                    asin = link.get('href').split("dp/")[1].split("/")[0]
                    asins.append(asin)
                    links.append(f"https://www.amazon.in/{link.get('href')}")

            for img in soup.find_all("img", {"class": "a-dynamic-image p13n-sc-dynamic-image p13n-product-image"}):
                images.append(img.get('src'))

            for index in range(len(links)):
                data = {"ASIN": asins[index], "Web_Page_URL": links[index], "Title": titles[index],
                        "Price": prices[index],
                        "MRP": 0, "Image_URL": images[index]}
                more_choices.append(data)

        meta_data["data"]["More_Buying_Choices"] = more_choices
        yield meta_data
