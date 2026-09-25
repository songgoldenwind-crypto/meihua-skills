# -*- coding: utf-8 -*-
"""
梅花易数 · 起卦引擎
古法两数起卦：上卦=首数÷8取余，下卦=次数÷8取余，动爻=两数之和÷6取余。
提供本卦 / 互卦 / 变卦计算、体用划分与五行生克判定。
"""
import json
import os

# 先天八卦（序 0-7，爻自下而上，1=阳 0=阴）序：乾兑离震巽坎艮坤
GUA = {
    "乾": {"num": 1, "wu": "金", "lines": (1, 1, 1), "symbol": "☰"},
    "兑": {"num": 2, "wu": "金", "lines": (1, 1, 0), "symbol": "☱"},
    "离": {"num": 3, "wu": "火", "lines": (1, 0, 1), "symbol": "☲"},
    "震": {"num": 4, "wu": "木", "lines": (1, 0, 0), "symbol": "☳"},
    "巽": {"num": 5, "wu": "木", "lines": (0, 1, 1), "symbol": "☴"},
    "坎": {"num": 6, "wu": "水", "lines": (0, 1, 0), "symbol": "☵"},
    "艮": {"num": 7, "wu": "土", "lines": (0, 0, 1), "symbol": "☶"},
    "坤": {"num": 8, "wu": "土", "lines": (0, 0, 0), "symbol": "☷"},
}
GUA_ORDER = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
NUM_TO_GUA = {info["num"]: name for name, info in GUA.items()}

# 六十四卦 · 上下卦组合 → 卦名（行=上卦，列=下卦，按先天八卦序；卦名与 gua64.json 一致）
GUA_TABLE = {
    "乾": {"乾": "乾卦", "兑": "履卦", "离": "同人卦", "震": "无妄卦",
           "巽": "姤卦", "坎": "讼卦", "艮": "遁卦", "坤": "否卦"},
    "兑": {"乾": "夬卦", "兑": "兑卦", "离": "革卦", "震": "随卦",
           "巽": "大过卦", "坎": "困卦", "艮": "咸卦", "坤": "萃卦"},
    "离": {"乾": "大有卦", "兑": "睽卦", "离": "离卦", "震": "噬嗑卦",
           "巽": "鼎卦", "坎": "未济卦", "艮": "旅卦", "坤": "晋卦"},
    "震": {"乾": "大壮卦", "兑": "归妹卦", "离": "丰卦", "震": "震卦",
           "巽": "恒卦", "坎": "解卦", "艮": "小过卦", "坤": "豫卦"},
    "巽": {"乾": "小畜卦", "兑": "中孚卦", "离": "家人卦", "震": "益卦",
           "巽": "巽卦", "坎": "涣卦", "艮": "渐卦", "坤": "观卦"},
    "坎": {"乾": "需卦", "兑": "节卦", "离": "既济卦", "震": "屯卦",
           "巽": "井卦", "坎": "坎卦", "艮": "蹇卦", "坤": "比卦"},
    "艮": {"乾": "大畜卦", "兑": "损卦", "离": "贲卦", "震": "颐卦",
           "巽": "蛊卦", "坎": "蒙卦", "艮": "艮卦", "坤": "剥卦"},
    "坤": {"乾": "泰卦", "兑": "临卦", "离": "明夷卦", "震": "复卦",
           "巽": "升卦", "坎": "师卦", "艮": "谦卦", "坤": "坤卦"},
}

# 五行生克环
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # 生
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}      # 克


def gua_symbol(upper: str, lower: str) -> str:
    """上卦/下卦名 → 卦名 → 卦象字符（从 gua64.json 匹配）。"""
    name = GUA_TABLE[upper][lower]
    item = _gua64().by_name.get(name)
    return item["卦象"] if item else "䷀"


