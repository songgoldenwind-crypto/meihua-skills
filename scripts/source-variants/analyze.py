#!/usr/bin/env python3
"""Optional method overlays; never changes the canonical Meihua chart."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from functools import lru_cache
from pathlib import Path


ELEMENTS = {"乾": "金", "兑": "金", "离": "火", "震": "木", "巽": "木", "坎": "水", "艮": "土", "坤": "土"}
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
BRANCH_ELEMENTS = dict(zip("子丑寅卯辰巳午未申酉戌亥", ("水", "土", "木", "木", "土", "火", "火", "土", "金", "金", "土", "水")))
TAIJI_BRANCHES = {"乾": "戌亥", "坎": "子", "艮": "丑寅", "震": "卯", "巽": "辰巳", "离": "午", "坤": "未申", "兑": "酉"}
TOMBS = {"金": "丑", "木": "未", "火": "戌", "水": "辰", "土": "辰"}
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
HETU = {"0": "土", "1": "水", "2": "火", "3": "木", "4": "金", "5": "土", "6": "水", "7": "火", "8": "木", "9": "金"}
XIANTIAN = dict(zip("1234567890", ("乾", "兑", "离", "震", "巽", "坎", "艮", "坤", "乾", "坤")))
HOUTIAN = dict(zip("12346789", ("坎", "坤", "震", "巽", "乾", "兑", "艮", "离")))
LIANSHAN = dict(zip("1234567890", ("艮", "兑", "坎", "离", "震", "巽", "巽", "坤", "乾", "艮")))
TAIJI_SEASON_MONTHS = {"春": "寅卯", "夏": "巳午", "秋": "申酉", "冬": "亥子", "四季": "辰未戌丑"}
TAIJI_SEASON_ELEMENTS = {
    "春": {"旺": "木", "相": "火", "休": "水", "囚": "金", "死": "土"},
    "夏": {"旺": "火", "相": "土", "休": "木", "囚": "水", "死": "金"},
    "秋": {"旺": "金", "相": "水", "休": "土", "囚": "火", "死": "木"},
    "冬": {"旺": "水", "相": "木", "休": "金", "囚": "土", "死": "火"},
    "四季": {"旺": "土", "相": "金", "休": "火", "囚": "木", "死": "水"},
}
NUMBER_TRANSFORMS = (
    dict(zip("0123456789", "5678901234")),
    dict(zip("0123456789", "2679341826")),
    dict(zip("0123456789", "1926456189")),
)
PHONETIC_SOUND_TRIGRAMS = {"乾": "元", "兑": "会", "离": "运", "震": "世"}
PHONETIC_VOWEL_TRIGRAMS = {"坤": "元", "艮": "会", "坎": "运", "巽": "世"}
CEGUI_XIANTIAN_NUMBERS = dict(zip("乾兑离震巽坎艮坤", range(1, 9)))
CEGUI_HOUTIAN_NUMBERS = {"坎": 1, "坤": 2, "震": 3, "巽": 4, "乾": 6, "兑": 7, "艮": 8, "离": 9}
NUMBER_TRIADS = {"申子辰": "1380", "巳酉丑": "29", "亥卯未": "567", "寅午戌": "4"}


def relation(base: str, other: str) -> str:
    if base == other:
        return "兄弟"
    if GENERATES[base] == other:
        return "子孙"
    if GENERATES[other] == base:
        return "父母"
    if CONTROLS[base] == other:
        return "妻财"
    return "官鬼"


def void_branches(day_ganzhi: str) -> str:
    if len(day_ganzhi) != 2 or day_ganzhi[0] not in STEMS or day_ganzhi[1] not in BRANCHES:
        raise ValueError("有效日干支须为两个汉字，例如甲子")
    cycle = [(STEMS[n % 10], BRANCHES[n % 12]) for n in range(60)]
    if tuple(day_ganzhi) not in cycle:
        raise ValueError("日干支阴阳序列不合法")
    index = cycle.index(tuple(day_ganzhi))
    start = index - index % 10
    occupied = {branch for _, branch in cycle[start:start + 10]}
    return "".join(branch for branch in BRANCHES if branch not in occupied)


def load_chart(path: str) -> dict:
    chart = json.loads(Path(path).read_text(encoding="utf-8"))
    if chart.get("schema_version") != "meihua-chart/1.1":
        raise ValueError("需要 meihua-engine 输出的 meihua-chart/1.1 JSON")
    return chart


def positions(chart: dict) -> dict[str, str]:
    return {
        f"{stage}.{half}": chart[stage][half]["name"]
        for stage in ("original", "mutual", "changed")
        for half in ("upper", "lower")
    }


def taiji_seasonal_strength(month_branch: str | None) -> dict | None:
    if not isinstance(month_branch, str) or month_branch not in BRANCHES:
        return None
    season = next(name for name, branches in TAIJI_SEASON_MONTHS.items() if month_branch in branches)
    states = TAIJI_SEASON_ELEMENTS[season]
    return {
        "month_branch": month_branch,
        "month_branch_source": "chart.calendar.month_branch（排盘引擎的节令月支）",
        "season": season,
        "elements_by_state": states,
        "state_by_element": {element: state for state, element in states.items()},
    }


def flying(chart: dict) -> dict:
    base_name = chart["body_use"]["body"]["name"]
    base_element = ELEMENTS[base_name]
    calendar = chart.get("calendar", {})
    month = calendar.get("month_branch")
    day = calendar.get("day_branch")
    return {
        "method": "flying-relations",
        "mode": "flying-relations-overlay",
        "canonical_chart_unchanged": True,
        "body": {"trigram": base_name, "element": base_element},
        "flying_relatives": [
            {"position": path, "trigram": trigram, "element": ELEMENTS[trigram], "relative_to_body": relation(base_element, ELEMENTS[trigram])}
            for path, trigram in positions(chart).items()
        ],
        "month_day": {
            "month_branch": month,
            "month_element": BRANCH_ELEMENTS.get(month),
            "month_relation_to_body": relation(base_element, BRANCH_ELEMENTS[month]) if month in BRANCH_ELEMENTS else None,
            "day_branch": day,
            "day_element": BRANCH_ELEMENTS.get(day),
            "day_relation_to_body": relation(base_element, BRANCH_ELEMENTS[day]) if day in BRANCH_ELEMENTS else None,
            "day_ganzhi": calendar.get("day_ganzhi"),
            "day_boundary_policy": calendar.get("day_boundary_policy"),
        },
        "limits": "六亲仅为以体卦为中心的五行标签；日月与卦组同气须合参，不自动判旺衰、成败或应期；同一卦多法解读不是独立复验。",
    }


def taiji(chart: dict, path: str, evidence: str) -> dict:
    if path not in positions(chart):
        raise ValueError("太极点必须是 original/mutual/changed 的 upper 或 lower 路径")
    if not evidence.strip():
        raise ValueError("必须先说明为何按占问选此太极点")
    trigram = positions(chart)[path]
    element = ELEMENTS[trigram]
    calendar = chart.get("calendar", {})
    day_ganzhi = calendar.get("day_ganzhi")
    empty = void_branches(day_ganzhi) if day_ganzhi else None
    branches = TAIJI_BRANCHES[trigram]
    seasonal = taiji_seasonal_strength(calendar.get("month_branch"))
    groups = [
        {"position": pos, "trigram": name, "element": ELEMENTS[name], "relative": relation(element, ELEMENTS[name])}
        for pos, name in positions(chart).items()
    ]
    support_positions = [item["position"] for item in groups if item["relative"] in ("兄弟", "父母")]
    restraining_positions = [item["position"] for item in groups if item["relative"] in ("官鬼", "子孙", "妻财")]
    return {
        "method": "taiji-chart-groups",
        "mode": "taiji-partial-overlay",
        "canonical_chart_unchanged": True,
        "taiji": {"position": path, "evidence": evidence, "trigram": trigram, "element": element, "seasonal_state": seasonal["state_by_element"][element] if seasonal else None},
        "relative_to_taiji": [
            {**item, "seasonal_state": seasonal["state_by_element"][item["element"]] if seasonal else None}
            for item in groups
        ],
        "chart_group_counts": {
            "support_or_same_positions": support_positions,
            "restraining_or_draining_positions": restraining_positions,
            "note": "六个本互变经卦按五行列数，含太极点自身；仅供卦内强弱合参，不是旺衰评分或从格判定。",
        },
        "conditional_timing": {
            "strong_not_following": "若另经卦组与四柱合参确认为旺而不从，才取克制体卦和所测对应卦之时。",
            "weak_not_following": "若另经卦组与四柱合参确认为弱而不从，才取生助体卦和太极点之时。",
            "condition_status": "未自动判定从旺、从弱或唯一应期",
            "required_before_date": [
                "先固定所问的现实阶段：消息、面试、录用或入职不能混为一项",
                "另核卦组旺衰、从格与喜忌，不能仅由纳支或月令推出",
                "核对四柱口径及可验证的现实进程",
                "在原占时确定年、月、日、时的时间尺度",
            ],
        },
        "seasonal_strength": seasonal,
        "branch_candidates": list(branches),
        "branch_candidates_role": "卦纳地支的检索线索；单凭此项不能换算事项完成的年月日",
        "tomb_branch": TOMBS[element],
        "day_void_branches": list(empty) if empty else None,
        "day_ganzhi": day_ganzhi,
        "day_boundary_policy": calendar.get("day_boundary_policy"),
        "limits": "月令五态与卦内同气是两种证据；四柱可制约应期，不以月令一项决定卦体本身旺衰。从格和喜忌无完整自动判据，不给唯一成败或日期。",
    }


def number_profile(digits: str) -> dict:
    if not digits.isascii() or not digits.isdigit() or len(digits) not in (4, 11):
        raise ValueError("只接受四位尾号或 11 位号码的纯数字输入")
    last = digits[-4:]
    a, b, c, d = last
    candidates = [
        {"method": "夹", "age": a + d, "matter_digits": b + c},
        {"method": "靠", "age": a + b, "matter_digits": c + d},
        {"method": "翻", "age": d + c, "matter_digits": a + b},
        {"method": "翻", "age": b + a, "matter_digits": c + d},
    ]
    if b == "7":
        candidates.append({"method": "转", "age": "2" + d, "matter_digits": a + c, "basis": "7 按二七同火转成 2；仅对已核 1703 示例适用"})
    return {
        "method": "number-position-profile",
        "mode": "number-profile-candidates",
        "input_scope": "phone-11" if len(digits) == 11 else "tail-4",
        "masked_input": "*" * (len(digits) - 4) + last,
        "three_parts": {"heaven": digits[:3], "earth": digits[3:7], "human": last} if len(digits) == 11 else None,
        "four_grids": dict(zip(("元", "会", "运", "世"), (digits[3:5], digits[5:7], digits[7:9], digits[9:11]))) if len(digits) == 11 else None,
        "human_four_positions": dict(zip(("天", "地", "人一", "人二"), last)),
        "digits": [{"position": n + 1, "digit": value, "xiantian": XIANTIAN[value], "houtian": HOUTIAN.get(value), "lianshan": LIANSHAN[value], "hetu_element": HETU[value]} for n, value in enumerate(last)],
        "age_candidates": candidates,
        "printed_transform_rows": [
            {"row": index + 1, "last_four_transformed": "".join(mapping[value] for value in last)}
            for index, mapping in enumerate(NUMBER_TRANSFORMS)
        ],
        "three_harmony_timing": [
            {"branches": list(branches), "digits": list(values), "matching_tail_positions": [index + 1 for index, digit in enumerate(last) if digit in values]}
            for branches, values in NUMBER_TRIADS.items()
        ],
        "adjacent_hetu_pairs": [last[n:n + 2] for n in range(3) if frozenset(last[n:n + 2]) in (frozenset(x) for x in ("16", "27", "38", "49", "50"))],
        "limits": "四格、三合应期与三行变数表只列出候选；没有对任意号码唯一选行、选岁数或流年的通则，不自动择一。",
    }


@lru_cache(maxsize=1)
def _vendored_hexagram_table() -> dict:
    source = Path(__file__).resolve()
    candidates = (
        source.parents[1] / "meihua-engine" / "vendor" / "MeihuaYiAI" / "meihua_core.py",
        source.parents[2] / "meihua-engine" / "vendor" / "MeihuaYiAI" / "meihua_core.py",
    )
    vendor = next((path for path in candidates if path.is_file()), None)
    if vendor is None:
        raise ValueError("缺少随包固定版本的六十四卦名表")
    spec = importlib.util.spec_from_file_location("meihua_vendor_for_names", vendor)
    if spec is None or spec.loader is None:
        raise ValueError("缺少随包固定版本的六十四卦名表")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.GUA_TABLE


def _hexagram_short(upper: str, lower: str) -> str:
    return _vendored_hexagram_table()[upper][lower].removesuffix("卦")


@lru_cache(maxsize=1)
def _hanging_one() -> dict:
    path = Path(__file__).with_name("hanging-one.json")
    table = json.loads(path.read_text(encoding="utf-8"))
    if table.get("schema_version") != "hanging-one/1.0":
        raise ValueError("挂一图位表版本不符")
    rows = table["hexagrams"]
    if len(rows) != 16 or any(len(row) != 16 for row in rows):
        raise ValueError("挂一图位表须为十六乘十六")
    return table


def phonetic_composition(sound_upper: str, sound_lower: str, phonetic_upper: str, phonetic_lower: str, evidence: str) -> dict:
    trigrams = (sound_upper, sound_lower, phonetic_upper, phonetic_lower)
    if any(name not in PHONETIC_SOUND_TRIGRAMS for name in trigrams[:2]) or any(name not in PHONETIC_VOWEL_TRIGRAMS for name in trigrams[2:]):
        raise ValueError("此路声卦须由乾兑离震、音卦须由坤艮坎巽构成")
    if not evidence.strip():
        raise ValueError("须先提供古反切、声韵及声卦/音卦取定依据")
    labels = [PHONETIC_SOUND_TRIGRAMS[sound_upper], PHONETIC_SOUND_TRIGRAMS[sound_lower],
              PHONETIC_VOWEL_TRIGRAMS[phonetic_upper], PHONETIC_VOWEL_TRIGRAMS[phonetic_lower]]
    hanging = _hanging_one()
    row_label, column_label = "之".join(labels[:2]), "之".join(labels[2:])
    row = hanging["row_order"].index(row_label)
    column = hanging["column_order"].index(column_label)
    return {
        "method": "phonetic-hanging-one",
        "mode": "phonetic-recombination",
        "phonetic_evidence": evidence,
        "sound_hexagram": {"upper": sound_upper, "lower": sound_lower, "name": _hexagram_short(sound_upper, sound_lower)},
        "phonetic_hexagram": {"upper": phonetic_upper, "lower": phonetic_lower, "name": _hexagram_short(phonetic_upper, phonetic_lower)},
        "jiji_outer": {"upper": sound_upper, "lower": phonetic_upper, "name": _hexagram_short(sound_upper, phonetic_upper)},
        "jiji_inner": {"upper": sound_lower, "lower": phonetic_lower, "name": _hexagram_short(sound_lower, phonetic_lower)},
        "hanging_one": {"position": "之".join(labels), "hexagram": hanging["hexagrams"][row][column]},
        "limits": "最终挂一卦仅在声卦、音卦已据古反切和预先固定的音韵规则分别核定时可用；不能从现代汉字或普通话自动求古声韵，不同图序不可混用。",
    }


def cegui(chart: dict) -> dict:
    lines = chart["original"]["lines_bottom_up"]
    if len(lines) != 6 or any(line not in (0, 1) for line in lines):
        raise ValueError("卦画须为自下而上的六条 0/1 阴阳爻")
    yang = sum(lines)
    yin = 6 - yang
    moving = chart["moving_line"]
    if not isinstance(moving, int) or moving not in range(1, 7):
        raise ValueError("策轨计算须有一条已核的动爻")
    upper = chart["original"]["upper"]["name"]
    lower = chart["original"]["lower"]["name"]

    def calculated(body: int, numbers: dict[str, int]) -> dict:
        upper_number, lower_number = numbers[upper], numbers[lower]
        factor = moving * 10 + upper_number + 1 if moving >= 4 else lower_number * 10 + moving + 1
        added = moving + upper_number + lower_number
        return {"upper_trigram_number": upper_number, "lower_trigram_number": lower_number,
                "moving_line": moving, "moving_half": "upper" if moving >= 4 else "lower",
                "factor": factor, "added_original_and_moving": added,
                "result_number": body * factor + added}
    ce = yang * 36 + yin * 24
    gui = yang * 128 + yin * 112
    return {
        "method": "cegui-arithmetic",
        "mode": "cegui-arithmetic",
        "canonical_chart_unchanged": True,
        "line_counts": {"yang": yang, "yin": yin},
        "ce_count": {"yang_per_line": 36, "yin_per_line": 24, "body_number": ce, **calculated(ce, CEGUI_XIANTIAN_NUMBERS)},
        "gui_count": {"yang_per_line": 128, "yin_per_line": 112, "body_number": gui, **calculated(gui, CEGUI_HOUTIAN_NUMBERS)},
        "limits": "前提是已按相应先天或后天路线取得六画卦与动爻；程序只复算身数与乘加，不补造原始起卦步骤或自动解释应期。",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="梅花可选方法输出")
    sub = parser.add_subparsers(dest="command", required=True)
    x = sub.add_parser("flying", help="飞宫五行与日月标签")
    x.add_argument("--chart", required=True)
    t = sub.add_parser("taiji", help="太极点、卦组与月令五态")
    t.add_argument("--chart", required=True)
    t.add_argument("--taiji-path", required=True)
    t.add_argument("--evidence", required=True)
    n = sub.add_parser("number", help="数码结构候选")
    n.add_argument("--digits", required=True)
    y = sub.add_parser("cegui", help="策轨身数与乘加")
    y.add_argument("--chart", required=True)
    ys = sub.add_parser("phonetic", help="古音声/音横合与挂一图位")
    ys.add_argument("--sound-upper", required=True)
    ys.add_argument("--sound-lower", required=True)
    ys.add_argument("--phonetic-upper", required=True)
    ys.add_argument("--phonetic-lower", required=True)
    ys.add_argument("--evidence", required=True)
    args = parser.parse_args()
    try:
        if args.command == "flying":
            result = flying(load_chart(args.chart))
        elif args.command == "taiji":
            result = taiji(load_chart(args.chart), args.taiji_path, args.evidence)
        elif args.command == "cegui":
            result = cegui(load_chart(args.chart))
        elif args.command == "phonetic":
            result = phonetic_composition(args.sound_upper, args.sound_lower, args.phonetic_upper, args.phonetic_lower, args.evidence)
        else:
            result = number_profile(args.digits)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
