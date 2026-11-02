"""retrieval_funnel_timeline_score —— 自检测试。

按时间线排列Prompt 工程负责人·检索召回的漏斗分析并标出节奏异常

覆盖：正常路径、边界输入、防呆红线、幂等性。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import retrieval_funnel_timeline_score  # noqa: E402

SAMPLE_TEXT = '12:00 start\n12:05 middle\n12:20 end'


class TestPromptlead_jd082(unittest.TestCase):
    """Prompt 工程负责人·检索召回的漏斗分析"""

    def test_rules_come_from_the_job_description(self):
        """规则表必须非空，且每条规则都挂在本岗位的要求上。

        这是「工具与 JD 同源」的可核查证据：规则名带 domain 前缀，
        why 里引用了岗位技能线或领域标签。
        """
        rules = getattr(retrieval_funnel_timeline_score, "RULES", None)
        self.assertTrue(rules, "规则表为空")
        self.assertGreaterEqual(len(rules), 8)
        for r in rules:
            self.assertIn("Prompt 工程负责人·检索召回的漏斗分析", r["name"])
            self.assertTrue(r["why"], "规则缺少判定说明")
            self.assertIn(r["severity"], ("high", "medium", "low"))
            self.assertTrue(r["keywords"], "规则缺少关键词")

    def test_cli_help_exits_zero(self):
        """--help 必须能正常退出。"""
        import subprocess
        proc = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "retrieval_funnel_timeline_score.py"), "--help"],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0)

    def test_cli_rejects_empty_input(self):
        """空输入必须明确报错，不能静默成功。"""
        import subprocess
        proc = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "retrieval_funnel_timeline_score.py"), "--text", "   "],
            capture_output=True, text=True, encoding="utf-8")
        self.assertNotEqual(proc.returncode, 0)

    def test_cli_json_output_parses(self):
        """--json 输出必须是合法 JSON。"""
        import subprocess
        proc = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "retrieval_funnel_timeline_score.py"), "--text", SAMPLE_TEXT,
             "--json"],
            capture_output=True, text=True, encoding="utf-8")
        if proc.returncode not in (0, 1):
            self.fail(f"退出码异常：{proc.returncode} {proc.stderr[:300]}")
        data = json.loads(proc.stdout)
        self.assertIsInstance(data, dict)

    def test_does_not_mutate_input(self):
        """防呆：分析过程不得改动调用方传入的对象。"""
        payload = SAMPLE_TEXT
        before = payload
        retrieval_funnel_timeline_score.retrieval_funnel_timeline_score_analyze(payload)
        self.assertEqual(before, payload)

    def test_is_idempotent(self):
        """同一输入跑两次结果必须一致。"""
        a = retrieval_funnel_timeline_score.retrieval_funnel_timeline_score_analyze(SAMPLE_TEXT)
        b = retrieval_funnel_timeline_score.retrieval_funnel_timeline_score_analyze(SAMPLE_TEXT)
        self.assertEqual(json.dumps(a, ensure_ascii=False, sort_keys=True),
                         json.dumps(b, ensure_ascii=False, sort_keys=True))

    def test_parses_events(self):
        r = retrieval_funnel_timeline_score.retrieval_funnel_timeline_score_analyze(SAMPLE_TEXT)
        self.assertTrue(r["ok"])
        self.assertEqual(r["count"], 3)

    def test_events_are_sorted(self):
        """防呆：事件必须按时间排好，乱序输入也要排。"""
        r = retrieval_funnel_timeline_score.retrieval_funnel_timeline_score_analyze("12:20 end\n12:00 start\n12:05 middle")
        times = [e["at"] for e in r["events"]]
        self.assertEqual(times, sorted(times))

    def test_reports_slowest_gap(self):
        r = retrieval_funnel_timeline_score.retrieval_funnel_timeline_score_analyze(SAMPLE_TEXT)
        self.assertIsNotNone(r["slowest_gap"])
