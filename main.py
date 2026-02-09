#!/usr/bin/env python3
"""Simple BaZi (Eight Characters) element analysis and 4D recommendation."""

from __future__ import annotations

import datetime as dt
import hashlib
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

ELEMENTS_BY_STEM = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

ELEMENTS_BY_BRANCH = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

MONTH_BRANCHES_BY_GREGORIAN = {
    1: "丑", 2: "寅", 3: "卯", 4: "辰",
    5: "巳", 6: "午", 7: "未", 8: "申",
    9: "酉", 10: "戌", 11: "亥", 12: "子",
}

HOUR_BRANCHES = [
    (23, 1, "子"), (1, 3, "丑"), (3, 5, "寅"), (5, 7, "卯"),
    (7, 9, "辰"), (9, 11, "巳"), (11, 13, "午"), (13, 15, "未"),
    (15, 17, "申"), (17, 19, "酉"), (19, 21, "戌"), (21, 23, "亥"),
]

MONTH_STEM_START = {
    "甲": "丙", "己": "丙",
    "乙": "戊", "庚": "戊",
    "丙": "庚", "辛": "庚",
    "丁": "壬", "壬": "壬",
    "戊": "甲", "癸": "甲",
}

HOUR_STEM_START = {
    "甲": "甲", "己": "甲",
    "乙": "丙", "庚": "丙",
    "丙": "戊", "辛": "戊",
    "丁": "庚", "壬": "庚",
    "戊": "壬", "癸": "壬",
}

ELEMENT_DIGITS = {
    "木": [3, 4],
    "火": [9],
    "土": [2, 5, 8],
    "金": [6, 7],
    "水": [0, 1],
}


@dataclass
class BaZi:
    year: Tuple[str, str]
    month: Tuple[str, str]
    day: Tuple[str, str]
    hour: Tuple[str, str]

    def pillars(self) -> List[Tuple[str, str]]:
        return [self.year, self.month, self.day, self.hour]


def _stem_branch_from_index(index: int) -> Tuple[str, str]:
    return STEMS[index % 10], BRANCHES[index % 12]


def _day_index_from_base(date_value: dt.date) -> int:
    base = dt.date(1984, 2, 2)  # 甲子日
    return (date_value - base).days


def year_pillar(date_value: dt.date) -> Tuple[str, str]:
    return _stem_branch_from_index(date_value.year - 1984)


def month_pillar(date_value: dt.date, year_stem: str) -> Tuple[str, str]:
    branch = MONTH_BRANCHES_BY_GREGORIAN[date_value.month]
    start_stem = MONTH_STEM_START[year_stem]
    stem_index = (STEMS.index(start_stem) + date_value.month - 1) % 10
    return STEMS[stem_index], branch


def day_pillar(date_value: dt.date) -> Tuple[str, str]:
    return _stem_branch_from_index(_day_index_from_base(date_value))


def hour_pillar(time_value: dt.time, day_stem: str) -> Tuple[str, str]:
    hour = time_value.hour
    branch = "子"
    for start, end, b in HOUR_BRANCHES:
        if start <= end and start <= hour < end:
            branch = b
            break
        if start > end and (hour >= start or hour < end):
            branch = b
            break
    stem_index = (STEMS.index(HOUR_STEM_START[day_stem]) + BRANCHES.index(branch)) % 10
    return STEMS[stem_index], branch


def compute_bazi(date_value: dt.date, time_value: dt.time) -> BaZi:
    year = year_pillar(date_value)
    month = month_pillar(date_value, year[0])
    day = day_pillar(date_value)
    hour = hour_pillar(time_value, day[0])
    return BaZi(year, month, day, hour)


def element_strength(bazi: BaZi) -> Dict[str, int]:
    counts = {e: 0 for e in ELEMENT_DIGITS}
    for stem, branch in bazi.pillars():
        counts[ELEMENTS_BY_STEM[stem]] += 1
        counts[ELEMENTS_BY_BRANCH[branch]] += 1
    return counts


def recommend_numbers(seed: str, counts: Dict[str, int], sets: int = 5):
    weak = sorted(counts, key=counts.get)[:2]
    pool = [d for e in weak for d in ELEMENT_DIGITS[e]]
    seed_hash = hashlib.sha256(seed.encode()).hexdigest()
    rng = random.Random(int(seed_hash, 16))
    result = []
    for _ in range(sets):
        num = "".join(str(rng.choice(pool)) for _ in range(4))
        result.append((num, f"偏弱元素: {'、'.join(weak)}"))
    return result


def parse_datetime(s: str) -> dt.datetime:
    for fmt in ("%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError("请输入格式 YYYY-MM-DD HH:MM")


def main():
    raw = input("请输入出生年月日与时间 (YYYY-MM-DD HH:MM): ").strip()
    dtv = parse_datetime(raw)
    bazi = compute_bazi(dtv.date(), dtv.time())
    counts = element_strength(bazi)

    print("\n八字:")
    for label, (s, b) in zip(["年", "月", "日", "时"], bazi.pillars()):
        print(f"{label}柱: {s}{b}")

    print("\n五行强弱:")
    for k, v in counts.items():
        print(f"{k}: {v}")

    print("\n推荐 4D 号码:")
    for i, (n, exp) in enumerate(recommend_numbers(raw, counts), 1):
        print(f"{i}. {n} ({exp})")


if __name__ == "__main__":
    main()
