import logging
from typing import Any

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)


class CurrencyRate:
    def __init__(self):
        self.url = "https://tour-kassa.ru/%D0%BA%D1%83%D1%80%D1%81%D1%8B-%D0%B2%D0%B0%D0%BB%D1%8E%D1%82-%D1%82%D1%83%D1%80%D0%BE%D0%BF%D0%B5%D1%80%D0%B0%D1%82%D0%BE%D1%80%D0%BE%D0%B2"
    
    def _build_options(self) -> Options:
        options = Options()
        options.binary_location = "/usr/bin/chromium"
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        return options

    def _table_to_list(self, table) -> list[list[Any]]:
        data = []
        rows = table.find_all("tr")
        for row in rows:
            cells = [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
            if cells:
                data.append(cells)

        if data:
            data = data[1:]

        parsed: list[list[Any]] = []
        for row in data:
            if len(row) < 5:
                continue
            try:
                operator_name = row[0].split("ИКС:")[0].strip()
                eur_value = float(row[1].replace(",", "."))
                usd_value = float(row[4].replace(",", "."))
                parsed.append([operator_name, eur_value, usd_value])
            except ValueError:
                continue

        return parsed

    def fetch(self) -> dict[str, list[list[Any]]]:
        service = Service(executable_path="/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=self._build_options())
        try:
            driver.get(self.url)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))

            soup = BeautifulSoup(driver.page_source, "html.parser")
            tables = soup.find_all("table")
            if len(tables) < 3:
                raise ValueError(f"Expected at least 3 tables, but found {len(tables)}")

            return {
                "today": self._table_to_list(tables[1]),
                "tomorrow": self._table_to_list(tables[2]),
            }
        finally:
            driver.quit()

    def update(self) -> tuple[list[list[Any]], list[list[Any]]]:
        data = self.fetch()
        return data["today"], data["tomorrow"]

    def __str__(self):
        try:
            data = self.fetch()
            return f"Today's Rates: {data['today']}\nTomorrow's Rates: {data['tomorrow']}"
        except Exception as error:
            logger.error(f"Error fetching currency rates: {error}")
            return "Currency rates are unavailable"


if __name__ == "__main__":
    currency_rate = CurrencyRate()
    try:
        rates = currency_rate.fetch()
        print(f"Today's Rates: {rates['today']}")
        print(f"Tomorrow's Rates: {rates['tomorrow']}")
    except Exception as error:
        logger.error(f"Error fetching currency rates: {error}")
