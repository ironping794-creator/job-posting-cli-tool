import unittest

from job_posting_cli.collect import get_path, parse_limit, record_fields, set_path
from job_posting_cli.url_export import clean_value, normalize_offer_row


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

    def test_offer_row_normalization(self):
        row = normalize_offer_row(
            {"recordTime": "2026-06-07 00:00:00", "company": "测试公司", "referralMethod": "a&amp;b"},
            "https://offer.gfjianli.com/",
        )
        self.assertEqual(row["发布时间"], "2026-06-07 00:00:00")
        self.assertEqual(row["公司"], "测试公司")
        self.assertEqual(row["投递方式"], "a&b")
        self.assertEqual(clean_value(None), "")


if __name__ == "__main__":
    unittest.main()
