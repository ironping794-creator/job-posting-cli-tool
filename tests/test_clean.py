from pathlib import Path
import tempfile
import unittest

import openpyxl

from job_posting_cli.clean import clean_rows, filter_rows, parse_salary, write_csv
from job_posting_cli.xlsx import write_xlsx


class CleanTests(unittest.TestCase):
    def test_parse_salary_handles_common_units(self):
        self.assertEqual(parse_salary("8-12k")[0:2], (8000.0, 12000.0))
        self.assertEqual(parse_salary("1.5-2万")[0:2], (15000.0, 20000.0))
        self.assertEqual(parse_salary("面议"), (None, None, "unknown"))

    def test_clean_filter_rows_with_chinese_aliases(self):
        rows = [
            {
                "职位名称": "AI 数据分析实习生",
                "公司名称": "Example AI",
                "工作地点": "上海",
                "薪资待遇": "10-15k",
                "详情链接": "https://example.com/jobs/1",
            },
            {
                "职位名称": "AI 数据分析实习生",
                "公司名称": "Example AI",
                "工作地点": "上海",
                "薪资待遇": "10-15k",
                "详情链接": "https://example.com/jobs/1",
            },
        ]

        cleaned, duplicates = clean_rows(rows)
        filtered = filter_rows(cleaned, ["上海"], ["AI"], 8000)

        self.assertEqual(duplicates, 1)
        self.assertEqual(len(cleaned), 1)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["matched_keywords"], "AI")

    def test_writers_create_csv_and_clickable_xlsx(self):
        rows = [
            {
                "title": "AI Analyst",
                "company": "Example AI",
                "city": "Shanghai",
                "salary": "10-15k",
                "detail_url": "https://example.com/jobs/1",
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            csv_path = tmp_path / "jobs.csv"
            write_csv(csv_path, rows)
            self.assertTrue(csv_path.read_text(encoding="utf-8-sig").startswith("title,company,city"))

            xlsx_path = tmp_path / "jobs.xlsx"
            write_xlsx(xlsx_path, rows, ["title", "detail_url"], "Jobs")
            wb = openpyxl.load_workbook(xlsx_path)
            self.assertEqual(wb.active["B2"].hyperlink.target, "https://example.com/jobs/1")


if __name__ == "__main__":
    unittest.main()
