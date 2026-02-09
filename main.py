 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/main.py b/main.py
new file mode 100644
index 0000000000000000000000000000000000000000..e082cc32c278f6f8125decc36c09c8462ad2e4b9
--- /dev/null
+++ b/main.py
@@ -0,0 +1,234 @@
+#!/usr/bin/env python3
+"""Simple BaZi (Eight Characters) element analysis and 4D recommendation."""
+
+from __future__ import annotations
+
+import datetime as dt
+import hashlib
+import random
+from dataclasses import dataclass
+from typing import Dict, List, Tuple
+
+STEMS = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
+BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
+
+ELEMENTS_BY_STEM = {
+    "甲": "木",
+    "乙": "木",
+    "丙": "火",
+    "丁": "火",
+    "戊": "土",
+    "己": "土",
+    "庚": "金",
+    "辛": "金",
+    "壬": "水",
+    "癸": "水",
+}
+
+ELEMENTS_BY_BRANCH = {
+    "子": "水",
+    "丑": "土",
+    "寅": "木",
+    "卯": "木",
+    "辰": "土",
+    "巳": "火",
+    "午": "火",
+    "未": "土",
+    "申": "金",
+    "酉": "金",
+    "戌": "土",
+    "亥": "水",
+}
+
+MONTH_BRANCHES_BY_GREGORIAN = {
+    1: "丑",
+    2: "寅",
+    3: "卯",
+    4: "辰",
+    5: "巳",
+    6: "午",
+    7: "未",
+    8: "申",
+    9: "酉",
+    10: "戌",
+    11: "亥",
+    12: "子",
+}
+
+HOUR_BRANCHES = [
+    (23, 1, "子"),
+    (1, 3, "丑"),
+    (3, 5, "寅"),
+    (5, 7, "卯"),
+    (7, 9, "辰"),
+    (9, 11, "巳"),
+    (11, 13, "午"),
+    (13, 15, "未"),
+    (15, 17, "申"),
+    (17, 19, "酉"),
+    (19, 21, "戌"),
+    (21, 23, "亥"),
+]
+
+MONTH_STEM_START = {
+    "甲": "丙",
+    "己": "丙",
+    "乙": "戊",
+    "庚": "戊",
+    "丙": "庚",
+    "辛": "庚",
+    "丁": "壬",
+    "壬": "壬",
+    "戊": "甲",
+    "癸": "甲",
+}
+
+HOUR_STEM_START = {
+    "甲": "甲",
+    "己": "甲",
+    "乙": "丙",
+    "庚": "丙",
+    "丙": "戊",
+    "辛": "戊",
+    "丁": "庚",
+    "壬": "庚",
+    "戊": "壬",
+    "癸": "壬",
+}
+
+ELEMENT_DIGITS = {
+    "木": [3, 4],
+    "火": [9],
+    "土": [2, 5, 8],
+    "金": [6, 7],
+    "水": [0, 1],
+}
+
+
+@dataclass
+class BaZi:
+    year: Tuple[str, str]
+    month: Tuple[str, str]
+    day: Tuple[str, str]
+    hour: Tuple[str, str]
+
+    def pillars(self) -> List[Tuple[str, str]]:
+        return [self.year, self.month, self.day, self.hour]
+
+
+def _stem_branch_from_index(index: int) -> Tuple[str, str]:
+    return STEMS[index % 10], BRANCHES[index % 12]
+
+
+def _day_index_from_base(date_value: dt.date) -> int:
+    base = dt.date(1984, 2, 2)  # 甲子日 (simple base)
+    delta = date_value - base
+    return delta.days
+
+
+def year_pillar(date_value: dt.date) -> Tuple[str, str]:
+    index = date_value.year - 1984
+    return _stem_branch_from_index(index)
+
+
+def month_pillar(date_value: dt.date, year_stem: str) -> Tuple[str, str]:
+    branch = MONTH_BRANCHES_BY_GREGORIAN[date_value.month]
+    start_stem = MONTH_STEM_START[year_stem]
+    start_index = STEMS.index(start_stem)
+    month_index = (date_value.month - 1) % 12
+    stem = STEMS[(start_index + month_index) % 10]
+    return stem, branch
+
+
+def day_pillar(date_value: dt.date) -> Tuple[str, str]:
+    index = _day_index_from_base(date_value)
+    return _stem_branch_from_index(index)
+
+
+def hour_pillar(time_value: dt.time, day_stem: str) -> Tuple[str, str]:
+    hour = time_value.hour
+    branch = "子"
+    for start, end, value in HOUR_BRANCHES:
+        if start <= end and start <= hour < end:
+            branch = value
+            break
+        if start > end and (hour >= start or hour < end):
+            branch = value
+            break
+    start_stem = HOUR_STEM_START[day_stem]
+    start_index = STEMS.index(start_stem)
+    branch_index = BRANCHES.index(branch)
+    stem = STEMS[(start_index + branch_index) % 10]
+    return stem, branch
+
+
+def compute_bazi(date_value: dt.date, time_value: dt.time) -> BaZi:
+    year = year_pillar(date_value)
+    month = month_pillar(date_value, year[0])
+    day = day_pillar(date_value)
+    hour = hour_pillar(time_value, day[0])
+    return BaZi(year=year, month=month, day=day, hour=hour)
+
+
+def element_strength(bazi: BaZi) -> Dict[str, int]:
+    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
+    for stem, branch in bazi.pillars():
+        counts[ELEMENTS_BY_STEM[stem]] += 1
+        counts[ELEMENTS_BY_BRANCH[branch]] += 1
+    return counts
+
+
+def recommend_numbers(
+    seed: str, element_counts: Dict[str, int], sets: int = 5
+) -> List[Tuple[str, str]]:
+    sorted_elements = sorted(element_counts.items(), key=lambda item: item[1])
+    weak_elements = [element for element, _ in sorted_elements[:2]]
+    digits_pool = [digit for element in weak_elements for digit in ELEMENT_DIGITS[element]]
+    if not digits_pool:
+        digits_pool = [digit for digits in ELEMENT_DIGITS.values() for digit in digits]
+    seed_hash = hashlib.sha256(seed.encode("utf-8")).hexdigest()
+    rng = random.Random(int(seed_hash, 16))
+    recommendations = []
+    for _ in range(sets):
+        number = "".join(str(rng.choice(digits_pool)) for _ in range(4))
+        explanation = (
+            "偏弱元素: "
+            + "、".join(weak_elements)
+            + " | 使用对应数字: "
+            + ", ".join(str(d) for d in sorted(set(digits_pool)))
+        )
+        recommendations.append((number, explanation))
+    return recommendations
+
+
+def parse_datetime(input_value: str) -> dt.datetime:
+    for fmt in ("%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"):
+        try:
+            return dt.datetime.strptime(input_value.strip(), fmt)
+        except ValueError:
+            continue
+    raise ValueError("请输入格式: YYYY-MM-DD HH:MM")
+
+
+def main() -> None:
+    print("请输入出生年月日与时间 (YYYY-MM-DD HH:MM): ", end="")
+    raw = input().strip()
+    dt_value = parse_datetime(raw)
+    bazi = compute_bazi(dt_value.date(), dt_value.time())
+    counts = element_strength(bazi)
+    print("\n八字:")
+    labels = ["年", "月", "日", "时"]
+    for label, (stem, branch) in zip(labels, bazi.pillars()):
+        print(f"{label}柱: {stem}{branch}")
+    print("\n五行强弱:")
+    for element, count in counts.items():
+        print(f"{element}: {count}")
+    print("\n推荐 4D 号码:")
+    for idx, (number, explanation) in enumerate(
+        recommend_numbers(raw, counts), start=1
+    ):
+        print(f"{idx}. {number} ({explanation})")
+
+
+if __name__ == "__main__":
+    main()
 
EOF
)
