import logging
import re
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

    @staticmethod
    def _parse_float(raw_value: str) -> float:
        match = re.search(r"[-+]?\d+[.,]?\d*", raw_value.replace(" ", ""))
        if not match:
            raise ValueError(f"No numeric value found in: {raw_value}")
        return float(match.group(0).replace(",", "."))

    @staticmethod
    def _normalize_operator_name(name: str) -> str:
        lowered = name.lower().replace("ё", "е")
        return re.sub(r"[^a-zа-я0-9]+", "", lowered)

    def _should_skip_operator(self, operator_name: str) -> bool:
        normalized = self._normalize_operator_name(operator_name)
        blocked_fragments = (
            "сабре",
            "sabre",
            "тезтур",
            "teztour",
            "tez",
            "туркасса",
            "tourkassa",
            "пакс",
            "paks",
            "pax",
        )
        return any(fragment in normalized for fragment in blocked_fragments)

    def _table_to_list(self, table) -> list[list[Any]]:
        data = []
        rows = table.find_all("tr")
        for row in rows:
            cells = [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
            if cells:
                data.append(cells)

        if not data:
            return []

        header = [cell.lower() for cell in data[0]]

        operator_idx = 0
        eur_idx = next((index for index, value in enumerate(header) if "eur" in value or "евр" in value), 1)
        usd_idx = next((index for index, value in enumerate(header) if "usd" in value or "долл" in value), 4)

        data = data[1:]

        parsed: list[list[Any]] = []
        for row in data:
            required_index = max(operator_idx, eur_idx, usd_idx)
            if len(row) <= required_index:
                continue
            try:
                operator_name = row[operator_idx].split("ИКС:")[0].strip()
                if not operator_name:
                    continue
                if self._should_skip_operator(operator_name):
                    continue
                eur_value = self._parse_float(row[eur_idx])
                usd_value = self._parse_float(row[usd_idx])
                parsed.append([operator_name, eur_value, usd_value])
            except ValueError:
                continue

        return parsed

    def _find_operator_table(self, soup: BeautifulSoup):
        tables = soup.find_all("table")

        def table_score(table) -> tuple[int, int]:
            rows = table.find_all("tr")
            header_text = " ".join(th.get_text(" ", strip=True).lower() for th in table.find_all("th"))
            score = 0
            if "туроператор" in header_text:
                score += 4
            if "usd" in header_text or "долл" in header_text:
                score += 2
            if "eur" in header_text or "евр" in header_text:
                score += 2
            return score, len(rows)

        if not tables:
            return None

        ranked = sorted(tables, key=table_score, reverse=True)
        return ranked[0]

    def _extract_cbr_rates_from_tables(self, soup: BeautifulSoup) -> tuple[float | None, float | None, float | None, float | None]:
        usd_today = usd_tomorrow = eur_today = eur_tomorrow = None

        for table in soup.find_all("table"):
            table_text = table.get_text(" ", strip=True).lower()
            if "цб" not in table_text and "прогноз" not in table_text:
                continue

            for row in table.find_all("tr"):
                row_text = row.get_text(" ", strip=True).lower()
                if "завтра" not in row_text:
                    continue
                numbers = [self._parse_float(match) for match in re.findall(r"\d+[.,]\d+", row_text)]
                if len(numbers) < 2:
                    continue
                if "usd" in row_text or "доллар" in row_text:
                    usd_today, usd_tomorrow = numbers[0], numbers[1]
                if "eur" in row_text or "евро" in row_text:
                    eur_today, eur_tomorrow = numbers[0], numbers[1]

            if all(value is not None for value in [usd_today, usd_tomorrow, eur_today, eur_tomorrow]):
                return usd_today, usd_tomorrow, eur_today, eur_tomorrow

        return usd_today, usd_tomorrow, eur_today, eur_tomorrow

    def _extract_cbr_rates_from_widget(self, soup: BeautifulSoup) -> tuple[float | None, float | None, float | None, float | None]:
        key_map = {
            "eur-cbr-today": None,
            "eur-tomorrow": None,
            "usd-cbr-today": None,
            "usd-tomorrow": None,
        }

        for key in key_map:
            node = soup.select_one(f".tmw-item[data-key='{key}'] .tmw-value")
            if node:
                try:
                    key_map[key] = self._parse_float(node.get_text(" ", strip=True))
                except ValueError:
                    key_map[key] = None

        return (
            key_map["usd-cbr-today"],
            key_map["usd-tomorrow"],
            key_map["eur-cbr-today"],
            key_map["eur-tomorrow"],
        )

    def _extract_cbr_rates_from_text(self, soup: BeautifulSoup) -> tuple[float | None, float | None, float | None, float | None]:
        full_text = soup.get_text(" ", strip=True)
        normalized = full_text.replace("\xa0", " ")
        lower = normalized.lower()

        anchor_index = -1
        for keyword in ("прогноз", "цб", "центробанк", "центральный банк"):
            anchor_index = lower.find(keyword)
            if anchor_index != -1:
                break

        segment = normalized[max(0, anchor_index - 600): anchor_index + 2400] if anchor_index != -1 else normalized

        def extract_pair(code_pattern: str) -> tuple[float | None, float | None]:
            pattern = rf"{code_pattern}[^\d]{{0,80}}(\d+[.,]\d+)[^\d]{{0,80}}(\d+[.,]\d+)"
            match = re.search(pattern, segment, flags=re.IGNORECASE)
            if not match:
                return None, None
            return self._parse_float(match.group(1)), self._parse_float(match.group(2))

        usd_today, usd_tomorrow = extract_pair(r"(?:usd|доллар)")
        eur_today, eur_tomorrow = extract_pair(r"(?:eur|евро)")
        return usd_today, usd_tomorrow, eur_today, eur_tomorrow

    def _extract_cbr_change_ratios(self, soup: BeautifulSoup) -> tuple[float, float]:
        usd_today, usd_tomorrow, eur_today, eur_tomorrow = self._extract_cbr_rates_from_widget(soup)

        if None in (usd_today, usd_tomorrow, eur_today, eur_tomorrow):
            table_values = self._extract_cbr_rates_from_tables(soup)
            usd_today = usd_today if usd_today is not None else table_values[0]
            usd_tomorrow = usd_tomorrow if usd_tomorrow is not None else table_values[1]
            eur_today = eur_today if eur_today is not None else table_values[2]
            eur_tomorrow = eur_tomorrow if eur_tomorrow is not None else table_values[3]

        if None in (usd_today, usd_tomorrow, eur_today, eur_tomorrow):
            text_values = self._extract_cbr_rates_from_text(soup)
            usd_today = usd_today if usd_today is not None else text_values[0]
            usd_tomorrow = usd_tomorrow if usd_tomorrow is not None else text_values[1]
            eur_today = eur_today if eur_today is not None else text_values[2]
            eur_tomorrow = eur_tomorrow if eur_tomorrow is not None else text_values[3]

        usd_ratio = 1.0
        eur_ratio = 1.0

        if usd_today and usd_tomorrow and usd_today > 0:
            usd_ratio = usd_tomorrow / usd_today
        else:
            logger.warning("Could not determine USD CBR forecast ratio; fallback to 1.0")

        if eur_today and eur_tomorrow and eur_today > 0:
            eur_ratio = eur_tomorrow / eur_today
        else:
            logger.warning("Could not determine EUR CBR forecast ratio; fallback to 1.0")

        return usd_ratio, eur_ratio

    def fetch(self) -> dict[str, list[list[Any]]]:
        service = Service(executable_path="/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=self._build_options())
        try:
            driver.get(self.url)
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))

            soup = BeautifulSoup(driver.page_source, "html.parser")
            operator_table = self._find_operator_table(soup)
            if operator_table is None:
                raise ValueError("Could not find operator rates table on source page")

            today = self._table_to_list(operator_table)
            if not today:
                raise ValueError("Operator rates table was found but no rows could be parsed")

            usd_ratio, eur_ratio = self._extract_cbr_change_ratios(soup)
            tomorrow = [
                [
                    operator_name,
                    round(eur_value * eur_ratio, 2),
                    round(usd_value * usd_ratio, 2),
                ]
                for operator_name, eur_value, usd_value in today
            ]

            return {
                "today": today,
                "tomorrow": tomorrow,
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
