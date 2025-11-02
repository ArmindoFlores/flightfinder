import datetime
from typing import TypedDict


class SearchParams(TypedDict):
    currency: str
    origin: str
    destination: str
    return_journey: bool
    start_date: datetime.date
    end_date: datetime.date

    @staticmethod
    def _value_to_string(value):
        return str(value)

class SearchResults(TypedDict):
    price: float
    datetime: datetime.datetime
    provider: str
