import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

logger = logging.getLogger(__name__)

CBR_DAILY_URL = "https://www.cbr-xml-daily.ru/daily_json.js"
CBR_ARCHIVE_URL = "https://www.cbr-xml-daily.ru/archive/{year}/{month:02d}/{day:02d}/daily_json.js"
MOSCOW_TZ = timezone(timedelta(hours=3))
REQUEST_TIMEOUT = 20


class CurrencyRate:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "trip-kzn.ru currency widget"})

    def _get_json(self, url: str) -> dict | None:
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as error:
            logger.warning("Failed to fetch CBR data from %s: %s", url, error)
            return None

    @staticmethod
    def _extract_pair(payload: dict) -> tuple[float, float]:
        valute = payload["Valute"]
        eur = float(valute["EUR"]["Value"])
        usd = float(valute["USD"]["Value"])
        return round(eur, 2), round(usd, 2)

    def _fetch_for_date(self, day) -> tuple[float, float] | None:
        payload = self._get_json(
            CBR_ARCHIVE_URL.format(year=day.year, month=day.month, day=day.day)
        )
        if not payload:
            return None
        try:
            return self._extract_pair(payload)
        except (KeyError, TypeError, ValueError):
            return None

    def fetch(self) -> dict[str, list[list[Any]]]:
        payload = self._get_json(CBR_DAILY_URL)
        if not payload:
            raise RuntimeError("Could not fetch CBR daily rates")

        eur_today, usd_today = self._extract_pair(payload)
        today = [["ЦБ РФ", eur_today, usd_today]]

        tomorrow_date = datetime.now(MOSCOW_TZ).date() + timedelta(days=1)
        tomorrow_pair = self._fetch_for_date(tomorrow_date)
        if tomorrow_pair:
            tomorrow = [["ЦБ РФ", tomorrow_pair[0], tomorrow_pair[1]]]
        else:
            tomorrow = today

        return {"today": today, "tomorrow": tomorrow}


if __name__ == "__main__":
    currency_rate = CurrencyRate()
    try:
        rates = currency_rate.fetch()
        print(f"Today's Rates: {rates['today']}")
        print(f"Tomorrow's Rates: {rates['tomorrow']}")
    except Exception as error:
        logger.error(f"Error fetching currency rates: {error}")
