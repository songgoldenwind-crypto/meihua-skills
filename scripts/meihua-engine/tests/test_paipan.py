import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor" / "MeihuaYiAI"))
sys.path.insert(0, str(ROOT / "vendor" / "lunar-python"))

import meihua_core as upstream_meihua
from lunar_python import Solar


def cli(*args: str) -> dict:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "paipan.py"), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(completed.stdout)


class PaipanTests(unittest.TestCase):
    def test_2026_time_golden_case(self):
        result = cli(
            "time",
            "--datetime",
            "2026-09-15T11:00",
            "--timezone",
            "Asia/Shanghai",
        )
        self.assertEqual("二〇二六年八月初五", result["calendar"]["lunar_date"])
        self.assertEqual("雷火丰", result["original"]["name"])
        self.assertEqual("泽风大过", result["mutual"]["name"])
        self.assertEqual("震为雷", result["changed"]["name"])
        self.assertEqual(3, result["moving_line"])
        self.assertEqual("震", result["body_use"]["body"]["name"])
        self.assertEqual("离", result["body_use"]["use"]["name"])
        self.assertEqual("upper", result["body_use"]["body_position"])
        self.assertEqual("兑", result["body_use"]["body_mutual"]["name"])
        self.assertEqual("巽", result["body_use"]["use_mutual"]["name"])
        self.assertEqual("体生用", result["body_use"]["relation"])
        self.assertEqual("meihua-chart/1.1", result["schema_version"])
        self.assertEqual("酉", result["seasonal_qi"]["month_branch"])
        self.assertEqual("旺", result["seasonal_qi"]["trigram_status"]["乾"])
        self.assertEqual("衰", result["seasonal_qi"]["trigram_status"]["震"])

    def test_classic_guanmei_case(self):
        result = cli(
            "lunar-time",
            "--year-branch",
            "辰",
            "--month",
            "12",
            "--day",
            "17",
            "--hour-branch",
            "申",
        )
        self.assertEqual("泽火革", result["original"]["name"])
        self.assertEqual("天风姤", result["mutual"]["name"])
        self.assertEqual("泽山咸", result["changed"]["name"])
        self.assertEqual(1, result["moving_line"])

    def test_manual_regression_for_rejected_engine_bug(self):
        result = cli(
            "manual",
            "--upper",
            "震",
            "--lower",
            "离",
            "--moving-line",
            "3",
        )
        self.assertEqual("雷火丰", result["original"]["name"])
        self.assertEqual("泽风大过", result["mutual"]["name"])
        self.assertEqual("震为雷", result["changed"]["name"])

    def test_all_384_chart_states_close(self):
        names = set()
        for upper_number in range(1, 9):
            for lower_number in range(1, 9):
                base = upstream_meihua.cast_two_numbers(upper_number, lower_number)
                names.add(upstream_meihua.Gua64Data().name(base["ben_symbol"]))
                for line in range(1, 7):
                    chart = upstream_meihua.compute(base["ben_symbol"], line)
                    original = list(chart["lines"])
                    changed = list(upstream_meihua.six_lines(chart["var_symbol"]))
                    differences = [i for i, pair in enumerate(zip(original, changed)) if pair[0] != pair[1]]
                    self.assertEqual([line - 1], differences)
                    self.assertNotEqual("?", upstream_meihua.Gua64Data().name(chart["mut_symbol"]))
                    self.assertNotEqual("?", upstream_meihua.Gua64Data().name(chart["var_symbol"]))
                    if line <= 3:
                        self.assertEqual(chart["ben_upper"], chart["ti"])
                        self.assertEqual(chart["ben_lower"], chart["yong"])
                    else:
                        self.assertEqual(chart["ben_lower"], chart["ti"])
                        self.assertEqual(chart["ben_upper"], chart["yong"])
        self.assertEqual(64, len(names))

    def test_calendar_regressions(self):
        leap = Solar.fromYmd(1933, 7, 22).getLunar()
        self.assertEqual(-5, leap.getMonth())
        self.assertEqual(30, leap.getDay())
        new_year = Solar.fromYmd(2026, 2, 17).getLunar()
        self.assertEqual((2026, 1, 1), (new_year.getYear(), new_year.getMonth(), new_year.getDay()))

    def test_three_numbers_use_explicit_moving_number(self):
        result = cli(
            "numbers",
            "--upper-number",
            "23",
            "--lower-number",
            "41",
            "--moving-number",
            "17",
        )
        self.assertEqual(5, result["moving_line"])
        self.assertEqual(17, result["inputs"]["moving_number"])
        self.assertIn("显式动数 17", result["source_trace"])
        self.assertNotIn("两数和", result["source_trace"])

    def test_numeric_context_adds_qi_without_changing_the_cast(self):
        plain = cli(
            "strokes",
            "--upper-number",
            "4",
            "--lower-number",
            "4",
            "--moving-number",
            "8",
        )
        contextual = cli(
            "strokes",
            "--upper-number",
            "4",
            "--lower-number",
            "4",
            "--moving-number",
            "8",
            "--context-datetime",
            "2026-09-19T20:37:33",
            "--timezone",
            "Asia/Shanghai",
        )
        self.assertEqual(plain["original"], contextual["original"])
        self.assertEqual(plain["moving_line"], contextual["moving_line"])
        self.assertNotIn("seasonal_qi", plain)
        self.assertEqual("酉", contextual["seasonal_qi"]["month_branch"])

    def test_external_omen_requires_frozen_model_mappings(self):
        result = cli(
            "external-omen",
            "--object-trigram",
            "震",
            "--object-evidence",
            "车辆突然启动，以动态取震",
            "--direction-trigram",
            "离",
            "--direction-evidence",
            "车辆从正南方来",
            "--hour-branch",
            "申",
        )
        self.assertEqual("external-omen", result["method"])
        self.assertEqual("雷火丰", result["original"]["name"])
        self.assertEqual(4, result["moving_line"])
        self.assertEqual(16, result["inputs"]["moving_number"])
        self.assertEqual("车辆突然启动，以动态取震", result["inputs"]["object_evidence"])
        self.assertEqual("车辆从正南方来", result["inputs"]["direction_evidence"])
        self.assertIn("上游 div6", result["source_trace"])

    def test_external_omen_context_must_match_hour_branch(self):
        matching = cli(
            "external-omen",
            "--object-trigram",
            "震",
            "--object-evidence",
            "车辆突然启动，以动态取震",
            "--direction-trigram",
            "离",
            "--direction-evidence",
            "车辆从正南方来",
            "--hour-branch",
            "申",
            "--context-datetime",
            "2026-09-15T15:00",
            "--timezone",
            "Asia/Shanghai",
        )
        self.assertEqual("申", matching["calendar"]["hour_branch"])
        self.assertIn("seasonal_qi", matching)

        rejected = subprocess.run(
            [
                sys.executable,
                str(ROOT / "paipan.py"),
                "external-omen",
                "--object-trigram",
                "震",
                "--object-evidence",
                "车辆突然启动",
                "--direction-trigram",
                "离",
                "--direction-evidence",
                "车辆从正南方来",
                "--hour-branch",
                "午",
                "--context-datetime",
                "2026-09-15T15:00",
                "--timezone",
                "Asia/Shanghai",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(2, rejected.returncode)
        self.assertIn("对应时支 申 不一致", rejected.stderr)


if __name__ == "__main__":
    unittest.main()
