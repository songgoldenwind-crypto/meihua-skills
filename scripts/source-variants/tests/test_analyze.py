import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT.parent / "meihua-engine" / "paipan.py"
spec = importlib.util.spec_from_file_location("source_variants", ROOT / "analyze.py")
variants = importlib.util.module_from_spec(spec)
spec.loader.exec_module(variants)


def chart(*arguments):
    result = subprocess.run([sys.executable, str(ENGINE), *arguments], check=True, text=True, capture_output=True)
    return json.loads(result.stdout)


class SourceVariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = chart("time", "--datetime", "2026-09-15T11:00", "--timezone", "Asia/Shanghai")

    def test_calendar_gives_day_branch_without_changing_chart(self):
        self.assertEqual("壬辰", self.example["calendar"]["day_ganzhi"])
        self.assertEqual("辰", self.example["calendar"]["day_branch"])
        self.assertEqual("雷火丰", self.example["original"]["name"])
        self.assertEqual(3, self.example["moving_line"])
        late_zi = chart("time", "--datetime", "2026-09-15T23:30", "--timezone", "Asia/Shanghai")
        self.assertEqual("癸巳", late_zi["calendar"]["day_ganzhi"])
        self.assertIn("23:00", late_zi["calendar"]["day_boundary_policy"])

    def test_flying_relatives_and_month_day(self):
        result = variants.flying(self.example)
        positions = {item["position"]: item["relative_to_body"] for item in result["flying_relatives"]}
        self.assertEqual("子孙", positions["original.lower"])
        self.assertEqual("官鬼", positions["mutual.upper"])
        self.assertEqual("酉", result["month_day"]["month_branch"])
        self.assertEqual("辰", result["month_day"]["day_branch"])
        self.assertTrue(result["canonical_chart_unchanged"])

    def test_taiji_requires_frozen_point_and_lists_void_without_declaring_result(self):
        result = variants.taiji(self.example, "original.upper", "所问取震")
        self.assertEqual("卯", result["branch_candidates"][0])
        self.assertIn("不能换算", result["branch_candidates_role"])
        self.assertEqual(4, len(result["conditional_timing"]["required_before_date"]))
        self.assertEqual("未", result["tomb_branch"])
        self.assertEqual(["午", "未"], result["day_void_branches"])
        self.assertEqual("秋", result["seasonal_strength"]["season"])
        self.assertEqual("死", result["taiji"]["seasonal_state"])
        self.assertEqual(6, len(result["chart_group_counts"]["support_or_same_positions"]) + len(result["chart_group_counts"]["restraining_or_draining_positions"]))
        self.assertIn("未自动判定", result["conditional_timing"]["condition_status"])
        with self.assertRaises(ValueError):
            variants.taiji(self.example, "original.upper", " ")
        with self.assertRaises(ValueError):
            variants.taiji(self.example, "original.none", "所问取震")

    def test_taiji_five_seasonal_states(self):
        expected = {
            "寅": ("木", "火", "水", "金", "土"),
            "巳": ("火", "土", "木", "水", "金"),
            "申": ("金", "水", "土", "火", "木"),
            "亥": ("水", "木", "金", "土", "火"),
            "辰": ("土", "金", "火", "木", "水"),
        }
        for branch, elements in expected.items():
            with self.subTest(branch=branch):
                states = variants.taiji_seasonal_strength(branch)["elements_by_state"]
                self.assertEqual(elements, tuple(states.values()))
        self.assertIsNone(variants.taiji_seasonal_strength(None))

    def test_cegui_formula_reproduces_two_fixed_cases(self):
        result = variants.cegui(chart("manual", "--upper", "乾", "--lower", "坤", "--moving-line", "1"))
        self.assertEqual({"yang": 3, "yin": 3}, result["line_counts"])
        self.assertEqual(180, result["ce_count"]["body_number"])
        self.assertEqual(720, result["gui_count"]["body_number"])
        upper = variants.cegui(chart("manual", "--upper", "坎", "--lower", "离", "--moving-line", "4"))
        lower = variants.cegui(chart("manual", "--upper", "坎", "--lower", "离", "--moving-line", "2"))
        self.assertEqual(30254, upper["gui_count"]["result_number"])
        self.assertEqual(66972, lower["gui_count"]["result_number"])
        self.assertEqual("upper", upper["gui_count"]["moving_half"])
        self.assertEqual("lower", lower["gui_count"]["moving_half"])

    def test_phonetic_recombination_reproduces_two_fixed_cases(self):
        first = variants.phonetic_composition("兑", "乾", "坎", "坤", "书沼切，声卦夬，音卦比")
        self.assertEqual("夬", first["sound_hexagram"]["name"])
        self.assertEqual("比", first["phonetic_hexagram"]["name"])
        self.assertEqual("困", first["jiji_outer"]["name"])
        self.assertEqual("否", first["jiji_inner"]["name"])
        self.assertEqual({"position": "会之元之运之元", "hexagram": "大有"}, {key: first["hanging_one"][key] for key in ("position", "hexagram")})
        jiao = variants.phonetic_composition("兑", "震", "巽", "坤", "古吊切，声卦随，音卦观")
        self.assertEqual("大过", jiao["jiji_outer"]["name"])
        self.assertEqual("豫", jiao["jiji_inner"]["name"])
        self.assertEqual("既济", jiao["hanging_one"]["hexagram"])
        table = variants._hanging_one()
        names = [name for row in table["hexagrams"] for name in row]
        self.assertEqual(256, len(names))
        self.assertEqual(64, len(set(names)))
        self.assertEqual({4}, {names.count(name) for name in set(names)})
        with self.assertRaises(ValueError):
            variants.phonetic_composition("兑", "乾", "坎", "坤", " ")
        with self.assertRaises(ValueError):
            variants.phonetic_composition("坤", "乾", "坎", "坤", "书沼切")

    def test_number_example_enumerates_not_selects(self):
        result = variants.number_profile("1703")
        candidates = {(x["method"], x["age"]) for x in result["age_candidates"]}
        self.assertTrue({("夹", "13"), ("靠", "17"), ("翻", "30"), ("翻", "71"), ("转", "23")} <= candidates)
        self.assertEqual("坤", result["digits"][2]["xiantian"])
        self.assertIsNone(result["digits"][2]["houtian"])
        self.assertEqual(["6258", "6829", "9116"], [row["last_four_transformed"] for row in result["printed_transform_rows"]])
        self.assertEqual({"天": "1", "地": "7", "人一": "0", "人二": "3"}, result["human_four_positions"])
        triads = {item["branches"][0]: item for item in result["three_harmony_timing"]}
        self.assertEqual(["1", "3", "8", "0"], triads["申"]["digits"])
        self.assertEqual([1, 3, 4], triads["申"]["matching_tail_positions"])
        eleven = variants.number_profile("13313987561")
        self.assertEqual({"元": "13", "会": "98", "运": "75", "世": "61"}, eleven["four_grids"])
        with self.assertRaises(ValueError):
            variants.number_profile("170")

    def test_cli_preserves_schema_and_rejects_wrong_chart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "chart.json"
            path.write_text(json.dumps(self.example), encoding="utf-8")
            result = subprocess.run([sys.executable, str(ROOT / "analyze.py"), "flying", "--chart", str(path)], text=True, capture_output=True, check=True)
            self.assertEqual("flying-relations-overlay", json.loads(result.stdout)["mode"])
            path.write_text('{"schema_version":"wrong"}', encoding="utf-8")
            rejected = subprocess.run([sys.executable, str(ROOT / "analyze.py"), "flying", "--chart", str(path)], text=True, capture_output=True)
            self.assertNotEqual(0, rejected.returncode)


if __name__ == "__main__":
    unittest.main()
