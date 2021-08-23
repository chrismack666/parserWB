import csv
import bs4
import requests
import logging
import collections
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('wb')

ParseResult = collections.namedtuple(
    'ParseResult',
    (
        'url'
    )
)

class Client:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Accept-Language': 'ru'
        }
        self.result = []

    def load_page(self, url: str):

        try:
            res = self.session.get(url=url)
        except ConnectionError:
            logger.error("Connection error on " + url)

        res.raise_for_status()
        return res.text

    def parse_page(self, url: str):
        driver = webdriver.Chrome("C:\Program Files (x86)\Chromedriver\chromedriver.exe")
        driver.get(url)
        WebDriverWait(driver, 5).until(lambda driver: driver.find_element_by_class_name("j-menu-item"))
        soup = bs4.BeautifulSoup(driver.page_source, "lxml")
        driver.quit()

        url_block = soup.select('a.j-menu-item')
        logger.debug(len(url_block))
        for elem in url_block:
            url = elem.get('href')
            if not url:
                logger.error('no href on ' + url)
                return
            else:
                url = 'https://www.wildberries.ru' + url
            self.result.append(ParseResult(
                url=url
            ))







    def save_result(self):
        path = 'C:/Users/User/parser/wb/links.csv'
        with open(path, 'a', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            for item in self.result:
                writer.writerow(item)

    def run(self):
        urls = [
            'https://www.wildberries.ru/catalog/aksessuary',
            'https://www.wildberries.ru/catalog/elektronika',
            'https://www.wildberries.ru/catalog/knigi',
            'https://www.wildberries.ru/catalog/krasota',
            'https://www.wildberries.ru/catalog/igrushki',
            'https://www.wildberries.ru/catalog/tovary-dlya-zhivotnyh',
            'https://www.wildberries.ru/catalog/dom-i-dacha/instrumenty',
            'https://www.wildberries.ru/catalog/dom-i-dacha',
            'https://www.wildberries.ru/catalog/aksessuary/avtotovary',
            'https://www.wildberries.ru/catalog/yuvelirnye-ukrasheniya'
        ]
        for url in urls:
            logger.info('Parse: ' + url)
            self.parse_page(url=url)
            self.save_result()


if __name__ == '__main__':
    parser = Client()
    parser.run()