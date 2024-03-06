from typing import Optional
import datetime


def parse_date(date: Optional[str]) -> datetime.date:
    if not date:
        return

    return datetime.datetime.strptime(date, '%d/%m/%Y').date()