class Gua64Data:
    """六十四卦数据（gua64.json），支持按卦名 / 卦象索引。"""

    def __init__(self, json_path: str = None):
        if json_path is None:
            json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gua64.json")
        with open(json_path, encoding="utf-8") as f:
            self.data = json.load(f)
        self.by_symbol = {item["卦象"]: item for item in self.data}
        self.by_name = {item["卦名"]: item for item in self.data}

    def get(self, gua_symbol: str):
        return self.by_symbol.get(gua_symbol)

    def name(self, gua_symbol: str) -> str:
        item = self.get(gua_symbol)
        return item["卦名"] if item else "?"


_GA = None


def _gua64():
    global _GA
    if _GA is None:
        _GA = Gua64Data()
    return _GA


def div8(n: int) -> int:
    """n÷8 取余，余 0 记 8。"""
    r = n % 8
    return 8 if r == 0 else r


def div6(n: int) -> int:
    """n÷6 取余，余 0 记 6。"""
    r = n % 6
    return 6 if r == 0 else r


def cast_two_numbers(a: int, b: int):
    """
    古法两数起卦。
    返回 dict：上卦、下卦、动爻(1-6,自下而上)、本卦符号。
    """
    a = abs(int(a))
    b = abs(int(b))
    upper_num = div8(a)
    lower_num = div8(b)
    dong = div6(a + b)
    upper = NUM_TO_GUA[upper_num]
    lower = NUM_TO_GUA[lower_num]
    symbol = gua_symbol(upper, lower)
    return {
        "method": "古法两数起卦",
        "detail": f"首数 {a}÷8 余 {upper_num}，得上卦「{upper}」；"
                  f"次数 {b}÷8 余 {lower_num}，得下卦「{lower}」；"
                  f"两数和 {a + b}÷6 余 {dong}，动爻为第 {dong} 爻。",
        "upper": upper,
        "lower": lower,
        "dong": dong,
        "ben_symbol": symbol,
    }


def cast_lunar(zhi_num: int, month: int, day: int, hour_zhi: int):
    """
    古法农历时间起卦（梅花易数月日时起卦）。
    上卦=(年支+月+日)÷8 取余；下卦=(年支+月+日+时)÷8 取余；动爻=(年支+月+日+时)÷6 取余。
    zhi_num: 年地支数(子1..亥12)；hour_zhi: 时辰数(子1..亥12)。
    """
    y = int(zhi_num)
    m = int(month)
    d = int(day)
    h = int(hour_zhi)
    upper_sum = y + m + d
    lower_sum = upper_sum + h
    upper_num = div8(upper_sum)
    lower_num = div8(lower_sum)
    dong = div6(lower_sum)
    upper = NUM_TO_GUA[upper_num]
    lower = NUM_TO_GUA[lower_num]
    symbol = gua_symbol(upper, lower)
    return {
        "method": "农历时间起卦",
        "detail": (f"年支 {y} + 月 {m} + 日 {d} = {upper_sum}，÷8 余 {upper_num}，得上卦「{upper}」；"
                  f"再加时 {h} 得 {lower_sum}，÷8 余 {lower_num}，得下卦「{lower}」；"
                  f"{lower_sum}÷6 余 {dong}，动爻为第 {dong} 爻。"),
        "upper": upper,
        "lower": lower,
        "dong": dong,
        "ben_symbol": symbol,
    }


def cast_random():
    """随机起卦：随机两数（1~99）。"""
    import random
    a = random.randint(1, 99)
    b = random.randint(1, 99)
    return cast_two_numbers(a, b)


def six_lines(symbol: str):
    """卦象字符 → 六爻（自下而上：初爻在前、上爻在后，1=阳 0=阴）。"""
    name = _gua64().get(symbol)["卦名"]
    # 由卦名反查上下卦；六爻自下而上 = 下卦三爻 + 上卦三爻
    for upper, row in GUA_TABLE.items():
        for lower, gname in row.items():
            if gname == name:
                return GUA[lower]["lines"] + GUA[upper]["lines"]
    return (1, 1, 1, 1, 1, 1)


