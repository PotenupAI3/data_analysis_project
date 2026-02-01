import json
import re


def parse_kosis_loose(text: str):
    """
    KOSIS에서 내려오는 [{OBJ_ID:"A", ...}] 형태(키 따옴표 없음)를
    JSON으로 보정해서 list[dict]로 변환
    """
    t = text.strip()

    # {KEY: 또는 ,KEY: 를 {"KEY": 로 변환
    t = re.sub(r"([{,]\s*)([A-Za-z0-9_]+)\s*:", r'\1"\2":', t)

    # 혹시 값이 '...'로 오는 경우까지 대비(현재는 "..."라 그대로 OK)
    t = t.replace("'", '"')

    return json.loads(t)


def Hello():
    print("World")
