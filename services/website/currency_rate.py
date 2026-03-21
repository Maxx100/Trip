from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class CurrencyRate:
    def __init__(self):
        self.URL = 'https://tour-kassa.ru/%D0%BA%D1%83%D1%80%D1%81%D1%8B-%D0%B2%D0%B0%D0%BB%D1%8E%D1%82-%D1%82%D1%83%D1%80%D0%BE%D0%BF%D0%B5%D1%80%D0%B0%D1%82%D0%BE%D1%80%D0%BE%D0%B2'
        self.options = Options()
        self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=self.options)
        self.table_today = []
        self.table_tomorrow = []
    
    def table_to_dict(self, table):
        data = []
        rows = table.find_all('tr')
        for row in rows:
            cells = [c.get_text(strip=True) for c in row.find_all(['th', 'td'])]
            if cells:
                data.append(cells)
        data.pop(0)
        for i in range(len(data)):
            data[i] = [data[i][0].split('ИКС:')[0], float(data[i][1]), float(data[i][4])]
        return data
    
    def update(self):
        try:
            self.driver.get(self.URL)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'table'))
            )
            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            tables = soup.find_all('table')
            if len(tables) != 4:
                raise ValueError(f"Expected 4 tables, but found {len(tables)}")
            self.table_today = self.table_to_dict(tables[1])
            self.table_tomorrow = self.table_to_dict(tables[2])

        except Exception as e:
            logger.error(f"Error fetching currency rates: {e}")
    
    def __str__(self):
        return f"Today's Rates: {self.table_today}\nTomorrow's Rates: {self.table_tomorrow}"


if __name__ == "__main__":
    currency_rate = CurrencyRate()
    currency_rate.update()
    print(currency_rate)