def upper_lower(symbol: str):
    """卦象字符 → (上卦名, 下卦名)。"""
    name = _gua64().get(symbol)["卦名"]
    for upper, row in GUA_TABLE.items():
        for lower, gname in row.items():
            if gname == name:
                return upper, lower
    return "乾", "乾"


def compute(symbol: str, dong: int):
    """
    由本卦符号与动爻位(1-6自下而上)，计算互卦、变卦、体用。
    """
    lines = six_lines(symbol)
    upper_name, lower_name = upper_lower(symbol)

    # 互卦：下互=2,3,4爻；上互=3,4,5爻
    mut_lower = _name_from_lines(tuple(lines[1:4]))
    mut_upper = _name_from_lines(tuple(lines[2:5]))
    mut_symbol = gua_symbol(mut_upper, mut_lower)

    # 变卦：动爻翻转
    var_lines = list(lines)
    var_lines[dong - 1] = 1 - var_lines[dong - 1]
    var_upper = _name_from_lines(tuple(var_lines[3:6]))
    var_lower = _name_from_lines(tuple(var_lines[0:3]))
    var_symbol = gua_symbol(var_upper, var_lower)

    # 体用：动爻在 4-6 爻则上卦为用、下卦为体；1-3 爻则下卦为用、上卦为体
    if dong >= 4:
        ti, yong = lower_name, upper_name
    else:
        ti, yong = upper_name, lower_name

    return {
        "ben_symbol": symbol,
        "ben_upper": upper_name,
        "ben_lower": lower_name,
        "mut_symbol": mut_symbol,
        "var_symbol": var_symbol,
        "dong": dong,
        "ti": ti,
        "yong": yong,
        "lines": lines,
    }


def _name_from_lines(three):
    """三爻(自下而上) → 卦名。"""
    for name, info in GUA.items():
        if info["lines"] == tuple(three):
            return name
    return "?"


def ti_yong_relation(ti: str, yong: str) -> str:
    """体用生克断语。"""
    ti_wu = GUA[ti]["wu"]
    yong_wu = GUA[yong]["wu"]
    if ti_wu == yong_wu:
        return "体用比和，诸事顺遂，宜主动进取。"
    if SHENG[yong_wu] == ti_wu:
        return "用生体，外有助力，吉，可事半功倍。"
    if SHENG[ti_wu] == yong_wu:
        return "体生用，我泄其气，主付出耗损，宜守不宜进。"
    if KE[ti_wu] == yong_wu:
        return "体克用，我能掌控局面，虽费力但可成，吉中有劳。"
    if KE[yong_wu] == ti_wu:
        return "用克体，受制于人，凶，宜静待时机，忌冒进。"
    return "体用关系待定。"


def lines_to_display(lines, dong=None) -> str:
    """六爻(自下而上) → 爻线文本（自上而下展示），动爻处标注。"""
    parts = []
    for i in range(len(lines) - 1, -1, -1):
        v = lines[i]
        mark = "  ◆动" if dong and (i + 1) == dong else ""
        parts.append(("━━━━━" if v == 1 else "━ ━ ━") + mark)
    return "\n".join(parts)


if __name__ == "__main__":
    gua64 = Gua64Data()
    for test in [(3, 8), (1, 1), (7, 7), (5, 6), (9, 17), (23, 40)]:
        r = cast_two_numbers(*test)
        g = compute(r["ben_symbol"], r["dong"])
        print("=" * 40)
        print(r["detail"])
        print("本卦:", gua64.name(g["ben_symbol"]), g["ben_symbol"],
              " 互卦:", gua64.name(g["mut_symbol"]), g["mut_symbol"],
              " 变卦:", gua64.name(g["var_symbol"]), g["var_symbol"])
        print("动爻:", g["dong"], " 体:", g["ti"], " 用:", g["yong"],
              " →", ti_yong_relation(g["ti"], g["yong"]))
        print(lines_to_display(g["lines"], g["dong"]))
