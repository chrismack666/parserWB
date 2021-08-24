import csv
import time

import bs4
import requests
import logging
import collections
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('wb')

ParseResult = collections.namedtuple(
    'ParseResult',
    (
        'brand_name',
        'goods_name',
        'price',
        'orders_count',
        'first_feedback_date',
        'url'
    )
)
index = 0

class Client:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Accept-Language': 'ru'
        }
        self.result = []

    def load_page(self, url: str):
        res = self.session.get(url=url)
        res.raise_for_status()
        return res.text

    def parse_page(self, text: str):
        soup = bs4.BeautifulSoup(text, 'lxml')
        container = soup.select('div.product-card.j-card-item')
        for block in container:
            self.parse_block(block=block)

    def parse_block(self, block):

        url_block = block.select_one('a.product-card__main.j-open-full-product-card')
        if not url_block:
            logger.error('no url_block')
            return

        url = url_block.get('href')
        if not url:
            logger.error('no href on ' + url)
            return
        else:
            url = 'https://www.wildberries.ru' + url

        name_block = block.select_one('div.product-card__brand')
        if not name_block:
            logger.error('no name_block on ' + url)
            return

        brand_name = name_block.select_one('strong.brand-name')
        if not brand_name:
            logger.error(f'no brand_name on {url}')
            return
        brand_name = brand_name.text.replace('/','').strip()

        goods_name = name_block.select_one('span.goods-name')
        if not goods_name:
            logger.error(f'no goods_name on {url}')
            return
        goods_name = goods_name.text

        price = name_block.select_one('ins.lower-price')
        if not price:
            logger.error(f'no price on {url}')
            return
        price = str(price.text).split(' ₽')[0]

        text = self.load_page(url)
        soup = bs4.BeautifulSoup(text, 'lxml')
        scripts = soup.findAll('script')
        orders_count = self.parse_orders_count(scripts=scripts)
        first_feedback_date = self.parse_first_feedback_date(url=url, scripts=scripts)

        self.result.append(ParseResult(
            url=url,
            brand_name=brand_name,
            goods_name=goods_name,
            price = price,
            orders_count = orders_count,
            first_feedback_date = first_feedback_date
        ))
        global index
        index += 1
        logger.debug('index = ' + str(index))
        if index % 10 == 0:
            self.save_result()
            self.result.clear()

    def parse_orders_count(self, scripts: str):
        orders_count = str(scripts[24]).split('ordersCount":')[1].split(',')[0]
        return orders_count

    def parse_first_feedback_date(self, url: str, scripts):
        feedbacks_count = str(scripts[24]).split('feedbacksCount":')[1].split(',')[0]
        logger.info('feedbacks_count = ' + feedbacks_count)

        if feedbacks_count == '0':
            return 'no feedbacks'
        else:
            driver = webdriver.Chrome("C:\Program Files (x86)\Chromedriver\chromedriver.exe")
            driver.get(url + '#Comments')
            driver.execute_script("window.scrollBy(0, -200);")

            if feedbacks_count == '1':
                try:
                    WebDriverWait(driver, 5).until(lambda driver: driver.find_element_by_class_name("feedback__date"))
                    soup = bs4.BeautifulSoup(driver.page_source, "lxml")
                    feedback_date = soup.select_one('span.feedback__date')
                except TimeoutException:
                    logger.error("NO ELEMENT, Timeout Exception on " + url)
                finally:
                    driver.quit()
            else:
                try:
                    WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_class_name("sorting__item"))
                    option = driver.find_element_by_class_name('sorting__item')
                    ActionChains(driver).move_to_element(option).perform()
                    option.click()
                    time.sleep(0.5)
                except Exception:
                    logger.error('Cant click on ' + url)
                    driver.quit()
                    return 'cant click on feedback'

                try:
                    WebDriverWait(driver, 10).until(lambda driver: driver.find_element_by_class_name("feedback__date"))
                    soup = bs4.BeautifulSoup(driver.page_source, "lxml")
                    feedback_date = soup.select_one('span.feedback__date')
                except TimeoutException:
                    logger.error("NO ELEMENT, Timeout Exception on " + url)
                finally:
                    driver.quit()

                if not feedback_date:
                    logger.error(f'no feedbacks on {url}')
                    return 'no feedbacks'
                else:
                    logger.info(feedback_date['content'])

            return feedback_date['content']

    def save_result(self):
        path = 'C:/Users/User/parser/wb/result.csv'
        with open(path, 'a', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            for item in self.result:
                writer.writerow(item)

    def run(self):
        max_page = 2
        category_urls = [
            'https://www.wildberries.ru/catalog/aksessuary/dekor-dlya-odezhdy',
            'https://www.wildberries.ru/catalog/aksessuary/bizhuteriya',
            'https://www.wildberries.ru/catalog/aksessuary/veera',
            'https://www.wildberries.ru/catalog/aksessuary/galstuki-i-babochki',
            'https://www.wildberries.ru/catalog/aksessuary/golovnye-ubory',
            'https://www.wildberries.ru/catalog/aksessuary/zerkaltsa',
            'https://www.wildberries.ru/catalog/aksessuary/zonty',
            'https://www.wildberries.ru/catalog/aksessuary/koshelki-i-kreditnitsy',
            'https://www.wildberries.ru/catalog/aksessuary/maski-dlya-sna',
            'https://www.wildberries.ru/catalog/aksessuary/nosovye-platki',
            'https://www.wildberries.ru/catalog/aksessuary/ochki-i-futlyary',
            'https://www.wildberries.ru/catalog/aksessuary/perchatki-i-varezhki',
            'https://www.wildberries.ru/catalog/aksessuary/platki-i-sharfy',
            'https://www.wildberries.ru/catalog/aksessuary/religioznye',
            'https://www.wildberries.ru/catalog/aksessuary/remni-i-poyasa',
            'https://www.wildberries.ru/catalog/aksessuary/sumki-i-ryukzaki',
            'https://www.wildberries.ru/catalog/aksessuary/chasy-i-remeshki'
        ]
        urls = []
        for category_url in category_urls:
            category_url = category_url + '?sort=popular&page=1&priceU=0%3B150000'
            for i in range(1, max_page):
                urls.append(category_url.replace('page=1', 'page=' + str(i)))
        for url in urls:
            start_time = time.time()
            logger.info('Parse: ' + url)
            text = self.load_page(url)
            self.parse_page(text=text)
            self.save_result()
            self.result.clear()
            end_time = time.time() - start_time
            logger.info(str(end_time) + 's ___ saved ' + url)


if __name__ == '__main__':
    parser = Client()
    parser.run()