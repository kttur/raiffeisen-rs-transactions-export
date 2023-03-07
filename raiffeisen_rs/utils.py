import json


def decode_response(response):
    text = response.text
    text_without_bom = text.encode().decode('utf-8-sig')
    return json.loads(text_without_bom)
