from pathlib import Path
import datetime

import unittest
from unittest import mock

from hyde.pages import Metadata, HydePage

TEST_POST_FILE = {
    "file_path": Path("content/posts/test_title.md"),
    "content": """
author: Hyde
draft: False
date: 2021-03-01
type: posts
title: Test post
urlstub: test-post
---
# Welcome to hyde

How are you today?
""",
    "html": "<h1>Welcome to hyde</h1>\n<p>How are you today?</p>"
}


class TestHydePage(unittest.TestCase):
    def setUp(self) -> None:
        self.m_post = Metadata("test title", "posts", "test-title", False)
        self.m_index = Metadata("Posts", "posts", "index", True)

    def test_hydepage_init(self):
        p = HydePage(self.m_post, None)
        self.assertEqual(p.content, None)
        self.assertEqual(p.template_file, "posts.html.jinja2")
        self.assertEqual(p.url, "/posts/test-title.html")
        self.assertEqual(p.html_path, Path("posts/test-title.html"))

    def test_hydepage_from_dir(self):
        path = Path("content/posts")

        p = HydePage.from_dir(path)
        self.assertEqual(p.meta.title, "Posts")
        self.assertEqual(p.meta.type, "posts")
        self.assertEqual(p.meta.urlstub, "index")
        self.assertEqual(p.meta.is_index, True)
        self.assertEqual(p.content, None)
        self.assertEqual(p.template_file, "index.html.jinja2")
        self.assertEqual(p.url, "/posts/index.html")
        self.assertEqual(p.html_path, Path("posts/index.html"))

    def test_hydepage_from_file(self):
        with mock.patch('hyde.pages.open', mock.mock_open(read_data=TEST_POST_FILE["content"])) as m:
            p = HydePage.from_file(TEST_POST_FILE["file_path"])

        self.assertEqual(p.meta.title, "Test post")
        self.assertEqual(p.meta.type, "posts")
        self.assertEqual(p.meta.is_index, False)
        self.assertEqual(p.meta.date, datetime.date(year=2021, month=3, day=1))
        self.assertEqual(p.meta.author, "Hyde")
        self.assertEqual(p.meta.urlstub, "test-post")
        self.assertEqual(p.content, TEST_POST_FILE["html"])
        self.assertEqual(p.template_file, "posts.html.jinja2")
        self.assertEqual(p.url, "/posts/test-post.html")
        self.assertEqual(p.html_path, Path("posts/test-post.html"))

if __name__ == '__main__':
    unittest.main()