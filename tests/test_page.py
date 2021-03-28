from pathlib import Path
import datetime

import unittest

from hyde.pages import Metadata, Page
from .utils import page_from_file_str, TEST_PAGE_FILES


class TestPage(unittest.TestCase):
    def setUp(self) -> None:
        self.m_post = Metadata("test title", "posts", "test-title-stub")

    def test_Page_init(self):
        p = Page(self.m_post, None)
        self.assertEqual(p.content, None)
        self.assertEqual(p.template_file, "posts.html.jinja2")
        self.assertEqual(p.url, "test-title-stub.html")

    def test_Page_from_file(self):
        test_file = TEST_PAGE_FILES[0]
        p = page_from_file_str(test_file)

        self.assertEqual(p.meta.title, "Test post")
        self.assertEqual(p.meta.type, "posts")
        self.assertEqual(p.meta.date, datetime.date(year=2021, month=3, day=1))
        self.assertEqual(p.meta.author, "Hyde")
        self.assertEqual(p.meta.urlstub, "test-title-stub")
        self.assertEqual(p.content, test_file["html"])
        self.assertEqual(p.template_file, "posts.html.jinja2")
        self.assertEqual(p.url, "test-title-stub.html")

if __name__ == '__main__':
    unittest.main()