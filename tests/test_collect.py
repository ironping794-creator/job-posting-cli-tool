import unittest

from job_posting_cli.collect import get_path, parse_limit, record_fields, set_path
from datetime import datetime, timedelta

from job_posting_cli.url_export import clean_value, filter_export_rows, normalize_site_row, parse_datetime, unsupported_url_message


class CollectTests(unittest.TestCase):
    def test_json_path_helpers(self):
        data = {"data": {"records": [{"title": "A"}]}}
        self.assertEqual(get_path(data, "data.records.0.title"), "A")
        set_path(data, "query.page", 3)
        self.assertEqual(data["query"]["page"], 3)

    def test_limit_and_field_helpers(self):
        self.assertEqual(parse_limit("all", 10), 10)
        self.assertEqual(parse_limit("half", 9), 5)
        self.assertEqual(parse_limit("3", 10), 3)
        self.assertEqual(record_fields([{"a": 1, "b": 2}, {"b": 3, "c": 4}]), ["a", "b", "c"])

    def test_site_row_normalization(self):
        row = normalize_site_row(
            {"recordTime": "2026-06-07 00:00:00", "company": "测试公司", "referralMethod": "a&amp;b"},
            "https://example.com/jobs",
        )
        self.assertEqual(row["发布时间"], "2026-06-07 00:00:00")
        self.assertEqual(row["公司"], "测试公司")
        self.assertEqual(row["投递方式"], "a&b")
        self.assertEqual(clean_value(None), "")

    def test_url_export_filters_city_and_keywords(self):
        rows = [
            {"工作地点": "上海", "公司": "甲公司", "标题": "算法工程师", "行业": "人工智能", "岗位": "研发", "备注": ""},
            {"工作地点": "北京", "公司": "乙公司", "标题": "市场运营", "行业": "消费", "岗位": "运营", "备注": ""},
            {"工作地点": "深圳", "公司": "丙公司", "标题": "数据分析", "行业": "互联网", "岗位": "分析师", "备注": ""},
        ]

        filtered = filter_export_rows(rows, cities="上海,深圳", keywords="算法,数据")

        self.assertEqual(len(filtered), 2)
        self.assertEqual([row["公司"] for row in filtered], ["甲公司", "丙公司"])

    def test_url_export_filters_publication_date(self):
        recent = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d 00:00:00")
        old = (datetime.now() - timedelta(days=80)).strftime("%Y-%m-%d 00:00:00")
        rows = [
            {"发布时间": recent, "工作地点": "上海", "公司": "甲公司", "标题": "算法工程师", "行业": "", "岗位": "", "备注": ""},
            {"发布时间": old, "工作地点": "上海", "公司": "乙公司", "标题": "算法工程师", "行业": "", "岗位": "", "备注": ""},
            {"发布时间": "", "工作地点": "上海", "公司": "丙公司", "标题": "算法工程师", "行业": "", "岗位": "", "备注": ""},
        ]

        filtered = filter_export_rows(rows, published_within_days=30)

        self.assertEqual([row["公司"] for row in filtered], ["甲公司"])
        self.assertIsNotNone(parse_datetime("2026-06-07 00:00:00"))

    def test_unsupported_dynamic_site_message(self):
        message = unsupported_url_message("www.zhipin.com")

        self.assertIn("浏览器登录态", message)
        self.assertIn("清洗 CSV", message)


if __name__ == "__main__":
    unittest.main()
