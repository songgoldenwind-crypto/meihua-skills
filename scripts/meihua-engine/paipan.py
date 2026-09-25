#!/usr/bin/env python3
"""CLI adapter around pinned, vendored open-source Meihua engines.

All hexagram, mutual/changed hexagram, moving-line, body/use, and calendar
calculations are delegated to the upstream code under ``vendor/``.  This file
only validates CLI input and normalizes the upstream result as JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


ROOT = Path(__file__).resolve().parent
MEIHUA_VENDOR = ROOT / "vendor" / "MeihuaYiAI"
LUNAR_VENDOR = ROOT / "vendor" / "lunar-python"
sys.path.insert(0, str(MEIHUA_VENDOR))
sys.path.insert(0, str(LUNAR_VENDOR))

import meihua_core as upstream_meihua  # noqa: E402
from lunar_python import Solar  # noqa: E402


ENGINE = {
    "id": "bundled-meihua-core",
    "license": "MIT",
}
CALENDAR = {
    "id": "bundled-lunisolar-calendar",
    "version": "v1.4.8",
    "license": "MIT",
}

BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
LUNAR_MONTH_BRANCHES = ("寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑")
TRIGRAM_ELEMENTS = {
    "乾": "金",
    "兑": "金",
    "离": "火",
    "震": "木",
    "巽": "木",
    "坎": "水",
    "艮": "土",
    "坤": "土",
}
MONTH_QI = {
    "寅": ("木", "土"),
    "卯": ("木", "土"),
    "巳": ("火", "金"),
    "午": ("火", "金"),
    "申": ("金", "木"),
    "酉": ("金", "木"),
    "亥": ("水", "火"),
    "子": ("水", "火"),
    "辰": ("土", "水"),
    "戌": ("土", "水"),
    "丑": ("土", "水"),
    "未": ("土", "水"),
}
TRIGRAM_NATURE = {
    "乾": "天",
    "兑": "泽",
    "离": "火",
    "震": "雷",
    "巽": "风",
    "坎": "水",
    "艮": "山",
    "坤": "地",
}
PURE_NAMES = {
    "乾": "乾为天",
    "兑": "兑为泽",
    "离": "离为火",
    "震": "震为雷",
    "巽": "巽为风",
    "坎": "坎为水",
    "艮": "艮为山",
    "坤": "坤为地",
}


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("必须是正整数")
    return parsed


def moving_line(value: str) -> int:
    parsed = int(value)
    if not 1 <= parsed <= 6:
        raise argparse.ArgumentTypeError("动爻必须在 1 到 6 之间")
    return parsed


def non_empty_text(value: str) -> str:
    parsed = value.strip()
    if not parsed:
        raise argparse.ArgumentTypeError("取象依据不能为空")
    return parsed


def lunar_month(value: str) -> int:
    parsed = int(value)
    if not 1 <= parsed <= 12:
        raise argparse.ArgumentTypeError("农历月必须在 1 到 12 之间")
    return parsed


def lunar_day(value: str) -> int:
    parsed = int(value)
    if not 1 <= parsed <= 30:
        raise argparse.ArgumentTypeError("农历日必须在 1 到 30 之间")
    return parsed


def parse_branch(value: str) -> tuple[int, str]:
    raw = value.strip()
    if raw in BRANCHES:
        return BRANCHES.index(raw) + 1, raw
    try:
        number = int(raw)
    except ValueError as exc:
        raise ValueError("地支须写子至亥，或写 1 至 12") from exc
    if not 1 <= number <= 12:
        raise ValueError("地支序数必须在 1 到 12 之间")
    return number, BRANCHES[number - 1]


def parse_local_datetime(value: str, timezone: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("时间须为 ISO 格式，例如 2026-09-15T11:00") from exc
    try:
        zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"未知时区：{timezone}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=zone)
    return parsed.astimezone(zone)


def trigram_payload(name: str) -> dict[str, Any]:
    info = upstream_meihua.GUA[name]
    return {
        "name": name,
        "number": info["num"],
        "element": info["wu"],
        "symbol": info["symbol"],
        "lines_bottom_up": list(info["lines"]),
    }


def full_hexagram_name(symbol: str) -> str:
    upper, lower = upstream_meihua.upper_lower(symbol)
    short = upstream_meihua.GUA_TABLE[upper][lower].removesuffix("卦")
    if upper == lower:
        return PURE_NAMES[upper]
    return f"{TRIGRAM_NATURE[upper]}{TRIGRAM_NATURE[lower]}{short}"


def hexagram_payload(symbol: str) -> dict[str, Any]:
    upper, lower = upstream_meihua.upper_lower(symbol)
    return {
        "name": full_hexagram_name(symbol),
        "short_name": upstream_meihua.GUA_TABLE[upper][lower],
        "symbol": symbol,
        "upper": trigram_payload(upper),
        "lower": trigram_payload(lower),
        "lines_bottom_up": list(upstream_meihua.six_lines(symbol)),
    }


def seasonal_qi_payload(month_branch: str | None) -> dict[str, Any] | None:
    if month_branch not in MONTH_QI:
        return None
    thriving, declining = MONTH_QI[month_branch]
    statuses = {
        trigram: (
            "旺" if element == thriving else "衰" if element == declining else "平"
        )
        for trigram, element in TRIGRAM_ELEMENTS.items()
    }
    return {
        "basis": "梅花卦气旺衰，以月支归季；旺衰只调整体用强度，不单独定吉凶",
        "month_branch": month_branch,
        "thriving_element": thriving,
        "declining_element": declining,
        "trigram_status": statuses,
    }


def calendar_payload(local: datetime, timezone: str) -> dict[str, Any]:
    lunar = Solar.fromYmdHms(
        local.year, local.month, local.day, local.hour, local.minute, local.second
    ).getLunar()
    lunar_month_number = abs(lunar.getMonth())
    year_number, year_name = parse_branch(lunar.getYearZhi())
    hour_number, hour_name = parse_branch(lunar.getTimeZhi())
    return {
        "calendar": "solar-to-lunar",
        "civil_time": local.isoformat(),
        "timezone": timezone,
        "lunar_date": lunar.toString(),
        "lunar_year": lunar.getYear(),
        "year_ganzhi": lunar.getYearInGanZhi(),
        "year_branch": year_name,
        "year_branch_number": year_number,
        "month": lunar_month_number,
        "month_ganzhi": lunar.getMonthInGanZhiExact(),
        "month_branch": lunar.getMonthZhiExact(),
        "day_ganzhi": lunar.getDayInGanZhiExact(),
        "day_branch": lunar.getDayZhiExact(),
        "day_boundary_policy": "23:00 晚子换次日干支；农历日数仍按民用日期",
        "day": lunar.getDay(),
        "hour_branch": hour_name,
        "hour_branch_number": hour_number,
        "leap_month": lunar.getMonth() < 0,
        "leap_month_policy": "闰月沿用同名月份数",
    }


def context_calendar(args: argparse.Namespace) -> dict[str, Any] | None:
    value = getattr(args, "context_datetime", None)
    if not value:
        return None
    timezone = getattr(args, "timezone", "Asia/Shanghai")
    return calendar_payload(parse_local_datetime(value, timezone), timezone)


def normalize_chart(
    casting: dict[str, Any],
    *,
    method: str,
    inputs: dict[str, Any],
    calendar: dict[str, Any] | None = None,
) -> dict[str, Any]:
    chart = upstream_meihua.compute(casting["ben_symbol"], casting["dong"])
    relation_text = upstream_meihua.ti_yong_relation(chart["ti"], chart["yong"])
    relation = relation_text.split("，", 1)[0]
    body_position = "upper" if chart["dong"] <= 3 else "lower"
    use_position = "lower" if body_position == "upper" else "upper"
    mutual = hexagram_payload(chart["mut_symbol"])
    result = {
        "schema_version": "meihua-chart/1.1",
        "engine": ENGINE,
        "calendar_engine": CALENDAR if calendar else None,
        "method": method,
        "inputs": inputs,
        "source_trace": casting["detail"],
        "moving_line": chart["dong"],
        "original": hexagram_payload(chart["ben_symbol"]),
        "mutual": mutual,
        "changed": hexagram_payload(chart["var_symbol"]),
        "body_use": {
            "body": trigram_payload(chart["ti"]),
            "use": trigram_payload(chart["yong"]),
            "body_position": body_position,
            "use_position": use_position,
            "body_mutual": mutual[body_position],
            "use_mutual": mutual[use_position],
            "relation": relation,
            "source_text": relation_text,
        },
    }
    if calendar:
        result["calendar"] = calendar
        seasonal_qi = seasonal_qi_payload(calendar.get("month_branch"))
        if seasonal_qi:
            result["seasonal_qi"] = seasonal_qi
    return result


def cast_manual(args: argparse.Namespace) -> dict[str, Any]:
    symbol = upstream_meihua.gua_symbol(args.upper, args.lower)
    casting = {
        "ben_symbol": symbol,
        "dong": args.moving_line,
        "detail": "上游 gua_symbol 与 compute 接口按指定上下卦及动爻排盘。",
    }
    calendar = context_calendar(args)
    inputs = {
        "upper": args.upper,
        "lower": args.lower,
        "moving_line": args.moving_line,
    }
    if calendar:
        inputs["context_datetime"] = args.context_datetime
        inputs["timezone"] = args.timezone
    return normalize_chart(
        casting,
        method="manual",
        inputs=inputs,
        calendar=calendar,
    )


def cast_numbers(args: argparse.Namespace, method: str = "numbers") -> dict[str, Any]:
    casting = upstream_meihua.cast_two_numbers(args.upper_number, args.lower_number)
    inputs: dict[str, Any] = {
        "upper_number": args.upper_number,
        "lower_number": args.lower_number,
    }
    if args.moving_number is not None:
        casting["dong"] = upstream_meihua.div6(args.moving_number)
        casting["detail"] = (
            f"首数 {args.upper_number}÷8 余 {upstream_meihua.div8(args.upper_number)}，"
            f"得上卦「{casting['upper']}」；次数 {args.lower_number}÷8 余 "
            f"{upstream_meihua.div8(args.lower_number)}，得下卦「{casting['lower']}」；"
            f"显式动数 {args.moving_number} 交由上游 div6 取第 {casting['dong']} 爻。"
        )
        inputs["moving_number"] = args.moving_number
    calendar = context_calendar(args)
    if calendar:
        inputs["context_datetime"] = args.context_datetime
        inputs["timezone"] = args.timezone
    return normalize_chart(casting, method=method, inputs=inputs, calendar=calendar)


def cast_lunar_time(args: argparse.Namespace) -> dict[str, Any]:
    year_number, year_name = parse_branch(args.year_branch)
    hour_number, hour_name = parse_branch(args.hour_branch)
    casting = upstream_meihua.cast_lunar(
        year_number, args.month, args.day, hour_number
    )
    calendar = {
        "calendar": "lunar",
        "year_branch": year_name,
        "year_branch_number": year_number,
        "month": args.month,
        "month_branch": LUNAR_MONTH_BRANCHES[args.month - 1],
        "day": args.day,
        "hour_branch": hour_name,
        "hour_branch_number": hour_number,
        "leap_month": args.leap_month,
        "leap_month_policy": "闰月沿用同名月份数",
    }
    return normalize_chart(
        casting,
        method="lunar-time",
        inputs=calendar,
        calendar=calendar,
    )


def cast_time(args: argparse.Namespace) -> dict[str, Any]:
    local = parse_local_datetime(args.datetime, args.timezone)
    calendar = calendar_payload(local, args.timezone)
    lunar = Solar.fromYmdHms(
        local.year, local.month, local.day, local.hour, local.minute, local.second
    ).getLunar()
    lunar_month_number = abs(lunar.getMonth())
    year_number, year_name = parse_branch(lunar.getYearZhi())
    hour_number, hour_name = parse_branch(lunar.getTimeZhi())
    casting = upstream_meihua.cast_lunar(
        year_number, lunar_month_number, lunar.getDay(), hour_number
    )
    return normalize_chart(
        casting,
        method="time",
        inputs={"datetime": args.datetime, "timezone": args.timezone},
        calendar=calendar,
    )


def cast_sound(args: argparse.Namespace) -> dict[str, Any]:
    hour_number, hour_name = parse_branch(args.hour_branch)
    # Upstream cast_lunar implements the same “first total / first total plus
    # hour” route. Zero month/day keep every divination calculation upstream.
    casting = upstream_meihua.cast_lunar(args.count, 0, 0, hour_number)
    casting["detail"] = "闻声起卦复用上游 cast_lunar 数值路径：" + casting["detail"]
    calendar = context_calendar(args)
    if calendar and calendar["hour_branch"] != hour_name:
        raise ValueError(
            f"--hour-branch {hour_name} 与 --context-datetime 对应时支"
            f" {calendar['hour_branch']} 不一致"
        )
    inputs = {
        "sound_count": args.count,
        "hour_branch": hour_name,
        "hour_branch_number": hour_number,
    }
    if calendar:
        inputs["context_datetime"] = args.context_datetime
        inputs["timezone"] = args.timezone
    return normalize_chart(
        casting,
        method="sound",
        inputs=inputs,
        calendar=calendar,
    )


def cast_external_omen(args: argparse.Namespace) -> dict[str, Any]:
    """Cast after the model has frozen the object and direction mappings."""
    object_number = upstream_meihua.GUA[args.object_trigram]["num"]
    direction_number = upstream_meihua.GUA[args.direction_trigram]["num"]
    hour_number, hour_name = parse_branch(args.hour_branch)
    moving_number = object_number + direction_number + hour_number

    casting = upstream_meihua.cast_two_numbers(object_number, direction_number)
    casting["dong"] = upstream_meihua.div6(moving_number)
    casting["detail"] = (
        "后天外应法：模型先固定物象卦与方位卦；"
        f"上游 cast_two_numbers 以物象卦数 {object_number} 取上卦、"
        f"方位卦数 {direction_number} 取下卦；"
        f"物象卦数、方位卦数与时支数之和 {moving_number} "
        f"交由上游 div6，得第 {casting['dong']} 爻动。"
    )
    calendar = context_calendar(args)
    if calendar and calendar["hour_branch"] != hour_name:
        raise ValueError(
            f"--hour-branch {hour_name} 与 --context-datetime 对应时支"
            f" {calendar['hour_branch']} 不一致"
        )
    inputs = {
        "object_evidence": args.object_evidence,
        "object_trigram": args.object_trigram,
        "object_trigram_number": object_number,
        "direction_evidence": args.direction_evidence,
        "direction_trigram": args.direction_trigram,
        "direction_trigram_number": direction_number,
        "hour_branch": hour_name,
        "hour_branch_number": hour_number,
        "moving_number": moving_number,
    }
    if calendar:
        inputs["context_datetime"] = args.context_datetime
        inputs["timezone"] = args.timezone
    return normalize_chart(
        casting,
        method="external-omen",
        inputs=inputs,
        calendar=calendar,
    )


def add_context_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument(
        "--context-datetime",
        help="占问发生的当地民用时间；只补历法与卦气，不参与该命令的起卦公式",
    )
    command.add_argument("--timezone", default="Asia/Shanghai")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="开源梅花易数排盘适配器")
    sub = parser.add_subparsers(dest="command", required=True)

    manual = sub.add_parser("manual", help="指定上下卦与动爻")
    manual.add_argument("--upper", choices=list(upstream_meihua.GUA), required=True)
    manual.add_argument("--lower", choices=list(upstream_meihua.GUA), required=True)
    manual.add_argument("--moving-line", type=moving_line, required=True)
    add_context_arguments(manual)
    manual.set_defaults(handler=cast_manual)

    numbers = sub.add_parser("numbers", help="两数或三数起卦")
    numbers.add_argument("--upper-number", type=positive_int, required=True)
    numbers.add_argument("--lower-number", type=positive_int, required=True)
    numbers.add_argument("--moving-number", type=positive_int)
    add_context_arguments(numbers)
    numbers.set_defaults(handler=cast_numbers)

    strokes = sub.add_parser("strokes", help="上下字组笔画数起卦")
    strokes.add_argument("--upper-number", type=positive_int, required=True)
    strokes.add_argument("--lower-number", type=positive_int, required=True)
    strokes.add_argument("--moving-number", type=positive_int)
    add_context_arguments(strokes)
    strokes.set_defaults(handler=lambda args: cast_numbers(args, "strokes"))

    lunar_time = sub.add_parser("lunar-time", help="确认后的农历数值起卦")
    lunar_time.add_argument("--year-branch", required=True)
    lunar_time.add_argument("--month", type=lunar_month, required=True)
    lunar_time.add_argument("--day", type=lunar_day, required=True)
    lunar_time.add_argument("--hour-branch", required=True)
    lunar_time.add_argument("--leap-month", action="store_true")
    lunar_time.set_defaults(handler=cast_lunar_time)

    time = sub.add_parser("time", help="公历民用时间转农历后起卦")
    time.add_argument("--datetime", required=True)
    time.add_argument("--timezone", default="Asia/Shanghai")
    time.set_defaults(handler=cast_time)

    sound = sub.add_parser("sound", help="声音次数加时支起卦")
    sound.add_argument("--count", type=positive_int, required=True)
    sound.add_argument("--hour-branch", required=True)
    add_context_arguments(sound)
    sound.set_defaults(handler=cast_sound)

    external_omen = sub.add_parser(
        "external-omen",
        help="模型固定物象、方位与依据后，按后天外应法起卦",
    )
    external_omen.add_argument(
        "--object-trigram", choices=list(upstream_meihua.GUA), required=True
    )
    external_omen.add_argument("--object-evidence", type=non_empty_text, required=True)
    external_omen.add_argument(
        "--direction-trigram", choices=list(upstream_meihua.GUA), required=True
    )
    external_omen.add_argument(
        "--direction-evidence", type=non_empty_text, required=True
    )
    external_omen.add_argument("--hour-branch", required=True)
    add_context_arguments(external_omen)
    external_omen.set_defaults(handler=cast_external_omen)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = args.handler(args)
    except (KeyError, TypeError, ValueError) as exc:
        parser.error(str(exc))
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
