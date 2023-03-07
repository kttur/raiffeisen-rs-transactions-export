import json
from datetime import date, datetime


def decode_response(response):
    text = response.text
    text_without_bom = text.encode().decode('utf-8-sig')
    return json.loads(text_without_bom)


def parse_date(dt: str | datetime | date | int) -> str | None:
    date_format = '%d.%m.%Y'
    match dt:
        case str():
            try:
                return date.fromisoformat(dt).strftime(date_format)
            except ValueError:
                pass
            try:
                return datetime.strptime(dt, date_format).strftime(date_format)
            except ValueError:
                raise ValueError(f'Unsupported date format {dt}. Supported format is {date_format} or ISO format')
        case date() | datetime():
            return dt.strftime(date_format)
        case int():
            return datetime.fromtimestamp(dt).strftime(date_format)
        case None:
            return None
        case _:
            raise TypeError(f'Unsupported type {type(dt)}')
